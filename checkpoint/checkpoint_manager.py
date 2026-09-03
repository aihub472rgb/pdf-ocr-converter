"""
Checkpoint management for job resumption.
Allows pausing and resuming OCR jobs.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib

from models import Job, JobState, CheckpointData, Page, PageStatus
from exceptions import (
    CheckpointError,
    CheckpointInvalidError,
    CheckpointNotFoundError,
)
from config.paths import get_paths
from config import constants

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages checkpoint data for job resumption.
    
    Responsibilities:
    - Save checkpoint data to disk
    - Load checkpoint data
    - Validate checkpoint integrity
    - Manage checkpoint lifecycle
    """

    def __init__(self):
        """Initialize checkpoint manager."""
        self.paths = get_paths()

    def save_checkpoint(
        self,
        job: Job,
        pages: Dict[int, Page],
        stage: str = "processing",
    ) -> Path:
        """
        Save checkpoint for a job.
        
        Args:
            job: Job model
            pages: Dictionary of pages by page_num
            stage: Current processing stage
        
        Returns:
            Path to checkpoint file
        
        Raises:
            CheckpointError: If save fails
        """
        try:
            # Create checkpoint data
            checkpoint = CheckpointData(
                checkpoint_version=constants.CHECKPOINT_VERSION,
                created_at=datetime.utcnow().isoformat(),
                last_updated=datetime.utcnow().isoformat(),
                job_id=job.job_id,
                input_pdf_path=str(job.input_pdf_path),
                input_pdf_hash=job.input_pdf_hash or "",
                output_pdf_path=str(job.output_pdf_path),
                job_state=job.state.value,
                total_pages=job.total_pages,
                processed_pages=job.processed_pages,
                languages=job.languages,
                enable_preprocessing=job.enable_preprocessing,
                enable_optimization=job.enable_optimization,
                generate_cover_page=job.generate_cover_page,
                current_stage=stage,
                temp_directory=job.temp_directory or "",
            )
            
            # Track page status
            for page_num, page in pages.items():
                checkpoint.page_status[page_num] = page.status.value
                
                if page.status == PageStatus.COMPLETED:
                    checkpoint.completed_pages.append(page_num)
                elif page.status == PageStatus.FAILED:
                    checkpoint.failed_pages.append(page_num)
                elif page.status == PageStatus.SKIPPED:
                    checkpoint.skipped_pages.append(page_num)
                
                if page.error_message:
                    checkpoint.error_log[page_num] = {
                        'error': page.error_message,
                        'retry_count': page.retry_count,
                    }
            
            # Save to disk
            checkpoint_path = self.paths.get_checkpoint_file(job.job_id)
            self.paths.ensure_path_exists(checkpoint_path, is_file=True)
            
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Checkpoint saved: {checkpoint_path}")
            return checkpoint_path
        
        except Exception as e:
            raise CheckpointError(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self, job_id: str) -> CheckpointData:
        """
        Load checkpoint for a job.
        
        Args:
            job_id: Job ID
        
        Returns:
            CheckpointData object
        
        Raises:
            CheckpointNotFoundError: If checkpoint doesn't exist
            CheckpointInvalidError: If checkpoint is corrupted
        """
        checkpoint_path = self.paths.get_checkpoint_file(job_id)
        
        if not checkpoint_path.exists():
            raise CheckpointNotFoundError(job_id)
        
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate checkpoint version
            version = data.get('checkpoint_version')
            if version != constants.CHECKPOINT_VERSION:
                logger.warning(f"Checkpoint version mismatch: {version} != {constants.CHECKPOINT_VERSION}")
            
            checkpoint = CheckpointData.from_dict(data)
            logger.info(f"Checkpoint loaded: {checkpoint_path}")
            return checkpoint
        
        except json.JSONDecodeError as e:
            raise CheckpointInvalidError(f"Corrupted checkpoint file: {e}")
        except Exception as e:
            raise CheckpointInvalidError(f"Error loading checkpoint: {e}")

    def restore_job_from_checkpoint(
        self,
        checkpoint: CheckpointData,
    ) -> Job:
        """
        Restore Job model from checkpoint.
        
        Args:
            checkpoint: CheckpointData object
        
        Returns:
            Restored Job model
        """
        job = Job(
            job_id=checkpoint.job_id,
            input_pdf_path=checkpoint.input_pdf_path,
            output_pdf_path=checkpoint.output_pdf_path,
            state=JobState(checkpoint.job_state),
            total_pages=checkpoint.total_pages,
            processed_pages=checkpoint.processed_pages,
            input_pdf_hash=checkpoint.input_pdf_hash or None,
            languages=checkpoint.languages,
            enable_preprocessing=checkpoint.enable_preprocessing,
            enable_optimization=checkpoint.enable_optimization,
            generate_cover_page=checkpoint.generate_cover_page,
            failed_pages=checkpoint.failed_pages.copy(),
            skipped_pages=checkpoint.skipped_pages.copy(),
            temp_directory=checkpoint.temp_directory or None,
            checkpoint_file=str(self.paths.get_checkpoint_file(checkpoint.job_id)),
        )
        
        return job

    def restore_pages_from_checkpoint(
        self,
        checkpoint: CheckpointData,
    ) -> Dict[int, Page]:
        """
        Restore Page models from checkpoint.
        
        Args:
            checkpoint: CheckpointData object
        
        Returns:
            Dictionary of Page models by page_num
        """
        pages = {}
        
        for page_num in range(checkpoint.total_pages):
            # Get status from checkpoint
            status_str = checkpoint.page_status.get(str(page_num), 'pending')
            try:
                status = PageStatus(status_str)
            except ValueError:
                status = PageStatus.PENDING
            
            # Create page
            page = Page(
                page_num=page_num,
                status=status,
            )
            
            # Restore error info if exists
            if page_num in checkpoint.error_log:
                error_info = checkpoint.error_log[page_num]
                page.error_message = error_info.get('error')
                page.retry_count = error_info.get('retry_count', 0)
            
            pages[page_num] = page
        
        return pages

    def delete_checkpoint(self, job_id: str) -> bool:
        """
        Delete checkpoint file.
        
        Args:
            job_id: Job ID
        
        Returns:
            True if deleted, False otherwise
        """
        checkpoint_path = self.paths.get_checkpoint_file(job_id)
        try:
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                logger.info(f"Checkpoint deleted: {checkpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting checkpoint: {e}")
            return False

    def checkpoint_exists(self, job_id: str) -> bool:
        """
        Check if checkpoint exists for job.
        
        Args:
            job_id: Job ID
        
        Returns:
            True if checkpoint exists, False otherwise
        """
        checkpoint_path = self.paths.get_checkpoint_file(job_id)
        return checkpoint_path.exists()

    def validate_checkpoint(
        self,
        checkpoint: CheckpointData,
        input_pdf_path: Path,
    ) -> bool:
        """
        Validate that checkpoint matches the PDF file.
        
        Args:
            checkpoint: CheckpointData object
            input_pdf_path: Path to input PDF
        
        Returns:
            True if valid, False otherwise
        """
        # Check paths match
        if checkpoint.input_pdf_path != str(input_pdf_path):
            logger.warning(
                f"PDF path mismatch: {checkpoint.input_pdf_path} != {input_pdf_path}"
            )
            return False
        
        # Check PDF still exists
        if not Path(checkpoint.input_pdf_path).exists():
            logger.warning(f"PDF no longer exists: {checkpoint.input_pdf_path}")
            return False
        
        # Optionally validate hash if available
        if checkpoint.input_pdf_hash:
            # Could compute hash and compare, but expensive
            logger.debug("PDF hash validation skipped")
        
        return True

    def get_checkpoint_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint information without full restore.
        
        Args:
            job_id: Job ID
        
        Returns:
            Dictionary with checkpoint info or None if not found
        """
        try:
            checkpoint = self.load_checkpoint(job_id)
            return {
                'job_id': checkpoint.job_id,
                'state': checkpoint.job_state,
                'progress': f"{checkpoint.processed_pages}/{checkpoint.total_pages}",
                'stage': checkpoint.current_stage,
                'created_at': checkpoint.created_at,
                'last_updated': checkpoint.last_updated,
            }
        except CheckpointNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting checkpoint info: {e}")
            return None
