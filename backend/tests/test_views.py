import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from translation_service.views import TranslationViewSet
from rest_framework.test import APIClient
from django.urls import reverse
import json
from asgiref.sync import async_to_sync

@pytest.fixture
def api_client():
    """Create API client"""
    return APIClient()

@pytest.fixture
def mock_services():
    """Mock all service initializations"""
    with patch('translation_service.views.TranslationService') as mock_translation_service, \
         patch('translation_service.views.LokaliseService') as mock_lokalise_service, \
         patch('translation_service.views.TranslationPipeline') as mock_translation_pipeline:
        
        # Create mock instances
        mock_translation_service_instance = MagicMock()
        mock_lokalise_service_instance = MagicMock()
        mock_translation_pipeline_instance = MagicMock()
        
        # Set up return values for the class constructors
        mock_translation_service.return_value = mock_translation_service_instance
        mock_lokalise_service.return_value = mock_lokalise_service_instance
        mock_translation_pipeline.return_value = mock_translation_pipeline_instance
        
        yield {
            'translation_service': mock_translation_service_instance,
            'lokalise_service': mock_lokalise_service_instance,
            'translation_pipeline': mock_translation_pipeline_instance
        }

@pytest.fixture
def translation_viewset(mock_services):
    """Create TranslationViewSet instance with mocked services"""
    return TranslationViewSet()

def test_upload_file_success(api_client, translation_viewset, mock_services):
    """Test successful file upload"""
    # Create a valid JSON file content
    json_content = {
        "key1": "value1",
        "key2": "value2"
    }
    file_content = json.dumps(json_content).encode('utf-8')
    file = SimpleUploadedFile(
        "test.json",
        file_content,
        content_type="application/json"
    )
    
    # Set up mock response
    mock_services['lokalise_service'].upload_file.return_value = {"process_id": "123"}
    
    url = reverse('translation-upload-file')
    response = api_client.post(
        url,
        {
            "file": file,
            "lang_iso": "es",
            "detect_icu_plurals": True,
            "tags": ["test"]
        },
        format='multipart'
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["process_id"] == "123"

def test_upload_file_invalid_data(api_client, translation_viewset):
    """Test file upload with invalid data"""
    url = reverse('translation-upload-file')
    response = api_client.post(
        url,
        {},
        format='multipart'
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_upload_file_error(api_client, translation_viewset, mock_services):
    """Test file upload error handling"""
    # Create a valid JSON file content
    json_content = {
        "key1": "value1",
        "key2": "value2"
    }
    file_content = json.dumps(json_content).encode('utf-8')
    file = SimpleUploadedFile(
        "test.json",
        file_content,
        content_type="application/json"
    )
    
    # Set up mock error
    mock_services['lokalise_service'].upload_file.side_effect = Exception("Upload error")
    
    url = reverse('translation-upload-file')
    response = api_client.post(
        url,
        {
            "file": file,
            "lang_iso": "es"
        },
        format='multipart'
    )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "error" in response.data

def test_check_quality_success(api_client, translation_viewset, mock_services):
    """Test successful quality check"""
    # Set up mock response
    mock_services['translation_service'].check_translation_quality.return_value = {
        "bleu_score": 1.0,
        "translations": {
            "source_text": "Hello world",
            "reference_translation": "Hola mundo",
            "candidate_translation": "Hola mundo"
        }
    }
    
    url = reverse('translation-check-quality')
    response = api_client.post(
        url,
        {
            "source_text": "Hello world",
            "existing_translation": "Hola mundo",
            "llm_translation": "Hola mundo",
            "target_language": "es"
        },
        format='json'
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "bleu_score" in response.data
    assert "translations" in response.data

def test_check_quality_missing_data(api_client, translation_viewset):
    """Test quality check with missing data"""
    url = reverse('translation-check-quality')
    response = api_client.post(
        url,
        {
            "source_text": "Hello world"
        },
        format='json'
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data

def test_check_quality_error(api_client, translation_viewset, mock_services):
    """Test quality check error handling"""
    # Set up mock error
    mock_services['translation_service'].check_translation_quality.side_effect = Exception("Quality check error")
    
    url = reverse('translation-check-quality')
    response = api_client.post(
        url,
        {
            "source_text": "Hello world",
            "existing_translation": "Hola mundo",
            "llm_translation": "Hola mundo",
            "target_language": "es"
        },
        format='json'
    )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "error" in response.data

def test_process_translations_success(api_client, translation_viewset, mock_services):
    """Test successful translation processing"""
    mock_results = [
        {
            "key_id": "123",
            "status": "success",
            "translated_text": "Hola mundo"
        }
    ]
    
    # Set up mock response - wrap the coroutine in a synchronous result
    async def mock_async_result(*args, **kwargs):
        return mock_results
    mock_services['translation_pipeline'].process_translations = mock_async_result
    
    url = reverse('translation-process-translations')
    response = api_client.post(
        url,
        {
            "target_language": "es",
            "source_language": "en",
            "force_translate": False
        },
        format='json'
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "total_processed" in response.data
    assert "successful" in response.data
    assert "details" in response.data

def test_process_translations_missing_language(api_client, translation_viewset):
    """Test translation processing with missing target language"""
    url = reverse('translation-process-translations')
    response = api_client.post(
        url,
        {},
        format='json'
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data 