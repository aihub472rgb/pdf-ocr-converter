"""
Job management module.
Manages job lifecycle and state.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import uuid

from models import Job, JobState, Page, PageStatus
from exceptions import JobNotFoundError, JobStateError, JobInputError
from config.paths import get_paths
from utils.file_utils import FileUtils

logger = logging.getLogger(__name__)


class JobManager:
    """
    Manages job lifecycle.
    
    Responsibilities:
    - Create and validate jobs
    - Track job state
    - Manage temporary directories
    - Clean up completed jobs
    """

    def __init__(self):
        """Initialize job manager."""
        self.paths = get_paths()
        self.jobs: Dict[str, Job] = {}  # In-memory job cache

    def create_job(
        self,
        input_pdf_path: Path,
        output_pdf_path: Path,
        languages: Optional[List[str]] = None,
        enable_preprocessing: bool = True,
        enable_optimization: bool = True,
        generate_cover_page: bool = False,
    ) -> Job:
        """
        Create a new job.
        
        Args:
            input_pdf_path: Path to input PDF
            output_pdf_path: Path to output PDF
            languages: OCR languages
            enable_preprocessing: Enable image preprocessing
            enable_optimization: Enable PDF optimization
            generate_cover_page: Generate cover page
        
        Returns:
            Created Job model
        
        Raises:
            JobInputError: If input validation fails
        """
        # Validate input
        input_pdf_path = Path(input_pdf_path)
        output_pdf_path = Path(output_pdf_path)
        
        if not input_pdf_path.exists():
            raise JobInputError(f"Input PDF not found: {input_pdf_path}")
        
        if not input_pdf_path.is_file():
            raise JobInputError(f"Input path is not a file: {input_pdf_path}")
        
        if input_pdf_path.suffix.lower() != '.pdf':
            raise JobInputError(f"Input file is not a PDF: {input_pdf_path}")
        
        # Ensure output directory exists
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary directory for this job
        temp_dir = self.paths.create_job_temp_dir()
        
        # Create job
        job = Job(
            job_id=str(uuid.uuid4()),
            input_pdf_path=input_pdf_path,
            output_pdf_path=output_pdf_path,
            state=JobState.CREATED,
            total_pages=0,  # Will be set after validation
            processed_pages=0,
            languages=languages or ['eng'],
            enable_preprocessing=enable_preprocessing,
            enable_optimization=enable_optimization,
            generate_cover_page=generate_cover_page,
            temp_directory=temp_dir,
            created_at=datetime.utcnow().isoformat(),
        )
        
        # Compute PDF hash for validation
        try:
            job.input_pdf_hash = FileUtils.compute_sha256(input_pdf_path)
        except Exception as e:
            logger.warning(f"Could not compute PDF hash: {e}")
        
        # Store in cache
        self.jobs[job.job_id] = job
        
        logger.info(f"Job created: {job.job_id}")
        return job

    def get_job(self, job_id: str) -> Job:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
        
        Returns:
            Job model
        
        Raises:
            JobNotFoundError: If job not found
        """
        if job_id not in self.jobs:
            raise JobNotFoundError(job_id)
        return self.jobs[job_id]

    def update_job_state(
        self,
        job_id: str,
        new_state: JobState,
    ) -> Job:
        """
        Update job state.
        
        Args:
            job_id: Job ID
            new_state: New state
        
        Returns:
            Updated Job model
        
        Raises:
            JobNotFoundError: If job not found
            JobStateError: If state transition invalid
        """
        job = self.get_job(job_id)
        
        # Validate state transition
        if not self._is_valid_state_transition(job.state, new_state):
            raise JobStateError(
                f"Invalid state transition: {job.state.value} -> {new_state.value}"
            )
        
        old_state = job.state
        job.state = new_state
        
        if new_state == JobState.COMPLETED:
            job.completed_at = datetime.utcnow().isoformat()
        elif new_state == JobState.FAILED:
            job.failed_at = datetime.utcnow().isoformat()
        
        logger.info(f"Job {job_id} state: {old_state.value} -> {new_state.value}")
        return job

    def update_job_progress(
        self,
        job_id: str,
        processed_pages: int,
        failed_pages: Optional[List[int]] = None,
        skipped_pages: Optional[List[int]] = None,
    ) -> Job:
        """
        Update job progress.
        
        Args:
            job_id: Job ID
            processed_pages: Number of processed pages
            failed_pages: List of failed page numbers
            skipped_pages: List of skipped page numbers
        
        Returns:
            Updated Job model
        """
        job = self.get_job(job_id)
        job.processed_pages = processed_pages
        
        if failed_pages is not None:
            job.failed_pages = failed_pages
        if skipped_pages is not None:
            job.skipped_pages = skipped_pages
        
        logger.debug(
            f"Job {job_id} progress: {processed_pages}/{job.total_pages} pages"
        )
        return job

    def cleanup_job(
        self,
        job_id: str,
        remove_temp: bool = True,
    ) -> bool:
        """
        Clean up job resources.
        
        Args:
            job_id: Job ID
            remove_temp: If True, remove temporary directory
        
        Returns:
            True if successful, False otherwise
        """
        try:
            job = self.get_job(job_id)
            
            # Remove temporary directory
            if remove_temp and job.temp_directory:
                temp_path = Path(job.temp_directory)
                if temp_path.exists():
                    FileUtils.safe_remove_dir(temp_path)
                    logger.info(f"Removed temp directory: {temp_path}")
            
            # Remove from cache
            del self.jobs[job_id]
            logger.info(f"Job cleaned up: {job_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error cleaning up job {job_id}: {e}")
            return False

    def get_all_jobs(self) -> List[Job]:
        """
        Get all jobs.
        
        Returns:
            List of Job models
        """
        return list(self.jobs.values())

    def get_jobs_by_state(self, state: JobState) -> List[Job]:
        """
        Get jobs by state.
        
        Args:
            state: Job state
        
        Returns:
            List of Job models
        """
        return [job for job in self.jobs.values() if job.state == state]

    @staticmethod
    def _is_valid_state_transition(current: JobState, next_state: JobState) -> bool:
        """
        Validate state transition.
        
        Args:
            current: Current state
            next_state: Next state
        
        Returns:
            True if valid, False otherwise
        """
        # Valid transitions
        valid_transitions = {
            JobState.CREATED: [JobState.VALIDATING, JobState.FAILED],
            JobState.VALIDATING: [JobState.PROCESSING, JobState.FAILED],
            JobState.PROCESSING: [JobState.ASSEMBLING, JobState.FAILED],
            JobState.ASSEMBLING: [JobState.COMPLETED, JobState.FAILED],
            JobState.COMPLETED: [],
            JobState.FAILED: [JobState.CREATED],  # Allow retry
        }
        
        return next_state in valid_transitions.get(current, [])
