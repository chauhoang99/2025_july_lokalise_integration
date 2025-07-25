import pytest
from unittest.mock import MagicMock, patch
from translation_service.services.translation_service import TranslationService
from django.conf import settings

@pytest.fixture
def translation_service():
    """Create a TranslationService instance for testing"""
    return TranslationService()

def test_init(translation_service):
    """Test TranslationService initialization"""
    assert translation_service.lokalise_client is not None
    assert translation_service.openrouter_api_key == settings.OPEN_ROUTER_API_KEY
    assert translation_service.project_id == settings.LOKALISE_PROJECT_ID

def test_translate_with_ai_success(translation_service, mock_requests):
    """Test successful AI translation"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Texto traducido'}}]
    }
    mock_requests['post'].return_value = mock_response

    result = translation_service.translate_with_ai(
        source_text="Test text",
        target_language="es"
    )

    assert result == "Texto traducido"
    mock_requests['post'].assert_called_once()
    call_args = mock_requests['post'].call_args
    assert "openrouter.ai/api/v1/chat/completions" in call_args[0][0]
    assert "Test text" in call_args[1]['json']['messages'][0]['content']

def test_translate_with_ai_error(translation_service, mock_requests):
    """Test AI translation error handling"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "API Error"
    mock_requests['post'].return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        translation_service.translate_with_ai(
            source_text="Test text",
            target_language="es"
        )

    assert "OpenRouter API error" in str(exc_info.value)

def test_check_translation_quality(translation_service):
    """Test translation quality check"""
    source_text = "Hello world"
    reference = "Hola mundo"
    candidate = "Hola mundo"

    result = translation_service.check_translation_quality(
        source_text=source_text,
        reference_translation=reference,
        candidate_translation=candidate
    )

    assert isinstance(result, dict)
    assert 'bleu_score' in result
    assert 'translations' in result
    assert result['translations']['source_text'] == source_text
    assert result['translations']['reference_translation'] == reference
    assert result['translations']['candidate_translation'] == candidate
