import pytest
from unittest.mock import MagicMock, patch
from translation_service.services.lokalise_service import LokaliseService
from django.conf import settings

@pytest.fixture
def mock_lokalise_client():
    """Mock Lokalise client"""
    with patch('translation_service.services.lokalise_service.LokaliseClient') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def lokalise_service(mock_lokalise_client):
    """Create a LokaliseService instance with mocked client"""
    return LokaliseService()

@pytest.fixture
def mock_requests():
    """Mock requests for testing"""
    with patch('translation_service.services.lokalise_service.requests') as mock:
        yield mock

def test_init(lokalise_service, mock_lokalise_client):
    """Test LokaliseService initialization"""
    assert lokalise_service.client == mock_lokalise_client
    assert lokalise_service.project_id == settings.LOKALISE_PROJECT_ID

def test_detect_file_format_json(lokalise_service):
    """Test file format detection for JSON files"""
    result = lokalise_service._detect_file_format('test.json')
    assert result == {
        'plural_format': 'icu',
        'nested_json': False
    }

def test_detect_file_format_nested_json(lokalise_service):
    """Test file format detection for nested JSON files"""
    result = lokalise_service._detect_file_format('test.nested.json')
    assert result == {
        'plural_format': 'icu',
        'nested_json': True
    }

def test_detect_file_format_yaml(lokalise_service):
    """Test file format detection for YAML files"""
    result = lokalise_service._detect_file_format('test.yml')
    assert result == {
        'plural_format': 'icu',
        'nested_yaml': False
    }

def test_upload_file_success(lokalise_service, mock_lokalise_client):
    """Test successful file upload"""
    # Mock file and response
    mock_file = MagicMock()
    mock_file.read.return_value = b"test content"
    mock_response = MagicMock()
    mock_response.process_id = "123"
    mock_lokalise_client.upload_file.return_value = mock_response

    result = lokalise_service.upload_file(
        file=mock_file,
        filename="test.json",
        lang_iso="en",
        detect_icu_plurals=True,
        tags=["test"]
    )

    assert result["status"] == "success"
    assert result["process_id"] == "123"
    assert result["project_id"] == lokalise_service.project_id
    mock_lokalise_client.upload_file.assert_called_once()

def test_get_all_keys_success(lokalise_service, mock_lokalise_client):
    """Test successful all keys fetch"""
    mock_response = MagicMock()
    mock_key = MagicMock()
    mock_key.key_id = "123"
    mock_key.key_name = "test_key"
    mock_key.translations = {"en": {"value": "test"}}
    mock_key.tags = ["tag1"]
    mock_key.description = "description"
    mock_key.platforms = ["web"]
    
    mock_response.items = [mock_key]
    mock_lokalise_client.keys.return_value = mock_response
    
    result = lokalise_service.get_all_keys(include_translations=True)
    
    assert len(result) == 1
    assert result[0]["key_id"] == "123"
    assert result[0]["key_name"] == "test_key"
    assert result[0]["translations"] == {"en": {"value": "test"}}
    assert result[0]["tags"] == ["tag1"]
    assert result[0]["description"] == "description"
    assert result[0]["platforms"] == ["web"]
    mock_lokalise_client.keys.assert_called_once_with(
        project_id=lokalise_service.project_id,
        params={'limit': 1000, 'include_translations': 1}
    )

def test_get_key_translations_success(lokalise_service, mock_lokalise_client):
    """Test successful key translations fetch"""
    mock_key = MagicMock()
    mock_key.key_id = "123"
    mock_key.key_name = "test_key"
    mock_key.translations = {
        "en": {
            "value": "test",
            "is_reviewed": True,
            "is_fuzzy": False
        }
    }
    
    mock_lokalise_client.key.return_value = mock_key
    
    result = lokalise_service.get_key_translations("123")
    
    assert result["key_id"] == "123"
    assert result["key_name"] == "test_key"
    assert result["translations"]["en"]["translation"] == "test"
    assert result["translations"]["en"]["is_reviewed"] is True
    assert result["translations"]["en"]["is_fuzzy"] is False
    mock_lokalise_client.key.assert_called_once_with(
        project_id=lokalise_service.project_id,
        key_id="123",
        params={'include_translations': 1}
    )

def test_upload_translation_success(lokalise_service, mock_requests):
    """Test successful translation upload"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests.put.return_value = mock_response
    
    keys = [{
        "key_id": "123",
        "key_name": "test_key",
        "translations": [{
            "language_iso": "es",
            "translation": "prueba",
            "is_reviewed": True,
            "is_fuzzy": False
        }]
    }]
    
    result = lokalise_service.upload_translation(keys)
    
    assert len(result) == 1
    assert result[0]["key_id"] == "123"
    assert result[0]["status"] == "success"
    mock_requests.put.assert_called_once()

def test_upload_translation_error(lokalise_service, mock_requests):
    """Test translation upload error handling"""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "API Error"
    mock_requests.put.return_value = mock_response
    
    keys = [{
        "key_id": "123",
        "key_name": "test_key",
        "translations": [{
            "language_iso": "es",
            "translation": "prueba"
        }]
    }]
    
    result = lokalise_service.upload_translation(keys)
    
    assert len(result) == 1
    assert result[0]["status"] == "error"
    assert "API error" in result[0]["error"] 