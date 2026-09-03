"""
OCR package for PDF OCR Converter.
"""
from .tesseract_engine import TesseractOCREngine
from .language_manager import LanguageManager
from .text_layer import TextLayerInjector

__all__ = [
    'TesseractOCREngine',
    'LanguageManager',
    'TextLayerInjector',
]
