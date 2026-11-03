import os
import logging
import json
from openai import OpenAI
from typing import List, Dict, Any, Tuple, Optional, cast
from app.config import settings
from app.schemas.chat import CitationInfo
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY or "sk-mock")
        self._collection = None  # ChromaDB is opened lazily (only needed with a real OpenAI key)

    @property
    def collection(self):
        """Open the ChromaDB collection on first use. Offline mode never needs it, which keeps
        start-up fast and memory low on small hosting plans."""
        if self._collection is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = client.get_or_create_collection(name="policy_schemes")
        return self._collection

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI text-embedding-3-small."""
        if settings.ai_offline:
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
        if settings.ai_offline:
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
        if settings.ai_offline:
            return  # offline mode answers from the SQL database; no vector index needed
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
        self.collection.upsert(
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
        if settings.ai_offline:
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
        if settings.ai_offline or self.collection.count() == 0:
            # Offline mode uses mock (all-zero) embeddings, so similarity scores carry no
            # signal; keyword retrieval in synthesize_response is used instead.
            return results

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
        if settings.ai_offline:
            return offline_answer(query, schemes_db, profile_dict)

        if not search_results:
            return (
                "I couldn't find any government schemes in our knowledge base matching your request. "
                "Please search the Scheme Explorer or provide details about your demographics.",
                [],
                0
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
            "3b. If the question is not about government schemes, welfare, scholarships, subsidies or eligibility (for example fashion, sports, recipes, entertainment), politely say PolicyGPT only helps with Indian government schemes, set confidence_score to 0 and cited_ids to [].\n"
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


# ---------------------------------------------------------------------------
# Offline (no OpenAI key) answer engine: keyword retrieval over the scheme
# database + a structured, cited template answer that uses the user's profile.
# ---------------------------------------------------------------------------
import re as _re

_STOPWORDS = {
    "a", "an", "and", "are", "am", "any", "as", "at", "be", "by", "can", "do", "does", "for", "from",
    "get", "give", "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or", "please", "scheme",
    "schemes", "tell", "the", "there", "to", "what", "which", "who", "with", "you", "about", "eligible",
    "eligibility", "apply", "government", "yojana", "want", "need", "some", "show", "list", "find",
    "free", "get", "help", "any", "best", "good", "new", "available", "india", "indian",
    "pm", "pradhan", "mantri", "small", "support",
}
_SYNONYMS = {
    "business": ["startup", "enterprise", "entrepreneur", "msme", "loan", "self-employment"],
    "startup": ["business", "entrepreneur", "enterprise", "innovation"],
    "loan": ["credit", "finance", "subsidy", "business"],
    "student": ["scholarship", "education", "college", "study"],
    "scholarship": ["student", "education", "fee"],
    "farmer": ["agriculture", "farming", "kisan", "crop"],
    "farming": ["farmer", "agriculture", "kisan"],
    "women": ["woman", "female", "mahila", "girl"],
    "woman": ["women", "female", "mahila"],
    "health": ["insurance", "hospital", "medical", "treatment"],
    "house": ["housing", "home", "awas"],
    "job": ["employment", "skill", "training"],
    "daughter": ["girl", "child"],
    "girl": ["daughter", "child"],
    "savings": ["saving", "deposit"],
    "artisan": ["artisans", "craftspeople", "vishwakarma"],
    "tailor": ["artisan", "craftspeople", "tailors"],
    "carpenter": ["artisan", "craftspeople", "carpenters"],
    "unemployment": ["unemployed", "allowance"],
    "pension": ["pension", "old", "age"],
    "lpg": ["ujjwala", "gas", "cooking"],
    "gas": ["lpg", "ujjwala", "cooking"],
    "skill": ["kaushal", "training", "employment"],
    "training": ["kaushal", "skill"],
    "course": ["training", "kaushal"],
    "farmer": ["kisan", "agriculture", "farming", "crop"],
    "kisan": ["farmer", "agriculture"],
    "crop": ["fasal", "farmer", "agriculture"],
    "insurance": ["bima", "health"],
    "health": ["ayushman", "arogya", "hospital", "insurance"],
    "hospital": ["ayushman", "health"],
    "housing": ["awas", "house"],
    "house": ["awas", "housing"],
    "seed": ["startup", "funding"],
}


def _tokens(text: str) -> List[str]:
    return [t for t in _re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in _STOPWORDS and len(t) > 1]


def _split_items(text: Optional[str]) -> List[str]:
    if not text:
        return []
    parts = _re.split(r"(?:\s*\d+\.\s+)|[;,\n]", text)
    return [p.strip(" .") for p in parts if p and p.strip(" .")]


def _scheme_score(scheme: Any, q_terms: List[str], profile: Optional[Dict[str, Any]]) -> float:
    weighted_fields = [
        (str(scheme.title or ""), 3.0), (str(scheme.name or "").replace("_", " "), 3.0),
        (str(scheme.category or ""), 2.5), (str(scheme.description or ""), 1.0),
        (str(scheme.benefits or ""), 1.0), (str(scheme.eligibility_criteria or ""), 1.0),
        (str(scheme.state or ""), 1.5),
    ]
    score = 0.0
    strong = False  # did any term hit the title, id, category or a target-group flag?
    for text, weight in weighted_fields:
        field_tokens = set(_tokens(text))
        for t in q_terms:
            if t in field_tokens:
                score += weight
                if weight >= 2.5:
                    strong = True
            elif len(t) > 3 and any(ft.startswith(t) or t.startswith(ft) for ft in field_tokens if len(ft) > 3):
                score += weight * 0.5
    flags = {
        "student": bool(scheme.is_for_students), "scholarship": bool(scheme.is_for_students),
        "startup": bool(scheme.is_for_startups), "business": bool(scheme.is_for_startups),
        "farmer": bool(scheme.is_for_farmers), "women": bool(scheme.is_for_women),
        "woman": bool(scheme.is_for_women),
    }
    for t in q_terms:
        if flags.get(t):
            score += 2.0
            strong = True
    if not strong:
        score *= 0.5  # only incidental words in the description/benefits matched
    if score > 0 and profile:
        state = (profile.get("state") or "").lower()
        scheme_state = str(scheme.state or "").lower()
        if state and scheme_state not in ("central", state):
            score *= 0.4  # state scheme for a different state
        if profile.get("student_status") and scheme.is_for_students:
            score += 1.0
        if profile.get("startup_status") and scheme.is_for_startups:
            score += 1.0
        if (profile.get("gender") or "").lower() == "male" and scheme.is_for_women:
            score *= 0.3
    women_terms = {"women", "woman", "female", "mahila", "girl", "lady", "ladies", "widow"}
    if score > 0 and scheme.is_for_women and not women_terms & set(q_terms):
        if not profile or (profile.get("gender") or "").lower() != "female":
            score *= 0.5  # women-only scheme, but the question is not about women
    return score


# Common Hindi / Kannada words -> English search terms, so offline mode can match
# questions asked in those languages (answers are shown in English without an OpenAI key).
_INDIC_TERMS = {
    # Hindi
    "छात्रवृत्ति": "scholarship student", "स्कॉलरशिप": "scholarship", "छात्र": "student", "विद्यार्थी": "student",
    "पढ़ाई": "education", "शिक्षा": "education", "कॉलेज": "college", "किसान": "farmer", "खेती": "farming agriculture",
    "कृषि": "agriculture farmer", "फसल": "crop farmer", "बीमा": "insurance", "महिला": "women", "औरत": "women",
    "लड़की": "girl", "बेटी": "girl", "ऋण": "loan", "कर्ज": "loan", "लोन": "loan", "व्यवसाय": "business",
    "व्यापार": "business", "बिज़नेस": "business", "कारोबार": "business", "स्टार्टअप": "startup", "उद्यमी": "entrepreneur",
    "आवास": "housing", "मकान": "housing house", "घर": "house housing", "स्वास्थ्य": "health", "इलाज": "treatment health",
    "अस्पताल": "hospital", "पेंशन": "pension", "नौकरी": "job employment", "रोजगार": "employment", "बेरोजगार": "unemployed",
    "कौशल": "skill", "प्रशिक्षण": "training skill", "कारीगर": "artisan", "गैस": "lpg", "कर्नाटक": "karnataka",
    # Kannada
    "ವಿದ್ಯಾರ್ಥಿವೇತನ": "scholarship student", "ವಿದ್ಯಾರ್ಥಿ": "student", "ಶಿಕ್ಷಣ": "education", "ಕಾಲೇಜು": "college",
    "ರೈತ": "farmer", "ಕೃಷಿ": "agriculture farmer", "ಬೆಳೆ": "crop farmer", "ವಿಮೆ": "insurance", "ಮಹಿಳೆ": "women",
    "ಹೆಣ್ಣು": "girl women", "ಸಾಲ": "loan", "ವ್ಯಾಪಾರ": "business", "ಉದ್ಯಮಿ": "entrepreneur", "ಉದ್ಯಮ": "business",
    "ವಸತಿ": "housing", "ಮನೆ": "house housing", "ಆರೋಗ್ಯ": "health", "ಆಸ್ಪತ್ರೆ": "hospital", "ಪಿಂಚಣಿ": "pension",
    "ನಿರುದ್ಯೋಗ": "unemployed", "ಉದ್ಯೋಗ": "employment job", "ಕೌಶಲ್ಯ": "skill training", "ಕರ್ನಾಟಕ": "karnataka",
}
_INDIC_GREETINGS = ("नमस्ते", "नमस्कार", "ನಮಸ್ಕಾರ", "ನಮಸ್ತೆ")
_INDIC_SCRIPT = _re.compile(r"[\u0900-\u097F\u0C80-\u0CFF]")


def _indic_terms(query: str) -> List[str]:
    found: List[str] = []
    for word, english in _INDIC_TERMS.items():
        if word in (query or ""):
            found.extend(english.split())
    return found


_GREETINGS = {"hi", "hello", "hey", "namaste", "namaskara", "hii", "hola", "thanks", "thank"}

# Words that show the question is about government support, even if no scheme in the
# database covers it yet (used to give an honest "not covered yet" answer).
_GOV_HINTS = {
    "scheme", "schemes", "yojana", "subsidy", "subsidies", "grant", "grants", "loan", "loans", "scholarship",
    "scholarships", "pension", "insurance", "housing", "ration", "welfare", "benefit", "benefits", "stipend",
    "allowance", "government", "govt", "sarkari", "ministry", "certificate", "aadhaar", "farmer", "farmers",
    "kisan", "msme", "startup", "entrepreneur", "women", "widow", "disability", "disabled", "senior",
    "lpg", "gas", "training", "course", "fisheries", "vehicle", "transport", "solar", "electricity",
    "health", "hospital", "education", "skill", "employment", "job", "jobs", "apply", "eligible", "eligibility",
}

COVERED_TOPICS = "scholarships and student support, farmer support, women entrepreneurs, and startup / small-business loans"


def offline_answer(query: str, schemes_db: List[Any], profile: Optional[Dict[str, Any]]) -> Tuple[str, List[CitationInfo], int]:
    raw_words = set(_re.findall(r"[a-z]+", (query or "").lower()))
    is_indic = bool(_INDIC_SCRIPT.search(query or ""))
    indic_terms = _indic_terms(query) if is_indic else []
    base_terms = _tokens(query) + indic_terms
    base_terms += [t[:-1] for t in base_terms if len(t) > 4 and t.endswith("s") and not t.endswith("ss")]
    q_terms = list(base_terms)
    for t in base_terms:
        q_terms.extend(_SYNONYMS.get(t, []))

    ranked = sorted(
        ((s, _scheme_score(s, q_terms, profile)) for s in schemes_db),
        key=lambda x: x[1], reverse=True,
    )
    best_score = ranked[0][1] if ranked else 0.0
    # keep strong matches only: absolute floor + within 45% of the best match
    top = [(s, sc) for s, sc in ranked if sc >= 2.0 and sc >= best_score * 0.45][:3]

    if not top:
        is_greeting = (raw_words and raw_words <= _GREETINGS | {"there", "policygpt", "you", "very", "much"}) or (
            is_indic and not indic_terms and any(g in query for g in _INDIC_GREETINGS))
        if is_greeting:
            return (
                "Hello! I'm PolicyGPT. I help you find government schemes and check whether you qualify.\n\n"
                f"Right now I can help with {COVERED_TOPICS}. Try asking, for example:\n"
                "- *Scholarships for engineering students in Karnataka*\n"
                "- *Loans for a woman starting a small business*\n"
                "- *Support for small farmers*",
                [],
                0,
            )
        if raw_words & _GOV_HINTS or indic_terms:
            return (
                "I couldn't find a scheme for that in the PolicyGPT database yet.\n\n"
                f"The database currently covers {COVERED_TOPICS}. For other schemes, check the official "
                "portal **myscheme.gov.in** or your state government's website, or ask an administrator to "
                "add the scheme through the Insights page.",
                [],
                0,
            )
        return (
            "That question is outside what I can help with. PolicyGPT only answers questions about "
            "**Indian government schemes** - for example scholarships, farmer support, business loans and "
            "subsidies, and whether you are eligible for them.\n\n"
            "Try asking something like *Which schemes can a student in Karnataka apply for?*",
            [],
            0,
        )

    lines = ["Here are the government schemes from the PolicyGPT database that best match your question:", ""]
    citations: List[CitationInfo] = []
    for idx, (s, _) in enumerate(top, start=1):
        lines.append(f"### [{idx}] {s.title}")
        lines.append(f"*{s.state or 'Central'} - {s.category or 'General'}*")
        if s.description:
            lines.append(str(s.description).strip())
        if s.benefits:
            lines.append(f"- **Benefits:** {str(s.benefits).strip()} [{idx}]")
        if s.eligibility_criteria:
            lines.append(f"- **Who can apply:** {str(s.eligibility_criteria).strip()} [{idx}]")
        docs = _split_items(s.required_documents)
        if docs:
            lines.append(f"- **Documents:** {', '.join(docs)}")
        steps = _split_items(s.application_steps)
        if steps:
            lines.append("- **How to apply:** " + " -> ".join(steps))
        lines.append("")
        citations.append(CitationInfo(
            scheme_id=str(s.id), scheme_name=str(s.name), scheme_title=str(s.title),
            state=str(s.state or "Central"), category=str(s.category or "General"),
        ))

    missing = [label for key, label in (("age", "age"), ("state", "state"), ("income", "annual family income"))
               if not profile or profile.get(key) in (None, "")]
    if missing:
        lines.append(f"> Tip: add your {', '.join(missing)} on the **Profile** page to get a personalised eligibility check.")
    else:
        lines.append("> Use **Check Eligibility** in the Scheme Explorer for a rule-by-rule check against your profile.")
    lines.append("")
    if is_indic:
        lines.append("_Your question was understood from its Hindi / Kannada keywords. Answers are shown in English until an OpenAI API key is added._")
    lines.append("_Answer grounded in the PolicyGPT scheme database (offline mode - add an OpenAI API key for conversational answers)._")

    # Confidence reflects how strongly the best scheme matched (keyword hits), capped below 100.
    confidence = int(max(35, min(90, 30 + best_score * 4)))
    return "\n".join(lines), citations, confidence


ai_service = AIService()
