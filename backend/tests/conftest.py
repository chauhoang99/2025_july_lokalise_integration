import pytest
from unittest.mock import MagicMock, patch
from django.conf import settings
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from translation_service.views import TranslationViewSet

@pytest.fixture
def mock_lokalise_client():
    """Mock Lokalise client for testing"""
    with patch('lokalise.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_requests():
    """Mock requests for testing"""
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get, \
         patch('requests.put') as mock_put:
        yield {
            'post': mock_post,
            'get': mock_get,
            'put': mock_put
        }

@pytest.fixture
def sample_glossary_terms():
    """Sample glossary terms for testing"""
    return [
        {
            'term': 'cryptocurrency',
            'translation': 'criptomoneda',
            'description': 'Digital or virtual currency',
            'part_of_speech': 'noun'
        },
        {
            'term': 'wallet',
            'translation': 'billetera',
            'description': 'Digital container for cryptocurrencies',
            'part_of_speech': 'noun'
        }
    ]

@pytest.fixture
def sample_translation_response():
    """Sample OpenRouter API response"""
    return {
        'choices': [
            {
                'message': {
                    'content': 'Translated text here'
                }
            }
        ]
    }

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession for testing"""
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
        def __init__(self, response=None):
            self.response = response or MockResponse()

        async def post(self, *args, **kwargs):
            return self.response

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockClientSession 

@pytest.fixture
def api_urls():
    """Set up URL routing for tests"""
    router = DefaultRouter()
    router.register(r'translations', TranslationViewSet, basename='translation')
    
    urlpatterns = [
        path('', include(router.urls)),
    ]
    return urlpatterns 