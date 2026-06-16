import os
import logging
import json
import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI
from typing import List, Dict, Any, Tuple, Optional, cast
from app.config import settings
from app.schemas.chat import CitationInfo
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Ensure persistent directory exists
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        
        # Initialize ChromaDB persistent client
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="policy_schemes"
        )

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI text-embedding-3-small."""
        if settings.OPENAI_API_KEY.startswith("sk-mock"):
            # Return mock embedding of length 1536
            return [0.0] * 1536
            
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * 1536

    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch."""
        if not texts:
            return []
        if settings.OPENAI_API_KEY.startswith("sk-mock"):
            return [[0.0] * 1536 for _ in texts]
            
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [d.embedding for d in response.data]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [[0.0] * 1536 for _ in texts]

    def index_scheme_text(self, scheme_id: str, scheme_name: str, content: str):
        """Chunk and index scheme guidelines."""
        # Clean text and split into ~1000 character chunks with 200 character overlap
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        i = 0
        while i < len(content):
            chunks.append(content[i : i + chunk_size])
            i += chunk_size - overlap

        if not chunks:
            return

        # Prepare metadata and IDs
        ids = [f"{scheme_id}_chunk_{idx}" for idx in range(len(chunks))]
        metadatas = [
            {"scheme_id": scheme_id, "scheme_name": scheme_name, "chunk_index": idx}
            for idx in range(len(chunks))
        ]
        
        # Generate embeddings
        embeddings = self._get_embeddings_batch(chunks)
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=cast(Any, embeddings),
            metadatas=cast(Any, metadatas),
            documents=chunks
        )
        logger.info(f"Indexed {len(chunks)} chunks for scheme: {scheme_name}")

    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract plain text from uploaded PDF file."""
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text

    def expand_query(self, query: str) -> List[str]:
        """Expand search query into 3 variations for better vector retrieval."""
        if settings.OPENAI_API_KEY.startswith("sk-mock"):
            return [query]
            
        prompt = (
            "You are an expert search assistant. Generate exactly 3 synonyms, variations, or "
            "semantic expansions of the following user query to retrieve relevant public policies. "
            "Separate the variations with a newline. Output only the variations, no numbers or introduction.\n\n"
            f"Query: {query}"
        )
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            content = response.choices[0].message.content
            if not content:
                return [query]
            variations = [line.strip() for line in content.split("\n") if line.strip()]
            # Keep original query in list too
            return list(set([query] + variations))[:4]
        except Exception as e:
            logger.error(f"Failed to expand query: {e}")
            return [query]

    def vector_search(self, queries: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Query ChromaDB with expanded queries and aggregate unique chunks."""
        results = []
        seen_ids = set()

        for q in queries:
            q_emb = self._get_embedding(q)
            res = self.collection.query(
                query_embeddings=[q_emb],
                n_results=limit
            )
            
            # Chroma returns lists of results
            if res and res.get('ids') and res.get('metadatas') and res.get('documents'):
                ids = res['ids']
                metadatas = res['metadatas']
                documents = res['documents']
                distances = res.get('distances')
                if ids and metadatas and documents:
                    for idx, doc_id in enumerate(ids[0]):
                        if doc_id not in seen_ids:
                            seen_ids.add(doc_id)
                            results.append({
                                "id": doc_id,
                                "metadata": metadatas[0][idx],
                                "document": documents[0][idx],
                                "distance": distances[0][idx] if distances else 0.0
                            })
                        
        # Sort by distance (smaller means closer/more relevant)
        results.sort(key=lambda x: x["distance"])
        return results[:limit]

    def synthesize_response(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]], 
        schemes_db: List[Any], 
        profile_dict: Optional[Dict[str, Any]] = None,
        history: Optional[List[Any]] = None
    ) -> Tuple[str, List[CitationInfo], int]:
        """Synthesize answer with citations using LLM and ground it using references."""
        if not search_results:
            return (
                "I couldn't find any government schemes in our knowledge base matching your request. "
                "Please search the Scheme Explorer or provide details about your demographics.",
                [],
                0
            )

        if settings.OPENAI_API_KEY.startswith("sk-mock"):
            # Mock return for testing
            mock_citations = []
            if schemes_db:
                mock_citations = [
                    CitationInfo(
                        scheme_id=schemes_db[0].id,
                        scheme_name=schemes_db[0].name,
                        scheme_title=schemes_db[0].title,
                        state=schemes_db[0].state,
                        category=schemes_db[0].category or "General"
                    )
                ]
            return (
                "This is a simulated response grounded in mock policies. Based on your profile, you may be eligible.",
                mock_citations,
                85
            )

        # Build map of scheme_id -> Scheme DB info for fast access/metadata extraction
        schemes_map = {s.id: s for s in schemes_db}

        # Format context text with citations
        context_lines = []
        citation_mapping = {} # maps scheme_id to index number
        citation_counter = 1

        for idx, item in enumerate(search_results):
            s_id = item["metadata"]["scheme_id"]
            if s_id in schemes_map:
                s_info = schemes_map[s_id]
                if s_id not in citation_mapping:
                    citation_mapping[s_id] = {
                        "index": citation_counter,
                        "title": s_info.title,
                        "name": s_info.name,
                        "state": s_info.state,
                        "category": s_info.category or "General"
                    }
                    citation_counter += 1
                
                c_num = citation_mapping[s_id]["index"]
                context_lines.append(
                    f"[{c_num}] Scheme: {s_info.title}\n"
                    f"State: {s_info.state} | Ministry: {s_info.ministry}\n"
                    f"Details: {item['document']}\n"
                    f"Benefits: {s_info.benefits}\n"
                    f"Eligibility: {s_info.eligibility_criteria}\n"
                )

        context_str = "\n---\n".join(context_lines)

        # Build messages including user profile and history
        system_prompt = (
            "You are PolicyGPT, an AI-powered public policy expert assistant helping citizens understand government schemes, scholarship opportunities, and grants.\n\n"
            "INSTRUCTIONS:\n"
            "1. Answer the user's questions utilizing ONLY the policy documents provided in the context.\n"
            "2. Cite your sources using bracketed numbers corresponding to the context documents (e.g. [1], [2]). Every factual claim or benefit eligibility statement must carry an inline citation.\n"
            "3. If a user's question cannot be answered from the provided documents, state clearly: 'I could not find information on this in the indexed database.' DO NOT hallucinate rules or URLs.\n"
            "4. Provide answers in a structured format: explain benefits, summarize eligibility criteria, checklist of required documents, and concrete application steps.\n"
            "5. If you lack demographic information (e.g. income, state, education) required to determine eligibility, advise the user which fields they should update in their profile dashboard.\n"
            "6. Output your response in structured JSON format with three root keys:\n"
            "   - 'answer': your formatted response text (using markdown, bullet points, headers)\n"
            "   - 'confidence_score': integer from 0 to 100 based on the relevance and matching completeness of the documents.\n"
            "   - 'cited_ids': array of scheme IDs cited in your response. These must correspond exactly to the database IDs of the cited schemes.\n"
        )

        user_context = f"Context:\n{context_str}\n\n"
        if profile_dict:
            user_context += (
                f"User Profile details for eligibility mapping:\n"
                f"- Name: {profile_dict.get('name')}\n"
                f"- Age: {profile_dict.get('age')}\n"
                f"- Gender: {profile_dict.get('gender')}\n"
                f"- State: {profile_dict.get('state')}\n"
                f"- Education: {profile_dict.get('education')}\n"
                f"- Occupation: {profile_dict.get('occupation')}\n"
                f"- Income: {profile_dict.get('income')}\n"
                f"- Startup Status: {profile_dict.get('startup_status')}\n"
                f"- Student Status: {profile_dict.get('student_status')}\n\n"
            )

        messages: List[Any] = [{"role": "system", "content": system_prompt}]
        
        # Add history
        if history:
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": f"{user_context}User Query: {query}"})

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response content from OpenAI.")
            result_json = json.loads(content.strip())
            answer_text = result_json.get("answer", "")
            confidence = result_json.get("confidence_score", 50)
            cited_ids = result_json.get("cited_ids", [])
            
            # Map cited IDs (or indexes) back to CitationInfo
            citations = []
            # Check if cited_ids contains the index number as string or database scheme_id
            for s_id, info in citation_mapping.items():
                # If they returned database IDs or the corresponding index
                if s_id in cited_ids or str(info["index"]) in cited_ids or any(s_id[:10] in str(x) for x in cited_ids):
                    citations.append(
                        CitationInfo(
                            scheme_id=s_id,
                            scheme_name=info["name"],
                            scheme_title=info["title"],
                            state=info["state"],
                            category=info["category"]
                        )
                    )
            
            # If citations array is empty but we found indices inline in the response, auto-populate
            if not citations:
                for s_id, info in citation_mapping.items():
                    if f"[{info['index']}]" in answer_text:
                        citations.append(
                            CitationInfo(
                                scheme_id=s_id,
                                scheme_name=info["name"],
                                scheme_title=info["title"],
                                state=info["state"],
                                category=info["category"]
                            )
                        )

            return answer_text, citations, confidence
        except Exception as e:
            logger.error(f"Failed to synthesize response: {e}")
            return (
                "An error occurred while compiling your policy matches. Please try again or query a specific scheme name.",
                [],
                0
            )

ai_service = AIService()
