import requests
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from .lokalise_service import LokaliseService
from pprint import pprint
import asyncio
import aiohttp
import json
import os

LLM_MODEL = 'openai/gpt-4o-mini'

class TranslationPipeline:
    def __init__(self):
        self.lokalise_service = LokaliseService()
        self.openrouter_api_key = settings.OPEN_ROUTER_API_KEY
        # Load glossary
        glossary_path = os.path.join(settings.BASE_DIR, 'core', 'statics', 'glossary.json')
        with open(glossary_path, 'r', encoding='utf-8') as f:
            self.glossary = json.load(f)

    def _get_relevant_glossary_terms(self, source_text: str, target_language: str) -> List[Dict]:
        """Get glossary terms that appear in the source text"""
        relevant_terms = []
        
        for term_entry in self.glossary['translations']:
            if term_entry['term'].lower() in source_text.lower():
                # Find target language translation
                target_trans = next(
                    (t for t in term_entry['translations'] 
                     if t['language_iso'] == target_language),
                    None
                )
                
                if target_trans:
                    relevant_terms.append({
                        'term': term_entry['term'],
                        'translation': target_trans['translation'],
                        'description': term_entry.get('description', ''),
                        'part_of_speech': term_entry.get('part_of_speech', '')
                    })
        
        return relevant_terms

    def _format_glossary_terms(self, terms: List[Dict]) -> str:
        """Format glossary terms for the prompt"""
        if not terms:
            return ""
            
        formatted_terms = []
        for term in terms:
            term_info = [
                f"- {term['term']} → {term['translation']}"
            ]
            if term['description']:
                term_info.append(f"  Description: {term['description']}")
            if term['part_of_speech']:
                term_info.append(f"  Part of Speech: {term['part_of_speech']}")
            formatted_terms.append('\n'.join(term_info))
            
        return "Glossary Terms:\n" + '\n\n'.join(formatted_terms)

    async def translate_with_ai(self, source_text: str, target_language: str, session: aiohttp.ClientSession) -> str:
        """
        Translate text using OpenRouter's AI model with glossary support
        """
        # Get relevant glossary terms
        relevant_terms = self._get_relevant_glossary_terms(source_text, target_language)
        glossary_section = self._format_glossary_terms(relevant_terms)
        
        prompt = f"""Translate the following text to {'Italian' if target_language == 'it' else target_language}.

Here is the glossary:
{glossary_section}

Translation Guidelines:
1. Maintain the original meaning, tone, and formatting
2. Use the provided glossary terms exactly as shown when they appear
3. Preserve any special characters, numbers, or formatting
4. Keep any untranslatable terms (like product names) unchanged
5. Maintain any HTML or markdown formatting if present

Text to translate:
{source_text}

Translation:"""

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "${YOUR_SITE_URL}",
            "X-Title": "Lokalise Translation Pipeline"
        }

        data = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }

        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"OpenRouter API error: {text}")
            
            json_response = await response.json()
            return json_response["choices"][0]["message"]["content"].strip()

    async def process_translations(self, target_language: str, source_language: str = 'en', force_translate: bool = False) -> List[Dict]:
        """
        Process translations for all keys
        
        Args:
            target_language: Language to translate to
            source_language: Source language (default: 'en')
            force_translate: Whether to translate even if translation exists
            
        Returns:
            List of results for each key
        """
        results = []
        translation_tasks = []
        keys_to_translate = []
        
        # Get all keys with their translations
        all_keys = self.lokalise_service.get_all_keys(include_translations=True)

        # Prepare translation tasks
        async with aiohttp.ClientSession() as session:
            for key in all_keys:
                # Get source text
                source_trans = next((i for i in key['translations'] if i['language_iso'] == source_language), {})
                source_text = source_trans.get('translation', '')
                
                # Check if we should translate this key
                target_trans = next((i for i in key['translations'] if i['language_iso'] == target_language), {})
                has_translation = bool(target_trans.get('translation', ''))
                
                if not source_text:
                    results.append({
                        'key_id': key['key_id'],
                        'key_name': key['key_name'],
                        'status': 'skipped',
                        'reason': f'No {source_language} source text available',
                    })
                    continue
                    
                if has_translation and not force_translate:
                    results.append({
                        'key_id': key['key_id'],
                        'key_name': key['key_name'],
                        'status': 'skipped',
                        'reason': 'Translation already exists',
                        'source_text': source_text,
                        'existing_translation': target_trans.get('translation', '')
                    })
                    continue

                # Add to translation tasks
                translation_tasks.append(self.translate_with_ai(source_text, target_language, session))
                keys_to_translate.append((key, source_text, target_trans, has_translation))

            # Execute all translations concurrently
            try:
                translated_texts = await asyncio.gather(*translation_tasks)

                # Map results back to keys
                for (key, source_text, target_trans, has_translation), translated_text in zip(keys_to_translate, translated_texts):
                    results.append({
                        'key_id': key['key_id'],
                        'key_name': key['key_name'],
                        'status': 'success',
                        'source_text': source_text,
                        'translated_text': translated_text,
                        'existing_translation': target_trans.get('translation', ''),
                        'is_new_translation': not has_translation
                    })
                    key['key_id'] = int(key['key_id'])

                    if target_trans == {}:
                        target_trans['translation'] = translated_text
                        target_trans['is_reviewed'] = False
                        target_trans['is_fuzzy'] = True
                        target_trans['language_iso'] = target_language
                        target_trans['key_id'] = int(key['key_id'])
                        target_trans['words'] = len(translated_text.split(' '))
                        key['translations'].append(target_trans)
                    else:
                        target_trans['translation'] = translated_text
                        target_trans['key_id'] = int(key['key_id'])

            except Exception as e:
                # If a translation fails, add error results for remaining keys
                for key, source_text, _, _ in keys_to_translate:
                    results.append({
                        'key_id': key['key_id'],
                        'key_name': key['key_name'],
                        'status': 'error',
                        'error': str(e)
                    })

        # Bulk update translations
        upload_results = self.lokalise_service.upload_translation(all_keys)
        
        # Update results with upload status
        for upload_result in upload_results:
            for result in results:
                if result['key_id'] == upload_result['key_id']:
                    if upload_result['status'] == 'error':
                        result['status'] = 'error'
                        result['error'] = upload_result.get('error', 'Upload failed')
                    break

        return results