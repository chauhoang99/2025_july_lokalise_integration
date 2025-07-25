import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from translation_service.services.translation_pipeline import TranslationPipeline
import asyncio

class MockResponse:
    def __init__(self, status=200, json_data=None):
        self.status = status
        self._json_data = json_data or {}

    async def json(self):
        return self._json_data

    async def text(self):
        return str(self._json_data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class MockClientSession:
    def __init__(self, mock_response=None):
        self.mock_response = mock_response or MockResponse()

    def post(self, *args, **kwargs):
        return self.mock_response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def mock_aiohttp_session():
    def _create_session(status=200, json_data=None):
        session = MockClientSession()
        session.mock_response = MockResponse(status=status, json_data=json_data)
        return session
    return _create_session

@pytest.fixture
def mock_lokalise_service():
    """Mock LokaliseService"""
    with patch('translation_service.services.translation_pipeline.LokaliseService') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def translation_pipeline(mock_lokalise_service):
    """Create a TranslationPipeline instance with mocked services"""
    with patch('builtins.open', mock_open(read_data=json.dumps({
        'translations': [
            {
                'term': 'cryptocurrency',
                'translations': [
                    {'language_iso': 'es', 'translation': 'criptomoneda'}
                ],
                'description': 'Digital currency',
                'part_of_speech': 'noun'
            }
        ]
    }))):
        pipeline = TranslationPipeline()
        pipeline.lokalise_service = mock_lokalise_service
        return pipeline

def test_init(translation_pipeline):
    """Test TranslationPipeline initialization"""
    assert translation_pipeline.lokalise_service is not None
    assert translation_pipeline.openrouter_api_key is not None
    assert translation_pipeline.glossary is not None

def test_get_relevant_glossary_terms(translation_pipeline):
    """Test getting relevant glossary terms"""
    source_text = "This is a cryptocurrency wallet"
    target_language = "es"
    
    result = translation_pipeline._get_relevant_glossary_terms(source_text, target_language)
    
    assert len(result) == 1
    assert result[0]["term"] == "cryptocurrency"
    assert result[0]["translation"] == "criptomoneda"

def test_format_glossary_terms(translation_pipeline):
    """Test formatting glossary terms"""
    terms = [
        {
            "term": "test",
            "translation": "prueba",
            "description": "A test term",
            "part_of_speech": "noun"
        }
    ]
    
    result = translation_pipeline._format_glossary_terms(terms)
    
    assert "test → prueba" in result
    assert "Description: A test term" in result
    assert "Part of Speech: noun" in result

@pytest.mark.asyncio
async def test_translate_with_ai_success(translation_pipeline, mock_aiohttp_session):
    """Test successful AI translation"""
    session = mock_aiohttp_session(
        json_data={
            'choices': [{'message': {'content': 'Texto traducido'}}]
        }
    )
    
    async with session as s:
        result = await translation_pipeline.translate_with_ai(
            source_text="Test text",
            target_language="es",
            session=s
        )
    
    assert result == "Texto traducido"

@pytest.mark.asyncio
async def test_translate_with_ai_error(translation_pipeline, mock_aiohttp_session):
    """Test AI translation error handling"""
    session = mock_aiohttp_session(
        status=500,
        json_data={"error": "API Error"}
    )
    
    async with session as s:
        with pytest.raises(Exception) as exc_info:
            await translation_pipeline.translate_with_ai(
                source_text="Test text",
                target_language="es",
                session=s
            )
    
    assert "OpenRouter API error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_process_translations_success(translation_pipeline, mock_lokalise_service, mock_aiohttp_session):
    """Test successful translation processing"""
    # Mock Lokalise service responses
    mock_key = {
        'key_id': "123",
        'key_name': "test_key",
        'translations': [
            {"language_iso": "en", "translation": "test"}
        ]
    }
    
    mock_lokalise_service.get_all_keys.return_value = [mock_key]
    mock_lokalise_service.upload_translation.return_value = [{
        'key_id': "123",
        'status': 'success'
    }]
    
    # Mock AI translation response
    session = mock_aiohttp_session(
        json_data={
            'choices': [{'message': {'content': 'prueba'}}]
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=session):
        result = await translation_pipeline.process_translations(
            target_language="es",
            source_language="en"
        )
    
    assert len(result) == 1
    assert result[0]["status"] == "success"
    assert result[0]["key_id"] == "123"
    assert result[0]["translated_text"] == "prueba"

@pytest.mark.asyncio
async def test_process_translations_skip_existing(translation_pipeline, mock_lokalise_service):
    """Test skipping existing translations"""
    mock_key = {
        'key_id': "123",
        'key_name': "test_key",
        'translations': [
            {"language_iso": "en", "translation": "test"},
            {"language_iso": "es", "translation": "prueba"}
        ]
    }
    
    mock_lokalise_service.get_all_keys.return_value = [mock_key]
    
    result = await translation_pipeline.process_translations(
        target_language="es",
        source_language="en",
        force_translate=False
    )
    
    assert len(result) == 1
    assert result[0]["status"] == "skipped"
    assert result[0]["reason"] == "Translation already exists"

@pytest.mark.asyncio
async def test_process_translations_no_source(translation_pipeline, mock_lokalise_service):
    """Test handling missing source text"""
    mock_key = {
        'key_id': "123",
        'key_name': "test_key",
        'translations': []
    }
    
    mock_lokalise_service.get_all_keys.return_value = [mock_key]
    
    result = await translation_pipeline.process_translations(
        target_language="es",
        source_language="en"
    )
    
    assert len(result) == 1
    assert result[0]["status"] == "skipped"
    assert "No en source text available" in result[0]["reason"] 