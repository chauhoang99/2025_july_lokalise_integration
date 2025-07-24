from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .services import TranslationService
from .serializers import (
    FileUploadSerializer,
    QualityCheckSerializer
)
from typing import Dict, Any
from .services.translation_pipeline import TranslationPipeline
from .services.lokalise_service import LokaliseService
import requests
from asgiref.sync import async_to_sync

class TranslationViewSet(viewsets.ViewSet):    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.translation_pipeline = TranslationPipeline()
        self.lokalise_service = LokaliseService()
        self.translation_service = TranslationService()

    @action(detail=False, methods=['POST'], url_path='upload-file')
    def upload_file(self, request) -> Response:
        """
        Upload a file to Lokalise for translation
        """
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            file = request.FILES['file']
            result = self.lokalise_service.upload_file(
                file=file,
                filename=file.name,
                lang_iso=serializer.validated_data['lang_iso'],
                detect_icu_plurals=serializer.validated_data.get('detect_icu_plurals', True),
                tags=serializer.validated_data.get('tags')
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def check_quality(self, request) -> Response:
        """
        Check translation quality and compute BLEU score between existing and LLM translations
        """
        # try:
        source_text = request.data.get('source_text')
        existing_translation = request.data.get('existing_translation')
        llm_translation = request.data.get('llm_translation')
        target_language = request.data.get('target_language')

        if not all([source_text, existing_translation, llm_translation, target_language]):
            return Response(
                {"error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use translation service for quality check
        result = self.translation_service.check_translation_quality(
            source_text,
            existing_translation,
            llm_translation,
        )

        return Response(result, status=status.HTTP_200_OK)

        # except Exception as e:
        #     return Response(
        #         {"error": str(e)},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )

    @action(detail=False, methods=['POST'], url_path='process-translations')
    def process_translations(self, request) -> Response:
        """
        Process translations for all keys in Lokalise:
        1. Get keys from Lokalise
        2. Translate each key using AI
        3. Upload translations back to Lokalise
        """
        target_language = request.data.get('target_language')
        source_language = request.data.get('source_language', 'en')
        force_translate = request.data.get('force_translate', False)

        if not target_language:
            return Response(
                {"error": "Target language is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert async call to sync
        results = async_to_sync(self.translation_pipeline.process_translations)(
            target_language=target_language,
            source_language=source_language,
            force_translate=force_translate
        )

        summary = {
            'total_processed': len(results),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'error']),
            'skipped': len([r for r in results if r['status'] == 'skipped']),
            'new_translations': len([r for r in results if r['status'] == 'success' and r.get('is_new_translation', False)]),
            'updated_translations': len([r for r in results if r['status'] == 'success' and not r.get('is_new_translation', False)]),
            'details': results
        }

        return Response(summary, status=status.HTTP_200_OK) 