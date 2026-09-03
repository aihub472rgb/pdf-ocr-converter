"""
OCR language data management.
Handles Tesseract language packs.
"""

from pathlib import Path
from typing import List, Optional
import logging

from config.paths import get_paths
from config import constants
from exceptions import OCRLanguageNotFoundError

logger = logging.getLogger(__name__)


class LanguageManager:
    """
    Manages OCR language packs.
    
    Responsibilities:
    - Locate Tesseract language data files
    - Validate language availability
    - Provide language metadata
    """

    # Metadata about supported languages
    LANGUAGE_INFO = {
        'eng': {
            'name': 'English',
            'traineddata': 'eng.traineddata',
            'required': True,
        },
        'hin': {
            'name': 'Hindi',
            'traineddata': 'hin.traineddata',
            'required': True,
        },
    }

    def __init__(self):
        """Initialize language manager."""
        self.paths = get_paths()
        self.cached_availability = {}  # Cache language availability checks

    def is_language_available(self, language: str) -> bool:
        """
        Check if language data is available.
        
        Args:
            language: Language code (e.g., 'eng', 'hin')
        
        Returns:
            True if language data found, False otherwise
        """
        # Check cache first
        if language in self.cached_availability:
            return self.cached_availability[language]
        
        # Check if traineddata file exists
        traineddata_path = self.paths.get_tessdata_path(language)
        available = traineddata_path is not None and traineddata_path.exists()
        
        # Cache result
        self.cached_availability[language] = available
        
        if available:
            logger.debug(f"Language available: {language} ({traineddata_path})")
        else:
            logger.warning(f"Language not available: {language}")
        
        return available

    def validate_languages(self, languages: List[str]) -> bool:
        """
        Validate that all required languages are available.
        
        Args:
            languages: List of language codes
        
        Returns:
            True if all available, False otherwise
        
        Raises:
            OCRLanguageNotFoundError: If any language not found
        """
        for lang in languages:
            if not self.is_language_available(lang):
                raise OCRLanguageNotFoundError(lang)
        return True

    def get_language_name(self, language: str) -> str:
        """
        Get human-readable language name.
        
        Args:
            language: Language code
        
        Returns:
            Language name (e.g., "English")
        """
        info = self.LANGUAGE_INFO.get(language, {})
        return info.get('name', language.upper())

    def get_available_languages(self) -> List[str]:
        """
        Get list of available languages.
        
        Returns:
            List of available language codes
        """
        available = []
        for lang in self.LANGUAGE_INFO.keys():
            if self.is_language_available(lang):
                available.append(lang)
        return available

    def get_language_info(self, language: str) -> dict:
        """
        Get language metadata.
        
        Args:
            language: Language code
        
        Returns:
            Dictionary with language info
        """
        return self.LANGUAGE_INFO.get(language, {})

    def get_tessdata_dir(self) -> Path:
        """
        Get path to tessdata directory.
        
        Returns:
            Path to tessdata directory
        """
        return self.paths.tessdata_dir
