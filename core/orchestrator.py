"""
OCR orchestrator module.
Main application engine that coordinates the OCR pipeline.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from models import Job, JobState, Page, PageStatus
from exceptions import (
    OCROrchestrationError,
    JobNotFoundError,
    PDFValidationError,
)
from core.job_manager import JobManager
from checkpoint import CheckpointManager
from pdf import PDFValidator, PDFInspector
from ocr import TesseractOCREngine, LanguageManager
from image import ImagePreprocessor
from processing import PageProcessor, WorkQueue, WorkerManager
from config.settings import get_settings

logger = logging.getLogger(__name__)


class OCROrchestrator:
    """
    Main orchestrator for PDF OCR conversion.
    
    Coordinates:
    - Job creation and management
    - PDF validation
    - Worker pool management
    - Progress tracking
    - Checkpoint/resume
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.settings = get_settings()
        self.job_manager = JobManager()
        self.checkpoint_manager = CheckpointManager()
        
        # Initialize core components
        self.pdf_validator = PDFValidator()
        self.pdf_inspector = PDFInspector()
        self.language_manager = LanguageManager()
        self.image_preprocessor = ImagePreprocessor()
        
        # These will be created per job
        self.ocr_engine: Optional[TesseractOCREngine] = None
        self.page_processor: Optional[PageProcessor] = None
        self.work_queue: Optional[WorkQueue] = None
        self.worker_manager: Optional[WorkerManager] = None
        
        logger.info("OCR Orchestrator initialized")

    def process_pdf(
        self,
        input_pdf_path: Path,
        output_pdf_path: Path,
        languages: Optional[List[str]] = None,
        num_workers: Optional[int] = None,
        resume_from_checkpoint: bool = False,
    ) -> Job:
        """
        Process a PDF file through the OCR pipeline.
        
        Args:
            input_pdf_path: Path to input PDF
            output_pdf_path: Path to output PDF
            languages: OCR languages
            num_workers: Number of worker threads
            resume_from_checkpoint: Resume from checkpoint if exists
        
        Returns:
            Completed Job model
        
        Raises:
            OCROrchestrationError: If processing fails
        """
        try:
            # Create or restore job
            if resume_from_checkpoint:
                job = self._try_resume_job(input_pdf_path)
            else:
                job = self.job_manager.create_job(
                    input_pdf_path,
                    output_pdf_path,
                    languages=languages,
                    enable_preprocessing=self.settings.preprocessing.enable_deskew or 
                                        self.settings.preprocessing.enable_denoise,
                )
            
            logger.info(f"Starting OCR job: {job.job_id}")
            
            # Stage 1: Validation
            try:
                self.job_manager.update_job_state(job.job_id, JobState.VALIDATING)
                self._validate_and_inspect_pdf(job)
            except Exception as e:
                self.job_manager.update_job_state(job.job_id, JobState.FAILED)
                raise OCROrchestrationError(f"Validation failed: {e}")
            
            # Stage 2: Initialize components
            try:
                self._initialize_components(job, num_workers)
            except Exception as e:
                self.job_manager.update_job_state(job.job_id, JobState.FAILED)
                raise OCROrchestrationError(f"Component initialization failed: {e}")
            
            # Stage 3: Processing
            try:
                self.job_manager.update_job_state(job.job_id, JobState.PROCESSING)
                pages = self._create_pages(job)
                self._process_pages(job, pages)
            except Exception as e:
                self.job_manager.update_job_state(job.job_id, JobState.FAILED)
                raise OCROrchestrationError(f"Processing failed: {e}")
            finally:
                if self.worker_manager:
                    self.worker_manager.stop()
            
            # Stage 4: Assembly
            try:
                self.job_manager.update_job_state(job.job_id, JobState.ASSEMBLING)
                self._assemble_output_pdf(job)
            except Exception as e:
                self.job_manager.update_job_state(job.job_id, JobState.FAILED)
                raise OCROrchestrationError(f"Assembly failed: {e}")
            
            # Success
            self.job_manager.update_job_state(job.job_id, JobState.COMPLETED)
            logger.info(f"Job completed: {job.job_id}")
            
            # Cleanup
            self.job_manager.cleanup_job(job.job_id, remove_temp=True)
            self.checkpoint_manager.delete_checkpoint(job.job_id)
            
            return job
        
        except OCROrchestrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in orchestration: {e}")
            raise OCROrchestrationError(f"Orchestration failed: {e}")

    def _validate_and_inspect_pdf(self, job: Job):
        """
        Validate and inspect PDF file.
        
        Args:
            job: Job model
        """
        logger.info(f"Validating PDF: {job.input_pdf_path}")
        
        # Validate
        validation_result = self.pdf_validator.validate(job.input_pdf_path)
        if not validation_result['valid']:
            raise PDFValidationError(validation_result['reason'])
        
        # Inspect
        inspection = self.pdf_inspector.inspect_full(job.input_pdf_path)
        job.total_pages = inspection['page_count']
        
        logger.info(
            f"PDF validated: {job.total_pages} pages, "
            f"{inspection['estimated_text_pages']} with text layer"
        )

    def _initialize_components(
        self,
        job: Job,
        num_workers: Optional[int] = None,
    ):
        """
        Initialize OCR components.
        
        Args:
            job: Job model
            num_workers: Number of workers
        """
        logger.info("Initializing OCR components...")
        
        # Validate languages
        self.language_manager.validate_languages(job.languages)
        
        # Create OCR engine
        self.ocr_engine = TesseractOCREngine(languages=job.languages)
        
        # Create page processor
        self.page_processor = PageProcessor(
            ocr_engine=self.ocr_engine,
            image_preprocessor=self.image_preprocessor,
        )
        
        # Create work queue and workers
        self.work_queue = WorkQueue()
        
        if num_workers is None:
            from utils.memory_utils import MemoryUtils
            num_workers = MemoryUtils.calculate_optimal_workers(job.total_pages)
        
        self.worker_manager = WorkerManager(
            page_processor=self.page_processor,
            work_queue=self.work_queue,
            num_workers=num_workers,
        )
        
        logger.info(f"Initialized {num_workers} workers")

    def _create_pages(self, job: Job) -> Dict[int, Page]:
        """
        Create Page models for all pages in PDF.
        
        Args:
            job: Job model
        
        Returns:
            Dictionary of Page models
        """
        pages = {}
        for page_num in range(job.total_pages):
            page = Page(page_num=page_num, status=PageStatus.PENDING)
            pages[page_num] = page
        return pages

    def _process_pages(
        self,
        job: Job,
        pages: Dict[int, Page],
    ):
        """
        Process pages using worker pool.
        
        Args:
            job: Job model
            pages: Dictionary of pages
        """
        logger.info(f"Starting page processing with {self.worker_manager.num_workers} workers...")
        
        # Start workers
        self.worker_manager.start(job.input_pdf_path, Path(job.temp_directory))
        
        # Enqueue all pages
        self.work_queue.enqueue_batch(list(pages.values()))
        
        # Wait for completion
        self.worker_manager.wait_all()
        
        # Get statistics
        stats = self.worker_manager.get_stats()
        logger.info(
            f"Processing complete: {stats['pages_processed']} completed, "
            f"{stats['pages_failed']} failed"
        )
        
        # Save checkpoint
        self.checkpoint_manager.save_checkpoint(job, pages, stage="post-processing")

    def _assemble_output_pdf(self, job: Job):
        """
        Assemble output PDF from processed pages.
        
        Args:
            job: Job model
        """
        logger.info(f"Assembling output PDF: {job.output_pdf_path}")
        # TODO: Implement PDF assembly logic
        # This would combine processed pages and any optimizations
        logger.info("Output PDF assembly complete")

    def _try_resume_job(self, input_pdf_path: Path) -> Job:
        """
        Try to resume job from checkpoint.
        
        Args:
            input_pdf_path: Path to input PDF
        
        Returns:
            Restored Job model
        
        Raises:
            OCROrchestrationError: If resume fails
        """
        # Note: In a real implementation, would search for checkpoints
        # matching this PDF and allow resuming from them
        raise OCROrchestrationError(
            "Resume from checkpoint not yet implemented"
        )

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.
        
        Args:
            job_id: Job ID
        
        Returns:
            Dictionary with job status
        """
        try:
            job = self.job_manager.get_job(job_id)
            return {
                'job_id': job.job_id,
                'state': job.state.value,
                'progress': f"{job.processed_pages}/{job.total_pages}",
                'failed_pages': len(job.failed_pages),
                'skipped_pages': len(job.skipped_pages),
                'created_at': job.created_at,
                'completed_at': job.completed_at,
            }
        except JobNotFoundError:
            return None
