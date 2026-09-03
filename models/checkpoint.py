"""
Checkpoint persistence models.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

from .job import JobState
from .page import PageStatus
from .error import ProcessingError


@dataclass
class CheckpointData:
    """
    Checkpoint data for job resumption.
    Contains all information needed to resume a job from where it left off.
    """
    # Checkpoint metadata
    checkpoint_version: str = "1.0"
    created_at: str = ""  # ISO format
    last_updated: str = ""  # ISO format
    
    # Job identification
    job_id: str = ""
    input_pdf_path: str = ""
    input_pdf_hash: str = ""  # SHA256 for validation
    output_pdf_path: str = ""
    
    # Job state
    job_state: str = "running"  # JobState value
    total_pages: int = 0
    processed_pages: int = 0
    
    # Processing configuration
    languages: List[str] = field(default_factory=list)
    enable_preprocessing: bool = True
    enable_optimization: bool = True
    generate_cover_page: bool = False
    
    # Page status tracking
    page_status: Dict[int, str] = field(default_factory=dict)  # page_num -> status
    completed_pages: List[int] = field(default_factory=list)
    failed_pages: List[int] = field(default_factory=list)
    skipped_pages: List[int] = field(default_factory=list)
    
    # Error tracking
    error_log: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    # Processing stage
    current_stage: str = "initialization"  # e.g., 'validation', 'page_processing', 'reconstruction'
    last_completed_page: int = -1
    
    # Temp and intermediate files
    temp_directory: str = ""
    intermediate_pdf_sections: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'CheckpointData':
        """Create from dictionary (JSON)."""
        return cls(**{k: v for k, v in data.items() if k in asdict(cls())})

    def __repr__(self) -> str:
        return (
            f"CheckpointData(job_id={self.job_id}, "
            f"processed={self.processed_pages}/{self.total_pages}, "
            f"stage={self.current_stage})"
        )
