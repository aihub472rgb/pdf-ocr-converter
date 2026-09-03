"""
Worker manager for parallel page processing.
Manages pool of workers processing pages from queue.
"""

import logging
import threading
from typing import List, Optional, Callable, Dict, Any
from pathlib import Path

from models import Page, PageStatus
from exceptions import WorkerError, OCRProcessingError
from processing.work_queue import WorkQueue
from processing.page_processor import PageProcessor
from config import constants

logger = logging.getLogger(__name__)


class WorkerManager:
    """
    Manages pool of worker threads for parallel page processing.
    
    Features:
    - Configurable worker count
    - Thread pool management
    - Error handling and recovery
    - Progress tracking
    """

    def __init__(
        self,
        page_processor: PageProcessor,
        work_queue: WorkQueue,
        num_workers: int = constants.DEFAULT_WORKER_COUNT,
    ):
        """
        Initialize worker manager.
        
        Args:
            page_processor: PageProcessor instance
            work_queue: WorkQueue instance
            num_workers: Number of worker threads
        """
        self.page_processor = page_processor
        self.work_queue = work_queue
        self.num_workers = max(1, min(num_workers, constants.MAX_WORKER_COUNT))
        
        self.workers: List[threading.Thread] = []
        self.running = False
        self.pdf_path: Optional[Path] = None
        self.output_dir: Optional[Path] = None
        
        # Statistics
        self.pages_processed = 0
        self.pages_failed = 0
        self.lock = threading.Lock()
        
        logger.info(f"WorkerManager initialized with {self.num_workers} workers")

    def start(
        self,
        pdf_path: Path,
        output_dir: Path,
    ):
        """
        Start worker threads.
        
        Args:
            pdf_path: Source PDF path
            output_dir: Output directory for processed PDFs
        """
        if self.running:
            logger.warning("Workers already running")
            return
        
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.running = True
        self.pages_processed = 0
        self.pages_failed = 0
        
        # Start worker threads
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"Worker-{i}",
                daemon=False,
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.num_workers} worker threads")

    def stop(self, wait: bool = True):
        """
        Stop worker threads.
        
        Args:
            wait: If True, wait for workers to finish current jobs
        """
        self.running = False
        
        if wait:
            logger.info("Waiting for workers to finish...")
            for worker in self.workers:
                worker.join(timeout=10.0)
        
        self.workers.clear()
        logger.info("Workers stopped")

    def _worker_loop(self):
        """
        Worker thread main loop.
        Processes pages from queue until stopped.
        """
        worker_name = threading.current_thread().name
        logger.info(f"{worker_name} started")
        
        while self.running:
            try:
                # Get next page from queue
                page = self.work_queue.dequeue(timeout_seconds=1.0)
                
                if page is None:
                    # Queue empty, try again
                    continue
                
                # Process page
                logger.info(f"{worker_name} processing page {page.page_num}")
                
                try:
                    output_pdf = self.output_dir / f"page_{page.page_num:05d}.pdf"
                    result = self.page_processor.process_page(
                        self.pdf_path,
                        page.page_num,
                        output_pdf,
                    )
                    
                    if result['success']:
                        page.status = PageStatus.COMPLETED
                        with self.lock:
                            self.pages_processed += 1
                        logger.info(f"{worker_name} completed page {page.page_num}")
                    else:
                        page.status = PageStatus.FAILED
                        page.error_message = result.get('error', 'Unknown error')
                        with self.lock:
                            self.pages_failed += 1
                        logger.error(f"{worker_name} failed page {page.page_num}: {result.get('error')}")
                
                except Exception as e:
                    page.status = PageStatus.FAILED
                    page.error_message = str(e)
                    with self.lock:
                        self.pages_failed += 1
                    logger.error(f"{worker_name} error processing page {page.page_num}: {e}")
            
            except Exception as e:
                logger.error(f"{worker_name} unexpected error: {e}")
        
        logger.info(f"{worker_name} stopped")

    def wait_all(self, timeout: Optional[float] = None):
        """
        Wait for all workers to finish.
        
        Args:
            timeout: Timeout in seconds (None for no timeout)
        """
        for worker in self.workers:
            worker.join(timeout=timeout)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics.
        
        Returns:
            Dictionary with stats
        """
        with self.lock:
            return {
                'running': self.running,
                'num_workers': self.num_workers,
                'pages_processed': self.pages_processed,
                'pages_failed': self.pages_failed,
            }
