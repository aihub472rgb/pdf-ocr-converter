"""
Error reporting models.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"        # Informational, not a failure
    WARNING = "warning"  # Warning, may continue
    ERROR = "error"      # Error, page skipped
    CRITICAL = "critical"  # Critical, job may fail


@dataclass
class ProcessingError:
    """
    Represents a processing error.
    """
    page_num: Optional[int]  # None for non-page errors
    error_message: str
    error_code: str
    severity: ErrorSeverity
    timestamp: str  # ISO format
    retry_count: int = 0
    recoverable: bool = True
    details: dict = field(default_factory=dict)  # Additional context

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessingError':
        """Create from dictionary."""
        severity_str = data.get('severity', 'error')
        severity = ErrorSeverity(severity_str)
        data['severity'] = severity
        return cls(**data)

    def __str__(self) -> str:
        """String representation."""
        if self.page_num is not None:
            return f"Page {self.page_num}: [{self.error_code}] {self.error_message}"
        return f"[{self.error_code}] {self.error_message}"
