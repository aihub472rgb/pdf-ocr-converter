"""
Page processing pipeline.
OCRs a single page from extraction to text layer injection.
"""

import logging
from typing import Optional, Dict, Any
import numpy as np
from pathlib import Path

from models import Page, PageStatus, PageState
from exceptions import OCRProcessingError, ImageProcessingError
from pdf import PDFExtractor
from image import ImagePreprocessor
from ocr import TesseractOCREngine, TextLayerInjector
from config.settings import get_settings

logger = logging.getLogger(__name__)


class PageProcessor:
    """
    Processes a single PDF page through the OCR pipeline.
    
    Pipeline stages:
    1. Extract page image from PDF
    2. Preprocess image (deskew, denoise, etc.)
    3. Run OCR to extract text
    4. Inject text layer back into PDF
    """

    def __init__(
        self,
        ocr_engine: TesseractOCREngine,
        pdf_extractor: Optional[PDFExtractor] = None,
        image_preprocessor: Optional[ImagePreprocessor] = None,
        text_layer_injector: Optional[TextLayerInjector] = None,
    ):
        """
        Initialize page processor.
        
        Args:
            ocr_engine: OCR engine instance
            pdf_extractor: PDF extractor (created if None)
            image_preprocessor: Image preprocessor (created if None)
            text_layer_injector: Text layer injector (created if None)
        """
        self.ocr_engine = ocr_engine
        self.pdf_extractor = pdf_extractor or PDFExtractor()
        self.image_preprocessor = image_preprocessor or ImagePreprocessor()
        self.text_layer_injector = text_layer_injector or TextLayerInjector()
        self.settings = get_settings()

    def process_page(
        self,
        pdf_path: Path,
        page_num: int,
        output_pdf_path: Path,
    ) -> Dict[str, Any]:
        """
        Process a single page through complete OCR pipeline.
        
        Args:
            pdf_path: Source PDF path
            page_num: 0-indexed page number
            output_pdf_path: Output PDF path
        
        Returns:
            Dictionary with processing results:
            {
                'success': bool,
                'page_num': int,
                'ocr_text': str or None,
                'confidence': float,
                'error': str or None,
            }
        """
        result = {
            'success': False,
            'page_num': page_num,
            'ocr_text': None,
            'confidence': 0.0,
            'error': None,
        }

        try:
            # Stage 1: Extract page image
            logger.info(f"Extracting page {page_num}...")
            page_image = self.pdf_extractor.extract_page_image(pdf_path, page_num)
            logger.debug(f"Extracted: {page_image.shape}")

            # Stage 2: Preprocess image
            logger.info(f"Preprocessing page {page_num}...")
            if self.settings.preprocessing.enable_deskew or self.settings.preprocessing.enable_denoise:
                page_image = self.image_preprocessor.preprocess(
                    page_image,
                    config=self.settings.preprocessing,
                )
                logger.debug(f"Preprocessed: {page_image.shape}")

            # Stage 3: Run OCR
            logger.info(f"Running OCR on page {page_num}...")
            ocr_result = self.ocr_engine.ocr_image(page_image)
            
            result['ocr_text'] = ocr_result['text']
            result['confidence'] = ocr_result['confidence']
            logger.info(f"OCR complete: confidence={result['confidence']:.2%}")

            # Stage 4: Inject text layer
            logger.info(f"Injecting text layer into page {page_num}...")
            success = self.text_layer_injector.inject_text_layer(
                pdf_path,
                page_num,
                ocr_result['hocr'],
                output_pdf_path,
            )
            
            if not success:
                logger.warning(f"Text layer injection failed for page {page_num}")
            
            result['success'] = True
            logger.info(f"Page {page_num} processed successfully")
        
        except OCRProcessingError as e:
            result['error'] = str(e)
            logger.error(f"OCR error on page {page_num}: {e}")
        except ImageProcessingError as e:
            result['error'] = str(e)
            logger.error(f"Image processing error on page {page_num}: {e}")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Unexpected error processing page {page_num}: {e}")

        return result

    def process_page_to_page_object(
        self,
        page: Page,
        pdf_path: Path,
    ) -> Page:
        """
        Process page and update Page model object.
        
        Args:
            page: Page model to update
            pdf_path: Source PDF path
        
        Returns:
            Updated Page model
        """
        try:
            page.status = PageStatus.PROCESSING
            
            # Extract image
            page_image = self.pdf_extractor.extract_page_image(pdf_path, page.page_num)
            page.current_state = PageState.EXTRACTED
            
            # Preprocess
            if self.settings.preprocessing.enable_deskew or self.settings.preprocessing.enable_denoise:
                page_image = self.image_preprocessor.preprocess(page_image)
            page.current_state = PageState.PREPROCESSED
            
            # OCR
            ocr_result = self.ocr_engine.ocr_image(page_image)
            page.ocr_text = ocr_result['text']
            page.ocr_confidence = ocr_result['confidence']
            page.current_state = PageState.OCR_COMPLETE
            
            # Get page dimensions
            width, height = self.pdf_extractor.get_page_dimensions(pdf_path, page.page_num)
            page.page_width_points = width
            page.page_height_points = height
            
            page.status = PageStatus.COMPLETED
            
        except Exception as e:
            page.status = PageStatus.FAILED
            page.error_message = str(e)
            page.retry_count += 1
            logger.error(f"Error processing page {page.page_num}: {e}")
        
        return page
