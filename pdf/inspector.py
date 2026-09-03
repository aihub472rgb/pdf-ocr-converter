"""
PDF inspection module.
Extracts metadata and information from PDFs.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from exceptions import PDFExtractionError

logger = logging.getLogger(__name__)


class PDFInspector:
    """
    Inspects PDF files and extracts metadata.
    Provides information about:
    - Page dimensions
    - Page count
    - Metadata (title, author, subject, etc.)
    - Text layer presence
    - Image-based vs text-based pages
    """

    def __init__(self):
        """Initialize inspector."""
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required")

    def get_page_count(self, pdf_path: Path) -> int:
        """
        Get total page count.
        
        Args:
            pdf_path: Path to PDF
        
        Returns:
            Number of pages
        """
        pdf_doc = fitz.open(pdf_path)
        try:
            return pdf_doc.page_count
        finally:
            pdf_doc.close()

    def get_page_dimensions(self, pdf_path: Path, page_num: int) -> Tuple[float, float]:
        """
        Get dimensions of a specific page.
        
        Args:
            pdf_path: Path to PDF
            page_num: 0-indexed page number
        
        Returns:
            Tuple of (width, height) in points
        """
        pdf_doc = fitz.open(pdf_path)
        try:
            page = pdf_doc[page_num]
            rect = page.rect
            return rect.width, rect.height
        finally:
            pdf_doc.close()

    def get_all_dimensions(self, pdf_path: Path) -> List[Tuple[float, float]]:
        """
        Get dimensions of all pages.
        
        Args:
            pdf_path: Path to PDF
        
        Returns:
            List of (width, height) tuples
        """
        pdf_doc = fitz.open(pdf_path)
        try:
            dimensions = []
            for page in pdf_doc:
                rect = page.rect
                dimensions.append((rect.width, rect.height))
            return dimensions
        finally:
            pdf_doc.close()

    def get_metadata(self, pdf_path: Path) -> Dict[str, Optional[str]]:
        """
        Extract PDF metadata.
        
        Args:
            pdf_path: Path to PDF
        
        Returns:
            Dictionary of metadata fields
        """
        pdf_doc = fitz.open(pdf_path)
        try:
            raw_metadata = pdf_doc.metadata
            
            # Normalize metadata keys
            metadata = {
                'title': raw_metadata.get('title'),
                'author': raw_metadata.get('author'),
                'subject': raw_metadata.get('subject'),
                'keywords': raw_metadata.get('keywords'),
                'creator': raw_metadata.get('creator'),
                'producer': raw_metadata.get('producer'),
                'creation_date': raw_metadata.get('creationDate'),
                'modification_date': raw_metadata.get('modDate'),
            }
            
            return metadata
        finally:
            pdf_doc.close()

    def has_text_layer(self, pdf_path: Path, sample_pages: int = 5) -> bool:
        """
        Check if PDF has searchable text layer.
        Samples first N pages to determine.
        
        Args:
            pdf_path: Path to PDF
            sample_pages: Number of pages to sample
        
        Returns:
            True if text layer detected, False otherwise
        """
        pdf_doc = fitz.open(pdf_path)
        try:
            page_count = pdf_doc.page_count
            sample_count = min(sample_pages, page_count)
            
            for page_num in range(sample_count):
                page = pdf_doc[page_num]
                text = page.get_text().strip()
                if text:  # Found some text
                    logger.info(f"Text layer detected on page {page_num}")
                    return True
            
            logger.info("No text layer detected in sampled pages")
            return False
        finally:
            pdf_doc.close()

    def get_page_text(self, pdf_path: Path, page_num: int) -> str:
        """
        Extract text from a page (if it has text layer).
        
        Args:
            pdf_path: Path to PDF
            page_num: 0-indexed page number
        
        Returns:
            Extracted text
        """
        pdf_doc = fitz.open(pdf_path)
        try:
            page = pdf_doc[page_num]
            return page.get_text()
        finally:
            pdf_doc.close()

    def get_page_images(self, pdf_path: Path, page_num: int) -> List[int]:
        """
        Get list of image XObject IDs on a page.
        
        Args:
            pdf_path: Path to PDF
            page_num: 0-indexed page number
        
        Returns:
            List of image XObject numbers
        """
        pdf_doc = fitz.open(pdf_path)
        try:
            page = pdf_doc[page_num]
            image_list = page.get_images()
            return image_list if image_list else []
        finally:
            pdf_doc.close()

    def inspect_full(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Perform full inspection of PDF.
        
        Args:
            pdf_path: Path to PDF
        
        Returns:
            Dictionary with complete inspection results
        """
        pdf_doc = fitz.open(pdf_path)
        try:
            page_count = pdf_doc.page_count
            metadata = pdf_doc.metadata
            
            # Sample pages for characteristics
            sample_pages = min(10, page_count)
            text_pages = 0
            image_pages = 0
            
            for page_num in range(sample_pages):
                page = pdf_doc[page_num]
                if page.get_text().strip():
                    text_pages += 1
                if page.get_images():
                    image_pages += 1
            
            return {
                'page_count': page_count,
                'metadata': metadata,
                'estimated_text_pages': text_pages,
                'estimated_image_pages': image_pages,
                'sample_size': sample_pages,
            }
        finally:
            pdf_doc.close()
