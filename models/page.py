"""
Page processing models.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List


class PageStatus(Enum):
    """Status of page processing."""
    PENDING = "pending"          # Waiting to be processed
    PROCESSING = "processing"    # Currently being processed
    COMPLETED = "completed"      # Successfully processed
    FAILED = "failed"            # Processing failed
    SKIPPED = "skipped"          # Intentionally skipped
    RETRY = "retry"              # Queued for retry


class PageState(Enum):
    """Internal state during page processing."""
    EXTRACTED = "extracted"      # Page image extracted from PDF
    PREPROCESSED = "preprocessed"  # Image preprocessing complete
    OCR_COMPLETE = "ocr_complete"  # OCR processing complete
    TEXT_LAYER_INJECTED = "text_layer_injected"  # Text layer added


@dataclass
class Page:
    """
    Represents a single page in the PDF.
    """
    page_num: int  # 0-indexed
    status: PageStatus = PageStatus.PENDING
    current_state: Optional[PageState] = None
    
    # Processing results
    ocr_text: Optional[str] = None
    ocr_confidence: float = 0.0  # 0.0-1.0
    detected_language: Optional[str] = None
    
    # Intermediate file paths
    temp_image_path: Optional[str] = None
    temp_preprocessed_path: Optional[str] = None
    temp_ocr_result_path: Optional[str] = None
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # Metadata
    page_width_points: Optional[float] = None
    page_height_points: Optional[float] = None
    has_existing_text: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['current_state'] = self.current_state.value if self.current_state else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Page':
        """Create from dictionary."""
        status_str = data.get('status', 'pending')
        status = PageStatus(status_str)
        data['status'] = status
        
        state_str = data.get('current_state')
        data['current_state'] = PageState(state_str) if state_str else None
        
        return cls(**data)

    def __repr__(self) -> str:
        return f"Page({self.page_num}, {self.status.value})"
