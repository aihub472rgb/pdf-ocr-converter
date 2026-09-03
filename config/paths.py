"""
Path management for the application.
Handles platform-specific paths and cross-platform compatibility.
"""

import os
import sys
from pathlib import Path
from typing import Optional


class Paths:
    """
    Centralized path management.
    Ensures cross-platform compatibility and consistent directory structure.
    """

    def __init__(self):
        """Initialize paths based on application location."""
        # Root directory (where the app is installed/running from)
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            self.root_dir = Path(sys.executable).parent
        else:
            # Running as Python script
            self.root_dir = Path(__file__).parent.parent

        # Core application directories
        self.config_dir = self.root_dir / "config"
        self.models_dir = self.root_dir / "models"
        self.logging_dir = self.root_dir / "logging_"
        self.exceptions_dir = self.root_dir / "exceptions"
        self.pdf_dir = self.root_dir / "pdf"
        self.ocr_dir = self.root_dir / "ocr"
        self.image_dir = self.root_dir / "image"
        self.processing_dir = self.root_dir / "processing"
        self.checkpoint_dir = self.root_dir / "checkpoint"
        self.job_dir = self.root_dir / "job"
        self.gui_dir = self.root_dir / "gui"
        self.utils_dir = self.root_dir / "utils"
        self.resources_dir = self.root_dir / "resources"
        self.tests_dir = self.root_dir / "tests"

        # Resource directories
        self.tessdata_dir = self.resources_dir / "tessdata"
        self.icons_dir = self.resources_dir / "icons"
        self.templates_dir = self.resources_dir / "templates"

        # User directories
        self.user_home = Path.home()
        self.app_data_dir = self._get_app_data_dir()
        self.app_temp_dir = self._get_app_temp_dir()
        self.app_log_dir = self.app_data_dir / "logs"
        self.app_checkpoint_dir = self.app_data_dir / "checkpoints"

        # Ensure critical directories exist
        self._ensure_directories()

    def _get_app_data_dir(self) -> Path:
        """
        Get platform-specific application data directory.
        Windows: %APPDATA%/PDFOCRConverter
        Linux: ~/.local/share/PDFOCRConverter
        macOS: ~/Library/Application Support/PDFOCRConverter
        """
        if sys.platform == "win32":
            base = Path(os.getenv("APPDATA", self.user_home / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            base = self.user_home / "Library" / "Application Support"
        else:  # Linux and others
            base = Path(os.getenv("XDG_DATA_HOME", self.user_home / ".local" / "share"))

        return base / "PDFOCRConverter"

    def _get_app_temp_dir(self) -> Path:
        """
        Get platform-specific temporary directory for application.
        """
        import tempfile
        base_temp = Path(tempfile.gettempdir())
        return base_temp / "pdf_ocr_converter"

    def _ensure_directories(self):
        """
        Ensure all necessary directories exist.
        Create if missing.
        """
        dirs_to_create = [
            self.app_data_dir,
            self.app_log_dir,
            self.app_checkpoint_dir,
            self.app_temp_dir,
        ]

        for directory in dirs_to_create:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                # Log but don't fail - app can work without some dirs
                print(f"Warning: Could not create directory {directory}: {e}")

    def get_tessdata_path(self, language: str) -> Optional[Path]:
        """
        Get path to Tesseract traineddata file.
        
        Args:
            language: Language code (e.g., 'eng', 'hin')
        
        Returns:
            Path to traineddata file if exists, else None
        """
        traineddata_file = self.tessdata_dir / f"{language}.traineddata"
        if traineddata_file.exists():
            return traineddata_file
        return None

    def get_job_temp_dir(self, job_id: str) -> Path:
        """
        Get temporary directory for a specific job.
        
        Args:
            job_id: Unique job identifier
        
        Returns:
            Path to job-specific temp directory
        """
        return self.app_temp_dir / f"job_{job_id}"

    def get_checkpoint_file(self, job_id: str) -> Path:
        """
        Get checkpoint file path for a job.
        
        Args:
            job_id: Unique job identifier
        
        Returns:
            Path to checkpoint JSON file
        """
        return self.app_checkpoint_dir / f"checkpoint_{job_id}.json"

    def get_log_file(self, job_id: Optional[str] = None) -> Path:
        """
        Get log file path.
        
        Args:
            job_id: Optional job identifier for job-specific log
        
        Returns:
            Path to log file
        """
        if job_id:
            return self.app_log_dir / f"job_{job_id}.log"
        return self.app_log_dir / "app.log"

    def ensure_path_exists(self, path: Path, is_file: bool = False) -> bool:
        """
        Ensure a path exists. Create directories if needed.
        
        Args:
            path: Path to ensure
            is_file: If True, create parent directories only
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if is_file:
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def cleanup_job_temp_dir(self, job_id: str) -> bool:
        """
        Clean up temporary directory for a completed job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if successful, False otherwise
        """
        import shutil
        job_temp_dir = self.get_job_temp_dir(job_id)
        try:
            if job_temp_dir.exists():
                shutil.rmtree(job_temp_dir)
            return True
        except Exception:
            return False


# Global singleton instance
_paths_instance: Optional[Paths] = None


def get_paths() -> Paths:
    """
    Get global Paths instance (singleton).
    
    Returns:
        Paths instance
    """
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = Paths()
    return _paths_instance
