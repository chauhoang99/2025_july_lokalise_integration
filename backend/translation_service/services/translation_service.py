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
