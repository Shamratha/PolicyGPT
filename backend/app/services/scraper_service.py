import json
import logging
import uuid
import httpx
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.repositories.scheme_repo import scheme_repository
from app.models.scheme import Scheme, EligibilityRule
from app.services.ai_service import ai_service
from openai import OpenAI

logger = logging.getLogger(__name__)

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore_tags = {"script", "style", "head", "meta", "link", "noscript", "header", "footer", "nav"}
        self.void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
        self.current_tag_stack = []

    def handle_starttag(self, tag, attrs):
        if tag in self.void_tags:
            return
        self.current_tag_stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.void_tags:
            return
        if tag in self.current_tag_stack:
            while self.current_tag_stack:
                popped = self.current_tag_stack.pop()
                if popped == tag:
                    break

    def handle_data(self, data):
        # Ignore text content inside scripts, styles, headers, footers, etc.
        if any(ignored in self.current_tag_stack for ignored in self.ignore_tags):
            return
        
        text = data.strip()
        if text:
            self.text_parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self.text_parts)

def extract_text_from_html(html_content: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html_content)
    return parser.get_text()

class ScraperService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def scrape_and_index_scheme(self, url: str, db: Session) -> Scheme:
        """
        Scrapes a government website URL, uses GPT-4o to parse it into a structured schema
        with logical eligibility rules, registers it in SQL, and indexes it in ChromaDB.
        """
        logger.info(f"Initiating scraping pipeline for URL: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            # Step 1: Fetch raw webpage HTML
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                html_content = response.text
        except Exception as e:
            logger.error(f"Failed to fetch content from URL {url}: {e}")
            raise ValueError(f"Failed to fetch website content: {str(e)}")

        # Step 2: Extract clean plain text
        try:
            cleaned_text = extract_text_from_html(html_content)
            # Limit page content length to avoid massive prompt token costs
            cleaned_text = cleaned_text[:12000]
            if not cleaned_text.strip():
                raise ValueError("No text content could be extracted from page HTML.")
        except Exception as e:
            logger.error(f"HTML parsing failure: {e}")
            raise ValueError(f"Failed to parse page HTML: {str(e)}")

        # Step 3: Call GPT-4o to extract structured scheme details and eligibility rules
        system_prompt = (
            "You are an AI data ingestion agent. Your task is to analyze scraped web page text from a government "
            "policy or scheme portal and extract the scheme information in structured JSON format.\n\n"
            "INSTRUCTIONS:\n"
            "1. Output a JSON object with exactly these keys:\n"
            "   - 'name': unique lowercase string slug with underscores (e.g. 'pm_awas_yojana').\n"
            "   - 'title': full official scheme title.\n"
            "   - 'description': detailed overview of what the scheme is and who it benefits.\n"
            "   - 'benefits': description of monetary subsidies, allowances, or technical support.\n"
            "   - 'eligibility_criteria': summary of eligibility criteria.\n"
            "   - 'required_documents': list of documents in plain string or comma-separated format.\n"
            "   - 'application_steps': step-by-step applying instructions.\n"
            "   - 'state': name of the state (e.g. 'Karnataka', 'Maharashtra') or 'Central'.\n"
            "   - 'category': name of category (e.g. 'Business', 'Education', 'Agriculture', 'Healthcare').\n"
            "   - 'ministry': government ministry or department in charge.\n"
            "   - 'is_for_women': boolean (true if women-only or specific benefits targeting women).\n"
            "   - 'is_for_students': boolean (true if technical students, scholar, etc.).\n"
            "   - 'is_for_startups': boolean (true if for business founders, MSMEs, etc.).\n"
            "   - 'is_for_farmers': boolean (true if for agricultural workers/landowners).\n"
            "   - 'rules': an array of rules where each rule has:\n"
            "       * 'field_name': must be one of: 'age', 'gender', 'income', 'state', 'student_status', 'startup_status', 'occupation'\n"
            "       * 'operator': must be one of: '>=', '<=', '==', 'in'\n"
            "       * 'expected_value': value constraint (e.g., '18', '35', 'female', 'karnataka', 'true', 'farmer')\n"
            "2. Make sure you respond ONLY with the JSON object, no introduction or markdown formatting wrapper."
        )

        user_content = f"Webpage Scraped Text:\n{cleaned_text}"

        result_json: Dict[str, Any] = {}
        try:
            # Development fallback check
            if settings.OPENAI_API_KEY.startswith("sk-mock"):
                # Return standard mocked result for testing/offline mode
                result_json = {
                    "name": "scraped_rajiv_gandhi",
                    "title": "Rajiv Gandhi Entrepreneurship Program",
                    "description": "Program to assist young tech entrepreneurs in Karnataka.",
                    "benefits": "Rs. 25,000 monthly stipend for 12 months.",
                    "eligibility_criteria": "Karnataka resident, age 18-35, startup status true.",
                    "required_documents": "Aadhaar, Domicile, Project Proposal",
                    "application_steps": "1. Apply on website. 2. Pitch to committee.",
                    "state": "Karnataka",
                    "category": "Business",
                    "ministry": "K-Tech, Govt of Karnataka",
                    "is_for_women": False,
                    "is_for_students": False,
                    "is_for_startups": True,
                    "is_for_farmers": False,
                    "rules": [
                        {"field_name": "state", "operator": "==", "expected_value": "karnataka"},
                        {"field_name": "age", "operator": ">=", "expected_value": "18"},
                        {"field_name": "age", "operator": "<=", "expected_value": "35"},
                        {"field_name": "startup_status", "operator": "==", "expected_value": "true"}
                    ]
                }
            else:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("OpenAI returned empty JSON parsing response.")
                result_json = json.loads(content.strip())
        except Exception as e:
            logger.error(f"Failed to parse webpage with AI: {e}")
            raise ValueError(f"AI extraction failure: {str(e)}")

        # Step 4: Register in local Database
        try:
            name = result_json.get("name", "scraped_scheme_" + str(uuid.uuid4())[:8]).lower().strip()
            
            # Check if exists and remove to overwrite cleanly
            existing = scheme_repository.get_by_name(db, name)
            if existing:
                db.delete(existing)
                db.commit()

            scheme = Scheme(
                name=name,
                title=result_json.get("title", "Scraped Scheme"),
                description=result_json.get("description", ""),
                benefits=result_json.get("benefits"),
                eligibility_criteria=result_json.get("eligibility_criteria"),
                required_documents=result_json.get("required_documents"),
                application_steps=result_json.get("application_steps"),
                state=result_json.get("state", "Central"),
                category=result_json.get("category", "General"),
                ministry=result_json.get("ministry"),
                is_for_women=bool(result_json.get("is_for_women", False)),
                is_for_students=bool(result_json.get("is_for_students", False)),
                is_for_startups=bool(result_json.get("is_for_startups", False)),
                is_for_farmers=bool(result_json.get("is_for_farmers", False))
            )
            db.add(scheme)
            db.flush()

            # Insert eligibility rules
            rules_data = result_json.get("rules", [])
            for r_data in rules_data:
                rule = EligibilityRule(
                    scheme_id=str(scheme.id),
                    field_name=r_data.get("field_name"),
                    operator=r_data.get("operator"),
                    expected_value=r_data.get("expected_value")
                )
                db.add(rule)

            db.commit()
            db.refresh(scheme)
        except Exception as e:
            logger.error(f"Failed to save scraped scheme to database: {e}")
            db.rollback()
            raise ValueError(f"Database save error: {str(e)}")

        # Step 5: Index raw text + details in ChromaDB for AI Policy Assistant
        try:
            full_indexing_text = (
                f"Scheme Name: {scheme.name}\n"
                f"Title: {scheme.title}\n"
                f"Description: {scheme.description}\n"
                f"Benefits: {scheme.benefits}\n"
                f"Eligibility Criteria: {scheme.eligibility_criteria}\n"
                f"Ministry: {scheme.ministry}\n"
                f"Source: Scraped from official URL {url}\n"
            )
            ai_service.index_scheme_text(str(scheme.id), str(scheme.name), full_indexing_text)
            logger.info(f"Scraped, registered, and indexed scheme: {scheme.title}")
        except Exception as e:
            # We don't crash the whole flow if vector indexing fails, but log it
            logger.error(f"Failed to vector index scraped scheme {scheme.title} in ChromaDB: {e}")

        return scheme

scraper_service = ScraperService()
