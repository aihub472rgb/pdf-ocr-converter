"""
Structured logging for the application.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime

from config import constants
from config.paths import get_paths


class ContextFilter(logging.Filter):
    """
    Add contextual information to log records.
    """

    def __init__(self, job_id: Optional[str] = None):
        super().__init__()
        self.job_id = job_id

    def filter(self, record):
        record.job_id = self.job_id or "NONE"
        return True


def get_logger(name: str, job_id: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        job_id: Optional job ID for contextual filtering
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if job_id:
        context_filter = ContextFilter(job_id)
        for handler in logger.handlers:
            handler.addFilter(context_filter)
    
    return logger


def setup_logging(
    log_level: str = constants.LOG_LEVEL_DEFAULT,
    job_id: Optional[str] = None,
    console: bool = True,
    file: bool = True,
) -> Path:
    """
    Set up logging for the application.
    Configures both console and file handlers.
    
    Args:
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        job_id: Optional job ID for job-specific logging
        console: Enable console output
        file: Enable file output
    
    Returns:
        Path to log file if file logging enabled, else None
    """
    paths = get_paths()
    
    # Convert string to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        constants.LOG_FORMAT,
        datefmt=constants.LOG_DATE_FORMAT
    )
    
    # Create context filter
    context_filter = ContextFilter(job_id)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(context_filter)
        root_logger.addHandler(console_handler)
    
    # File handler
    log_file = None
    if file:
        log_file = paths.get_log_file(job_id)
        try:
            paths.ensure_path_exists(log_file, is_file=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(context_filter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}")
    
    return log_file


def get_app_logger() -> logging.Logger:
    """
    Get the main application logger.
    
    Returns:
        Logger instance for application-level logging
    """
    return get_logger('pdf_ocr_converter')
