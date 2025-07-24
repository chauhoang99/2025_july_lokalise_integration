from rest_framework import serializers
import os
from typing import Dict
from django.conf import settings

# Lokalise supported file formats and their extensions
LOKALISE_SUPPORTED_FORMATS: Dict[str, str] = {
    # Key-value formats
    '.properties': 'Java Properties',
    '.strings': 'iOS Strings',
    '.stringsdict': 'iOS Stringsdict',
    '.plist': 'iOS Plist',
    '.xml': 'Android XML/XLIFF/HTML',
    '.resx': '.NET RESX',
    '.resw': 'UWP RESW',
    '.ts': 'QT Linguist',
    
    # Document formats
    '.json': 'JSON',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.po': 'GNU gettext',
    '.pot': 'GNU gettext template',
    '.csv': 'CSV',
    '.xlsx': 'Excel',
    '.xls': 'Excel',
    
    # Framework-specific
    '.arb': 'Flutter ARB',
    '.ini': 'INI',
    '.toml': 'TOML',
    
    # Nested formats
    '.nested.json': 'Nested JSON',
    '.nested.yml': 'Nested YAML',
    '.nested.yaml': 'Nested YAML'
}

def validate_target_language(target_language: str) -> str:
    """
    Validate if the target language is supported
    
    Args:
        target_language: Language code to validate
        
    Returns:
        str: The validated language code
        
    Raises:
        serializers.ValidationError: If language is not supported
    """
    if target_language not in settings.SUPPORTING_LANGUAGES:
        raise serializers.ValidationError(
            f"Language '{target_language}' is not supported. "
            f"Supported languages are: {', '.join(settings.SUPPORTING_LANGUAGES)}"
        )
    return target_language

def validate_lokalise_file_type(file) -> None:
    """
    Validate if the file type is supported by Lokalise
    
    Args:
        file: UploadedFile object
        
    Raises:
        serializers.ValidationError: If file type is not supported
    """
    if not file:
        raise serializers.ValidationError("No file was submitted")

    # Get the file extension
    filename = file.name.lower()
    file_ext = os.path.splitext(filename)[1]
    
    # Handle nested formats
    if file_ext in ['.json', '.yml', '.yaml']:
        base_name = os.path.splitext(os.path.splitext(filename)[0])[0]
        if base_name.endswith('.nested'):
            file_ext = '.nested' + file_ext

    # Check if extension is supported
    if file_ext not in LOKALISE_SUPPORTED_FORMATS:
        supported_formats = ', '.join(sorted(LOKALISE_SUPPORTED_FORMATS.keys()))
        raise serializers.ValidationError(
            f"Unsupported file type '{file_ext}'. Supported formats are: {supported_formats}"
        )

def validate_file_size(file, max_size_mb: int = 10) -> None:
    """
    Validate file size
    
    Args:
        file: UploadedFile object
        max_size_mb: Maximum file size in megabytes
        
    Raises:
        serializers.ValidationError: If file is too large
    """
    if not file:
        raise serializers.ValidationError("No file was submitted")

    # Convert MB to bytes
    max_size_bytes = max_size_mb * 1024 * 1024

    if file.size > max_size_bytes:
        raise serializers.ValidationError(
            f"File size ({file.size / 1024 / 1024:.1f}MB) exceeds maximum allowed size of {max_size_mb}MB"
        ) 