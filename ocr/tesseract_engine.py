"""
Tesseract OCR engine wrapper.
Provides high-level interface to Tesseract OCR.
"""

from typing import Dict, Optional, List
import logging
import numpy as np
from pathlib import Path

try:
    import pytesseract
except ImportError:
    pytesseract = None

from exceptions import (
    OCREngineError,
    OCRLanguageNotFoundError,
    OCRTimeoutError,
    OCRProcessingError,
)
from config import constants
from .language_manager import LanguageManager

logger = logging.getLogger(__name__)


class TesseractOCREngine:
    """
    Tesseract OCR engine wrapper.
    
    Handles:
    - Language data validation
    - Image-to-text OCR
    - Confidence scoring
    - Multiple language support
    - HOCR output (for text layer injection)
    """

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        tesseract_path: Optional[Path] = None,
    ):
        """
        Initialize Tesseract OCR engine.
        
        Args:
            languages: List of language codes (e.g., ['eng', 'hin'])
            tesseract_path: Path to tesseract executable (auto-detect if None)
        
        Raises:
            OCREngineError: If Tesseract not available
        """
        if pytesseract is None:
            raise OCREngineError("pytesseract is not installed")
        
        self.languages = languages or constants.DEFAULT_LANGUAGES
        self.lang_manager = LanguageManager()
        self.tesseract_path = tesseract_path
        
        # Validate languages
        for lang in self.languages:
            if not self.lang_manager.is_language_available(lang):
                raise OCRLanguageNotFoundError(lang)
        
        # Configure pytesseract
        if tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = str(tesseract_path)
        
        # Language string for Tesseract
        self.lang_string = '+'.join(self.languages)
        
        logger.info(f"Tesseract OCR engine initialized: {self.lang_string}")

    def ocr_image(
        self,
        image: np.ndarray,
        timeout_seconds: int = constants.OCR_TIMEOUT_SECONDS,
    ) -> Dict[str, any]:
        """
        Perform OCR on image.
        
        Args:
            image: Image as numpy array (RGB or grayscale)
            timeout_seconds: OCR timeout
        
        Returns:
            Dictionary with OCR results:
            {
                'text': 'Extracted text',
                'confidence': 0.87,  # 0.0-1.0
                'hocr': '<html><body>...',  # HOCR for coordinates
                'success': True,
            }
        
        Raises:
            OCRProcessingError: If OCR fails
            OCRTimeoutError: If OCR times out
        """
        try:
            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=self.lang_string,
            )
            
            # Get confidence scores
            data = pytesseract.image_to_data(
                image,
                lang=self.lang_string,
                output_type=pytesseract.Output.DICT,
            )
            
            # Calculate average confidence
            confidences = [int(c) for c in data['conf'] if int(c) > 0]
            confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
            
            # Get HOCR for text layer injection
            hocr = pytesseract.image_to_pdf_or_hocr(
                image,
                lang=self.lang_string,
                extension='hocr',
            ).decode('utf-8', errors='ignore')
            
            return {
                'text': text,
                'confidence': min(1.0, confidence),
                'hocr': hocr,
                'success': True,
            }
        
        except pytesseract.TesseractNotFoundError as e:
            raise OCREngineError(f"Tesseract not found: {e}")
        except Exception as e:
            if "timeout" in str(e).lower():
                raise OCRTimeoutError(f"OCR timed out after {timeout_seconds}s")
            raise OCRProcessingError(f"OCR processing failed: {e}")

    def ocr_image_to_pdf(
        self,
        image: np.ndarray,
    ) -> bytes:
        """
        Perform OCR and generate PDF with text layer.
        
        Args:
            image: Image as numpy array
        
        Returns:
            PDF bytes with embedded text layer
        
        Raises:
            OCRProcessingError: If OCR fails
        """
        try:
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                image,
                lang=self.lang_string,
                extension='pdf',
            )
            return pdf_bytes
        except Exception as e:
            raise OCRProcessingError(f"Failed to generate PDF from image: {e}")

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages.
        
        Returns:
            List of language codes
        """
        return self.languages

    def check_language_available(self, language: str) -> bool:
        """
        Check if language data is available.
        
        Args:
            language: Language code
        
        Returns:
            True if available, False otherwise
        """
        return self.lang_manager.is_language_available(language)
