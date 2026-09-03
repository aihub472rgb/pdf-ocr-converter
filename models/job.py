"""
Job processing models.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime


class JobState(Enum):
    """Overall job state."""
    INITIALIZED = "initialized"    # Job created, not started
    RUNNING = "running"            # Currently processing
    PAUSED = "paused"              # Paused by user
    COMPLETED = "completed"        # Successfully completed
    FAILED = "failed"              # Failed with unrecoverable error
    INTERRUPTED = "interrupted"    # Interrupted by user or system
    RESUMING = "resuming"          # Resuming from checkpoint


@dataclass
class Job:
    """
    Represents a PDF OCR conversion job.
    """
    job_id: str  # UUID
    input_pdf_path: str
    output_pdf_path: str
    state: JobState = JobState.INITIALIZED
    
    # PDF information
    total_pages: int = 0
    input_pdf_hash: Optional[str] = None  # SHA256 for validation
    input_file_size: int = 0  # Bytes
    
    # Processing progress
    processed_pages: int = 0
    failed_pages: List[int] = field(default_factory=list)
    skipped_pages: List[int] = field(default_factory=list)
    retry_pages: List[int] = field(default_factory=list)
    
    # Configuration
    languages: List[str] = field(default_factory=lambda: ['eng', 'hin'])
    enable_preprocessing: bool = True
    enable_optimization: bool = True
    generate_cover_page: bool = False
    
    # Timing
    created_at: str = ""  # ISO format
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    elapsed_seconds: float = 0.0
    
    # Results
    output_file_size: int = 0  # Bytes
    output_file_created: bool = False
    
    # Error tracking
    last_error: Optional[str] = None
    error_count: int = 0
    
    # Metadata
    temp_directory: Optional[str] = None
    checkpoint_file: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['state'] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Job':
        """Create from dictionary."""
        state_str = data.get('state', 'initialized')
        state = JobState(state_str)
        data['state'] = state
        return cls(**data)

    def get_success_rate(self) -> float:
        """
        Get percentage of successfully processed pages.
        
        Returns:
            Percentage (0.0-100.0)
        """
        if self.total_pages == 0:
            return 0.0
        successfully_processed = self.total_pages - len(self.failed_pages) - len(self.skipped_pages)
        return (successfully_processed / self.total_pages) * 100.0

    def __repr__(self) -> str:
        return f"Job({self.job_id}, {self.state.value}, {self.processed_pages}/{self.total_pages})"
