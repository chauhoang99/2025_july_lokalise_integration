import requests
from django.conf import settings
from lokalise import Client as LokaliseClient
from typing import Dict, List, Optional
from ..utils.bleu_scorer import compute_bleu_score

class TranslationService:
    def __init__(self):
        self.lokalise_client = LokaliseClient(settings.LOKALISE_API_KEY)
        self.openrouter_api_key = settings.OPEN_ROUTER_API_KEY
        self.project_id = settings.LOKALISE_PROJECT_ID

    def get_lokalise_glossary(self) -> List[Dict]:
        """Fetch glossary terms from Lokalise"""
        try:
            # This is a placeholder - actual implementation will depend on Lokalise API structure
            return self.lokalise_client.glossaries.list(self.project_id)
        except Exception as e:
            raise Exception(f"Error fetching glossary: {str(e)}")

    def translate_with_ai(self, source_text: str, target_language: str) -> str:
        """
        Use OpenRouter's AI model to translate the text
        """
        prompt = f"""
        Translate the following text to {target_language}. 
        Maintain the original meaning, tone, and formatting.
        
        Text to translate:
        {source_text}
        
        Translation:
        """

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "${YOUR_SITE_URL}",  # Replace with your site URL
            "X-Title": "Lokalise AI Translation"
        }

        data = {
            "model": "openai/gpt-3.5-turbo",  # Free model for POC
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.text}")

        return response.json()["choices"][0]["message"]["content"].strip()

    def check_translation_quality(self, source_text: str, reference_translation: str, candidate_translation: str) -> Dict:
        """
        Compute BLEU score for translation quality
        
        Args:
            source_text: Original text (for reference)
            reference_translation: Reference translation to compare against
            candidate_translation: Candidate translation to evaluate
            
        Returns:
            Dict containing BLEU score and translations
        """
        bleu_score = compute_bleu_score(reference_translation, candidate_translation)
        
        return {
            "bleu_score": bleu_score,
            "translations": {
                "source_text": source_text,
                "reference_translation": reference_translation,
                "candidate_translation": candidate_translation
            }
        }

    def fine_tune_translation(self, source_text: str, initial_translation: str, 
                            glossary_terms: List[Dict], target_language: str) -> str:
        """
        Fine-tune the translation using OpenRouter and glossary terms
        """
        # Format glossary terms for the prompt
        glossary_context = "\n".join([
            f"- {term['term']}: {term['translation']}"
            for term in glossary_terms
        ])

        prompt = f"""
        Please improve this translation using the provided glossary terms:

        Source Text: {source_text}
        Initial Translation: {initial_translation}
        Target Language: {target_language}

        Glossary Terms:
        {glossary_context}

        Please provide an improved translation that:
        1. Accurately reflects the source meaning
        2. Uses the correct glossary terms
        3. Maintains natural language flow
        4. Is culturally appropriate
        """

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "anthropic/claude-3-opus-20240229",
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.text}")

        return response.json()["choices"][0]["message"]["content"] 