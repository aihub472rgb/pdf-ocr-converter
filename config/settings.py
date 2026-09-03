"""
Application settings management.
Handles user preferences and configuration.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum

from . import constants
from .paths import get_paths


class ExistingOCRAction(Enum):
    """How to handle existing OCR in PDF."""
    PRESERVE = "preserve"       # Keep existing, skip pages with text
    RE_OCR = "re_ocr"           # Re-OCR all pages
    SMART = "smart"             # Re-OCR only low-quality text


@dataclass
class PreprocessingConfig:
    """Image preprocessing settings."""
    enable_deskew: bool = True
    enable_denoise: bool = True
    enable_contrast: bool = True
    enable_threshold: bool = False
    preserve_quality: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreprocessingConfig':
        return cls(**{k: v for k, v in data.items() if k in asdict(cls())})


@dataclass
class OCRConfig:
    """OCR settings."""
    languages: List[str] = field(default_factory=lambda: constants.DEFAULT_LANGUAGES)
    enable_language_detection: bool = False
    existing_ocr_action: ExistingOCRAction = ExistingOCRAction.PRESERVE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'languages': self.languages,
            'enable_language_detection': self.enable_language_detection,
            'existing_ocr_action': self.existing_ocr_action.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OCRConfig':
        action_str = data.get('existing_ocr_action', 'preserve')
        try:
            action = ExistingOCRAction(action_str)
        except ValueError:
            action = ExistingOCRAction.PRESERVE
        
        return cls(
            languages=data.get('languages', constants.DEFAULT_LANGUAGES),
            enable_language_detection=data.get('enable_language_detection', False),
            existing_ocr_action=action,
        )


@dataclass
class ProcessingConfig:
    """Processing pipeline settings."""
    worker_count: int = constants.DEFAULT_WORKER_COUNT
    max_retries: int = constants.MAX_PAGE_RETRIES
    page_timeout_seconds: int = constants.PAGE_PROCESSING_TIMEOUT_SECONDS
    enable_gpu: bool = False  # Not yet implemented

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingConfig':
        return cls(**{k: v for k, v in data.items() if k in asdict(cls())})


@dataclass
class OutputConfig:
    """Output PDF settings."""
    optimize_pdf: bool = constants.ENABLE_PDF_OPTIMIZATION
    compression_level: int = constants.COMPRESSION_LEVEL
    generate_cover_page: bool = constants.GENERATE_COVER_PAGE_DEFAULT

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OutputConfig':
        return cls(**{k: v for k, v in data.items() if k in asdict(cls())})


class Settings:
    """
    Global application settings.
    Manages user preferences and configuration persistence.
    """

    SETTINGS_FILENAME = "settings.json"

    def __init__(self):
        """
        Initialize settings from disk or create defaults.
        """
        self.paths = get_paths()
        self.settings_file = self.paths.app_data_dir / self.SETTINGS_FILENAME

        # Initialize with defaults
        self.ocr = OCRConfig()
        self.preprocessing = PreprocessingConfig()
        self.processing = ProcessingConfig()
        self.output = OutputConfig()
        self.last_input_dir = str(self.paths.user_home)
        self.last_output_dir = str(self.paths.user_home)

        # Load from disk if exists
        self.load()

    def load(self) -> bool:
        """
        Load settings from disk.
        
        Returns:
            True if loaded successfully, False if file doesn't exist or error
        """
        if not self.settings_file.exists():
            return False

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load each config section
            if 'ocr' in data:
                self.ocr = OCRConfig.from_dict(data['ocr'])
            if 'preprocessing' in data:
                self.preprocessing = PreprocessingConfig.from_dict(data['preprocessing'])
            if 'processing' in data:
                self.processing = ProcessingConfig.from_dict(data['processing'])
            if 'output' in data:
                self.output = OutputConfig.from_dict(data['output'])
            if 'last_input_dir' in data:
                self.last_input_dir = data['last_input_dir']
            if 'last_output_dir' in data:
                self.last_output_dir = data['last_output_dir']
            
            return True
        except Exception as e:
            print(f"Error loading settings: {e}")
            return False

    def save(self) -> bool:
        """
        Save settings to disk.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            self.paths.ensure_path_exists(self.settings_file, is_file=True)

            # Prepare data
            data = {
                'ocr': self.ocr.to_dict(),
                'preprocessing': self.preprocessing.to_dict(),
                'processing': self.processing.to_dict(),
                'output': self.output.to_dict(),
                'last_input_dir': self.last_input_dir,
                'last_output_dir': self.last_output_dir,
            }

            # Write to disk
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def reset_to_defaults(self):
        """
        Reset all settings to defaults.
        """
        self.ocr = OCRConfig()
        self.preprocessing = PreprocessingConfig()
        self.processing = ProcessingConfig()
        self.output = OutputConfig()
        self.last_input_dir = str(self.paths.user_home)
        self.last_output_dir = str(self.paths.user_home)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert all settings to dictionary.
        
        Returns:
            Dictionary representation of all settings
        """
        return {
            'ocr': self.ocr.to_dict(),
            'preprocessing': self.preprocessing.to_dict(),
            'processing': self.processing.to_dict(),
            'output': self.output.to_dict(),
            'last_input_dir': self.last_input_dir,
            'last_output_dir': self.last_output_dir,
        }


# Global singleton instance
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global Settings instance (singleton).
    
    Returns:
        Settings instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
