"""
Work queue for page processing jobs.
Thread-safe queue for distributing pages to workers.
"""

import logging
import queue
from typing import Optional, List
from threading import Lock

from models import Page, PageStatus
from config import constants
from exceptions import QueueTimeoutError

logger = logging.getLogger(__name__)


class WorkQueue:
    """
    Thread-safe work queue for page processing.
    
    Features:
    - FIFO queue for pending pages
    - Thread-safe operations
    - Timeout support
    - Statistics tracking
    """

    def __init__(self, max_size: int = constants.MAX_QUEUE_SIZE):
        """
        Initialize work queue.
        
        Args:
            max_size: Maximum queue size
        """
        self.queue = queue.Queue(maxsize=max_size)
        self.max_size = max_size
        self.lock = Lock()
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.total_failed = 0

    def enqueue(
        self,
        page: Page,
        timeout_seconds: float = constants.QUEUE_TIMEOUT_SECONDS,
    ) -> bool:
        """
        Add page to queue.
        
        Args:
            page: Page to process
            timeout_seconds: Timeout for queue operation
        
        Returns:
            True if enqueued, False if timeout
        """
        try:
            page.status = PageStatus.PENDING
            self.queue.put(page, timeout=timeout_seconds)
            
            with self.lock:
                self.total_enqueued += 1
            
            logger.debug(f"Page {page.page_num} enqueued")
            return True
        
        except queue.Full:
            logger.warning(f"Queue full, cannot enqueue page {page.page_num}")
            return False
        except Exception as e:
            logger.error(f"Error enqueuing page: {e}")
            return False

    def dequeue(
        self,
        timeout_seconds: float = constants.QUEUE_TIMEOUT_SECONDS,
    ) -> Optional[Page]:
        """
        Get next page from queue.
        
        Args:
            timeout_seconds: Timeout for queue operation
        
        Returns:
            Page object or None if timeout/empty
        """
        try:
            page = self.queue.get(timeout=timeout_seconds)
            
            with self.lock:
                self.total_dequeued += 1
            
            page.status = PageStatus.PROCESSING
            logger.debug(f"Page {page.page_num} dequeued")
            return page
        
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Error dequeuing page: {e}")
            return None

    def enqueue_batch(
        self,
        pages: List[Page],
        timeout_seconds: float = constants.QUEUE_TIMEOUT_SECONDS,
    ) -> int:
        """
        Add multiple pages to queue.
        
        Args:
            pages: List of pages
            timeout_seconds: Timeout per page
        
        Returns:
            Number of successfully enqueued pages
        """
        count = 0
        for page in pages:
            if self.enqueue(page, timeout_seconds):
                count += 1
        return count

    def size(self) -> int:
        """
        Get current queue size.
        
        Returns:
            Number of items in queue
        """
        return self.queue.qsize()

    def is_empty(self) -> bool:
        """
        Check if queue is empty.
        
        Returns:
            True if empty, False otherwise
        """
        return self.queue.empty()

    def get_stats(self) -> dict:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with stats
        """
        with self.lock:
            return {
                'current_size': self.size(),
                'max_size': self.max_size,
                'total_enqueued': self.total_enqueued,
                'total_dequeued': self.total_dequeued,
                'total_failed': self.total_failed,
            }

    def reset_stats(self):
        """
        Reset statistics counters.
        """
        with self.lock:
            self.total_enqueued = 0
            self.total_dequeued = 0
            self.total_failed = 0
            logger.info("Queue statistics reset")
