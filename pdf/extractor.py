"""
PDF page extraction module.
Extracts pages from PDF as images without loading entire PDF into RAM.
"""

from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import logging

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from exceptions import PDFExtractionError, ImageQualityError

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extracts pages from PDF as images.
    Designed for memory efficiency:
    - Opens PDF, extracts single page, closes file
    - Returns image as numpy array
    - Does NOT keep entire PDF in memory
    """

    def __init__(self, zoom: float = 2.0, dpi: int = 300):
        """
        Initialize extractor.
        
        Args:
            zoom: Zoom factor for rendering (higher = better quality, more memory)
            dpi: Target DPI (used for quality calculation)
        """
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required")
        
        self.zoom = zoom
        self.dpi = dpi
        self.mat = fitz.Matrix(zoom, zoom)  # Transformation matrix

    def extract_page_image(
        self,
        pdf_path: Path,
        page_num: int,
    ) -> np.ndarray:
        """
        Extract a single page as image without keeping PDF in RAM.
        
        Memory-efficient: Opens PDF, extracts page, closes immediately.
        
        Args:
            pdf_path: Path to PDF file
            page_num: 0-indexed page number
        
        Returns:
            Image as numpy array (RGB, uint8)
        
        Raises:
            PDFExtractionError: If extraction fails
        """
        pdf_doc = None
        try:
            # Open PDF (just file handle)
            pdf_doc = fitz.open(pdf_path)
            
            # Validate page number
            if page_num < 0 or page_num >= pdf_doc.page_count:
                raise PDFExtractionError(
                    f"Invalid page number {page_num} (PDF has {pdf_doc.page_count} pages)",
                    page_num
                )
            
            # Extract page
            page = pdf_doc[page_num]
            
            # Render to image (pixmap)
            pix = page.get_pixmap(mat=self.mat, alpha=False)
            
            # Convert to numpy array
            image_array = np.frombuffer(pix.samples, dtype=np.uint8)
            image_array = image_array.reshape(pix.height, pix.width, 3)
            
            logger.debug(f"Extracted page {page_num}: {image_array.shape}")
            
            return image_array
        
        except PDFExtractionError:
            raise
        except Exception as e:
            raise PDFExtractionError(
                f"Error extracting page: {e}",
                page_num
            )
        finally:
            # Ensure PDF is closed
            if pdf_doc is not None:
                pdf_doc.close()

    def extract_page_image_grayscale(
        self,
        pdf_path: Path,
        page_num: int,
    ) -> np.ndarray:
        """
        Extract page as grayscale image.
        
        Args:
            pdf_path: Path to PDF file
            page_num: 0-indexed page number
        
        Returns:
            Grayscale image as numpy array (uint8)
        """
        # Extract as RGB then convert to grayscale
        rgb_image = self.extract_page_image(pdf_path, page_num)
        
        # Convert RGB to grayscale using standard formula
        gray_image = (
            0.299 * rgb_image[:, :, 0] +
            0.587 * rgb_image[:, :, 1] +
            0.114 * rgb_image[:, :, 2]
        ).astype(np.uint8)
        
        return gray_image

    def extract_pages_batch(
        self,
        pdf_path: Path,
        page_nums: list,
        grayscale: bool = False,
    ) -> dict:
        """
        Extract multiple pages sequentially.
        
        Args:
            pdf_path: Path to PDF file
            page_nums: List of page numbers to extract
            grayscale: If True, return grayscale images
        
        Returns:
            Dictionary mapping page_num -> image_array
        """
        images = {}
        for page_num in page_nums:
            try:
                if grayscale:
                    image = self.extract_page_image_grayscale(pdf_path, page_num)
                else:
                    image = self.extract_page_image(pdf_path, page_num)
                images[page_num] = image
            except Exception as e:
                logger.error(f"Error extracting page {page_num}: {e}")
                images[page_num] = None
        
        return images

    def get_page_dimensions(
        self,
        pdf_path: Path,
        page_num: int,
    ) -> Tuple[float, float]:
        """
        Get original page dimensions (before zoom).
        
        Args:
            pdf_path: Path to PDF file
            page_num: 0-indexed page number
        
        Returns:
            Tuple of (width, height) in points
        """
        pdf_doc = None
        try:
            pdf_doc = fitz.open(pdf_path)
            page = pdf_doc[page_num]
            rect = page.rect
            return rect.width, rect.height
        finally:
            if pdf_doc is not None:
                pdf_doc.close()
