from typing import Dict, List, Optional, BinaryIO
from lokalise import Client as LokaliseClient
from django.conf import settings
import json
import os
from ..validators import LOKALISE_SUPPORTED_FORMATS
import base64
from pprint import pprint
import requests

class LokaliseService:
    def __init__(self):
        self.client = LokaliseClient(settings.LOKALISE_API_KEY)
        self.project_id = settings.LOKALISE_PROJECT_ID

    def _detect_file_format(self, filename: str) -> Dict:
        """
        Detect file format and return appropriate Lokalise options
        """
        file_ext = os.path.splitext(filename.lower())[1]
        base_name = os.path.splitext(filename)[0]
        
        # Handle nested formats
        if file_ext in ['.json', '.yml', '.yaml'] and base_name.endswith('.nested'):
            is_nested = True
        else:
            is_nested = False

        format_options = {
            'json': {
                'plural_format': 'icu',
                'nested_json': is_nested
            },
            'yaml': {
                'plural_format': 'icu',
                'nested_yaml': is_nested
            },
            'xml': {
                'extract_plurals': True
            },
            'properties': {
                'escape_quotes': 2
            },
            'strings': {
                'escape_quotes': 2
            }
        }

        # Get format key from extension
        format_key = file_ext.lstrip('.')
        if format_key == 'yml':
            format_key = 'yaml'

        return format_options.get(format_key, {})

    def upload_file(self, file: BinaryIO, filename: str, lang_iso: str, detect_icu_plurals: bool = True, tags: List[str] = None) -> Dict:
        """
        Upload a file to Lokalise
        """
        try:
            # Get format-specific options
            format_options = self._detect_file_format(filename)

            # Prepare upload options
            file_content = file.read()
            base64_data = base64.b64encode(file_content).decode("utf-8")
            options = {
                "filename": filename,
                "lang_iso": 'en',
                "detect_icu_plurals": detect_icu_plurals,
                "replace_modified": False,
                "skip_detect_lang_iso": False,
                "convert_placeholders": True,
                "format_options": format_options,
                "data": base64_data
            }

            if tags:
                options["tags"] = tags

            # Upload the file using the correct API method
            response = self.client.upload_file(
                self.project_id,
                options
            )

            return {
                "status": "success",
                "process_id": response.process_id,
                "project_id": self.project_id,
                "file_format": LOKALISE_SUPPORTED_FORMATS.get(os.path.splitext(filename.lower())[1]),
            }

        except Exception as e:
            raise Exception(f"Error uploading file: {str(e)}")

    def get_all_keys(self, include_translations: bool = True) -> List[Dict]:
        """Get all keys from the project"""
        try:
            params = {
                'limit': 1000,  # Adjust as needed
                'include_translations': 1 if include_translations else 0
            }
            response = self.client.keys(
                project_id=self.project_id,
                params=params
            )
            # The response is already a list of keys
            return [{
                'key_id': key.key_id,
                'key_name': key.key_name,
                'translations': key.translations if include_translations else [],
                'tags': key.tags or [],
                'description': key.description,
                'platforms': key.platforms
            } for key in response.items]            
        except Exception as e:
            print(f"Debug - Response type: {type(response)}")  # Debug log
            print(f"Debug - Response: {response}")  # Debug log
            raise Exception(f"Error fetching keys: {str(e)}")

    def get_key_translations(self, key_id: str) -> Dict:
        """Get translations for a specific key"""
        try:
            key = self.client.key(
                project_id=self.project_id,
                key_id=key_id,
                params={'include_translations': 1}
            )
            
            return {
                'key_id': key.key_id,
                'key_name': key.key_name,
                'translations': {
                    lang: {
                        'translation': trans.get('value', ''),
                        'is_reviewed': trans.get('is_reviewed', False),
                        'is_fuzzy': trans.get('is_fuzzy', False)
                    }
                    for lang, trans in key.translations.items()
                }
            }
            
        except Exception as e:
            print(f"Debug - Key response type: {type(key)}")  # Debug log
            print(f"Debug - Key response: {key}")  # Debug log
            raise Exception(f"Error fetching key translations: {str(e)}")

    def upload_translation(self, keys: List[Dict]) -> List[Dict]:
        """
        Upload translations one key at a time using direct API calls
        
        Args:
            keys: List of keys with their translations
            
        Returns:
            List of results for each key upload
        """
        results = []
        headers = {
            'X-Api-Token': settings.LOKALISE_API_KEY,
            'Content-Type': 'application/json'
        }
        
        for key in keys:
            try:
                # Prepare translations data
                translations = []
                for trans in key['translations']:
                    translations.append({
                        'language_iso': trans['language_iso'],
                        'translation': trans['translation'],
                        'is_reviewed': trans.get('is_reviewed', False),
                        'is_fuzzy': trans.get('is_fuzzy', True)
                    })

                # Make API request to update key
                response = requests.put(
                    f'https://api.lokalise.com/api2/projects/{self.project_id}/keys/{key["key_id"]}',
                    headers=headers,
                    json={
                        'translations': translations
                    }
                )
                if response.status_code != 200:
                    raise Exception(f"API error: {response.text}")
                
                results.append({
                    'key_id': key['key_id'],
                    'key_name': key['key_name'],
                    'status': 'success'
                })
                
            except Exception as e:
                print(f"Error uploading key {key['key_id']}: {str(e)}")
                results.append({
                    'key_id': key['key_id'],
                    'key_name': key['key_name'],
                    'status': 'error',
                    'error': str(e)
                })
                
        return results

        """Mark a translation as reviewed"""
        try:
            response = self.client.translations(
                project_id=self.project_id,
                key_id=key_id,
                language_code=language_code,
                params={
                    'is_reviewed': True,
                    'is_fuzzy': False
                }
            )
            return {
                'key_id': key_id,
                'language': language_code,
                'status': 'reviewed'
            }
        except Exception as e:
            print(f"Debug - Review response type: {type(response)}")  # Debug log
            print(f"Debug - Review response: {response}")  # Debug log
            raise Exception(f"Error marking translation as reviewed: {str(e)}") 