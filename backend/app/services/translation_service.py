import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        # Gracefully handle mock keys during testing
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key or "sk-mock")

    def translate_to_english(self, text: str, source_lang: str) -> str:
        if not text or source_lang.lower() == "en":
            return text

        lang_map = {"hi": "Hindi", "kn": "Kannada"}
        source_lang_name = lang_map.get(source_lang.lower(), source_lang)

        prompt = (
            f"You are a translation bot. Translate the following text from {source_lang_name} to English. "
            "Respond ONLY with the translated text. Maintain terms related to government schemes literally if they are proper names.\n\n"
            f"Text: {text}"
        )

        try:
            # Check if key is mock
            if settings.ai_offline:
                return text # fallback to original text for mock/tests
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            content = response.choices[0].message.content
            return content.strip() if content else text
        except Exception as e:
            logger.error(f"Failed to translate to English: {e}")
            return text

    def translate_from_english(self, text: str, target_lang: str) -> str:
        if not text or target_lang.lower() == "en":
            return text

        lang_map = {"hi": "Hindi", "kn": "Kannada"}
        target_lang_name = lang_map.get(target_lang.lower(), target_lang)

        prompt = (
            f"You are an expert public policy translator. Translate the following text from English to {target_lang_name}. "
            "CRITICAL: Keep citation tags like [1], [2], or [Scheme Name] intact and unmodified. "
            "Do not translate names of government schemes if they are proper nouns (e.g. keep 'Pradhan Mantri Udyogini Scheme' or 'PM-KISAN' recognizable). "
            "Only return the translation, with no conversational prefix or suffix.\n\n"
            f"Text:\n{text}"
        )

        try:
            if settings.ai_offline:
                return text # fallback for mock/tests
                
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            content = response.choices[0].message.content
            return content.strip() if content else text
        except Exception as e:
            logger.error(f"Failed to translate from English: {e}")
            return text

translation_service = TranslationService()
