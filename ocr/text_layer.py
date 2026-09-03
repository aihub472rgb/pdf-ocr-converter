"""
Text layer injection for PDFs.
Injects OCR-generated text as invisible searchable layer.
"""

from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from exceptions import PDFReconstructionError

logger = logging.getLogger(__name__)


class TextLayerInjector:
    """
    Injects OCR-generated text as invisible text layer in PDF.
    
    Strategy:
    1. Parse HOCR from OCR engine (contains word coordinates)
    2. Create text annotations at word positions
    3. Layer text beneath original page image
    4. Result: Page looks identical but text is selectable/searchable
    """

    def __init__(self):
        """Initialize text layer injector."""
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required")

    def parse_hocr(self, hocr_html: str) -> List[Dict]:
        """
        Parse HOCR HTML to extract word positions and text.
        
        HOCR format contains:
        <span class='ocrx_word' id='word_...' title='bbox x0 y0 x1 y1'>
            word text
        </span>
        
        Args:
            hocr_html: HOCR HTML string from Tesseract
        
        Returns:
            List of dicts with 'text' and 'bbox' (x0, y0, x1, y1)
        """
        words = []
        try:
            root = ET.fromstring(hocr_html)
            # Find all word spans
            for span in root.findall(".//span[@class='ocrx_word']"):
                text = span.text or ""
                title = span.get('title', '')
                
                # Extract bbox from title attribute
                # Format: "bbox x0 y0 x1 y1 ..."
                bbox = self._extract_bbox(title)
                if bbox and text.strip():
                    words.append({
                        'text': text,
                        'bbox': bbox,
                    })
        except Exception as e:
            logger.warning(f"Error parsing HOCR: {e}")
        
        return words

    def _extract_bbox(self, title_str: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Extract bounding box from HOCR title attribute.
        
        Args:
            title_str: Title string (e.g., "bbox 100 200 300 400")
        
        Returns:
            Tuple of (x0, y0, x1, y1) or None if parse error
        """
        try:
            parts = title_str.split()
            if len(parts) >= 5 and parts[0] == 'bbox':
                x0, y0, x1, y1 = map(float, parts[1:5])
                return (x0, y0, x1, y1)
        except (ValueError, IndexError):
            pass
        return None

    def inject_text_layer(
        self,
        pdf_path: Path,
        page_num: int,
        hocr_html: str,
        output_pdf_path: Path,
    ) -> bool:
        """
        Inject text layer into a specific page.
        
        Args:
            pdf_path: Source PDF path
            page_num: 0-indexed page number
            hocr_html: HOCR HTML from OCR
            output_pdf_path: Output PDF path
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse HOCR to extract words and positions
            words = self.parse_hocr(hocr_html)
            
            if not words:
                logger.warning(f"No words extracted from HOCR for page {page_num}")
                return False
            
            # Open PDF and add text layer
            pdf_doc = fitz.open(pdf_path)
            try:
                if page_num >= pdf_doc.page_count:
                    logger.error(f"Invalid page {page_num}")
                    return False
                
                page = pdf_doc[page_num]
                
                # Add text annotations for each word
                for word_info in words:
                    text = word_info['text']
                    bbox = word_info['bbox']
                    
                    # Create text annotation (invisible but searchable)
                    # Use a small font size and transparent color
                    page.insert_textbox(
                        fitz.Rect(bbox),
                        text,
                        fontsize=1,  # Tiny size to stay invisible
                        color=(1, 1, 1),  # White (will be transparent)
                        textbox=True,
                    )
                
                # Save to output
                pdf_doc.save(str(output_pdf_path))
                logger.info(f"Text layer injected for page {page_num}")
                return True
            
            finally:
                pdf_doc.close()
        
        except Exception as e:
            logger.error(f"Error injecting text layer: {e}")
            return False

    def inject_text_layer_via_ocr_pdf(
        self,
        original_page_image,
        ocr_pdf_bytes: bytes,
        output_path: Path,
    ) -> bool:
        """
        Alternative approach: Use Tesseract-generated PDF with text layer.
        
        Args:
            original_page_image: Original page image
            ocr_pdf_bytes: PDF bytes from Tesseract OCR
            output_path: Output path
        
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'wb') as f:
                f.write(ocr_pdf_bytes)
            return True
        except Exception as e:
            logger.error(f"Error writing OCR PDF: {e}")
            return False
