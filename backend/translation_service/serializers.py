from rest_framework import serializers

class TranslationRequestSerializer(serializers.Serializer):
    source_text = serializers.CharField(required=True)
    target_language = serializers.CharField(required=True)

class QualityCheckSerializer(serializers.Serializer):
    source_text = serializers.CharField(required=True)
    translated_text = serializers.CharField(required=True)
    target_language = serializers.CharField(required=True)

class TranslationFineTuneSerializer(serializers.Serializer):
    source_text = serializers.CharField(required=True)
    translated_text = serializers.CharField(required=True)
    target_language = serializers.CharField(required=True)
    feedback = serializers.CharField(required=True)

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    lang_iso = serializers.CharField(required=True)
    detect_icu_plurals = serializers.BooleanField(required=False, default=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )

    def validate_file(self, value):
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:  # 10MB in bytes
            raise serializers.ValidationError("File size cannot exceed 10MB")
        return value

    def validate_lang_iso(self, value):
        # Add validation for supported languages if needed
        return value.lower()

class ProcessIdSerializer(serializers.Serializer):
    process_id = serializers.CharField(required=True) 