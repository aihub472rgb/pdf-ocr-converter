"""
PDF validation module.
Validates PDF files before processing.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from exceptions import (
    PDFValidationError,
    PDFCorruptedError,
    PDFEncryptedError,
    PDFUnsupportedError,
)
from config import constants
from utils.file_utils import FileUtils

logger = logging.getLogger(__name__)


class PDFValidator:
    """
    Validates PDF files before processing.
    Checks for:
    - Valid PDF structure
    - Encryption
    - Corruption
    - Page count and dimensions
    - Reasonable file characteristics
    """

    def __init__(self):
        """Initialize validator."""
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required for PDF operations")

    def validate(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Perform comprehensive PDF validation.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'reason': str,
                'page_count': int or None,
                'dimensions': list of tuples or None,
                'is_encrypted': bool,
                'has_text_layer': bool or None,
                'file_size_mb': float,
                'warnings': list of warning strings,
            }
        
        Raises:
            PDFValidationError: If validation fails
        """
        result = {
            'valid': True,
            'reason': 'OK',
            'page_count': None,
            'dimensions': None,
            'is_encrypted': False,
            'has_text_layer': False,
            'file_size_mb': 0.0,
            'warnings': [],
        }

        # Check file exists
        if not pdf_path.exists():
            raise PDFValidationError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.is_file():
            raise PDFValidationError(f"Path is not a file: {pdf_path}")
        
        # Check file size
        file_size = FileUtils.get_file_size(pdf_path)
        if file_size < constants.MIN_PDF_FILE_SIZE:
            raise PDFValidationError(f"PDF file is too small: {file_size} bytes")
        
        if file_size > constants.MAX_PDF_FILE_SIZE:
            raise PDFValidationError(
                f"PDF file exceeds maximum size: "
                f"{file_size / (1024*1024):.1f} MB > {constants.MAX_PDF_FILE_SIZE / (1024*1024):.1f} MB"
            )
        
        result['file_size_mb'] = file_size / (1024 * 1024)

        # Try to open PDF
        try:
            pdf_doc = fitz.open(pdf_path)
        except RuntimeError as e:
            if "encrypted" in str(e).lower() or "password" in str(e).lower():
                raise PDFEncryptedError("PDF is encrypted and requires a password")
            else:
                raise PDFCorruptedError(f"Cannot open PDF: {e}")
        except Exception as e:
            raise PDFValidationError(f"Error opening PDF: {e}")

        try:
            # Check encryption
            result['is_encrypted'] = pdf_doc.is_encrypted
            if pdf_doc.is_encrypted:
                raise PDFEncryptedError("PDF is encrypted")

            # Get page count
            page_count = pdf_doc.page_count
            result['page_count'] = page_count
            
            if page_count == 0:
                raise PDFValidationError("PDF has no pages")
            
            if page_count > constants.MAX_PAGES_REASONABLE:
                result['warnings'].append(
                    f"PDF has {page_count} pages (unusual for typical documents)"
                )

            # Inspect pages
            dimensions = []
            has_any_text = False
            problematic_pages = []
            
            for page_num in range(min(10, page_count)):  # Check first 10 pages
                try:
                    page = pdf_doc[page_num]
                    rect = page.rect
                    dimensions.append((rect.width, rect.height))
                    
                    # Check for text
                    if page.get_text().strip():
                        has_any_text = True
                except Exception as e:
                    problematic_pages.append((page_num, str(e)))
            
            # Validate dimensions
            if dimensions:
                for width, height in dimensions:
                    if width < constants.MIN_PAGE_DIMENSION_POINTS:
                        result['warnings'].append(
                            f"Page width ({width} pt) below minimum ({constants.MIN_PAGE_DIMENSION_POINTS} pt)"
                        )
                    if width > constants.MAX_PAGE_DIMENSION_POINTS:
                        result['warnings'].append(
                            f"Page width ({width} pt) above maximum ({constants.MAX_PAGE_DIMENSION_POINTS} pt)"
                        )
                result['dimensions'] = dimensions
            
            # Check text layer
            result['has_text_layer'] = has_any_text
            
            if problematic_pages:
                result['warnings'].append(
                    f"Potential issues with {len(problematic_pages)} page(s): "
                    f"{problematic_pages[:3]}"
                )

        finally:
            pdf_doc.close()

        logger.info(f"PDF validation successful: {pdf_path}")
        logger.info(f"  Pages: {result['page_count']}")
        logger.info(f"  Size: {result['file_size_mb']:.1f} MB")
        logger.info(f"  Has text layer: {result['has_text_layer']}")
        
        if result['warnings']:
            logger.warning(f"  Warnings: {result['warnings']}")

        return result

    def is_valid(self, pdf_path: Path) -> bool:
        """
        Quick check if PDF is valid.
        
        Args:
            pdf_path: Path to PDF
        
        Returns:
            True if valid, False otherwise
        """
        try:
            result = self.validate(pdf_path)
            return result['valid']
        except Exception:
            return False
