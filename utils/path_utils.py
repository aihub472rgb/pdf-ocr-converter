"""
Path management utilities.
"""

from pathlib import Path
from typing import Optional
import os


class PathUtils:
    """
    Utilities for path manipulation.
    """

    @staticmethod
    def ensure_absolute(path: Path) -> Path:
        """
        Ensure path is absolute.
        
        Args:
            path: Path object
        
        Returns:
            Absolute path
        """
        return path.resolve()

    @staticmethod
    def make_relative(path: Path, base: Optional[Path] = None) -> Path:
        """
        Make path relative to base directory.
        
        Args:
            path: Path to make relative
            base: Base directory (default: current directory)
        
        Returns:
            Relative path
        """
        if base is None:
            base = Path.cwd()
        try:
            return path.relative_to(base)
        except ValueError:
            return path

    @staticmethod
    def is_path_safe(path: Path, base_dir: Path) -> bool:
        """
        Check if path is within base_dir (no path traversal).
        
        Args:
            path: Path to check
            base_dir: Base directory
        
        Returns:
            True if path is safe, False otherwise
        """
        try:
            path.resolve().relative_to(base_dir.resolve())
            return True
        except ValueError:
            return False

    @staticmethod
    def get_extension(path: Path) -> str:
        """
        Get file extension (lowercase, without dot).
        
        Args:
            path: File path
        
        Returns:
            Extension (e.g., "pdf", "txt")
        """
        return path.suffix.lstrip('.').lower()

    @staticmethod
    def replace_extension(path: Path, new_extension: str) -> Path:
        """
        Replace file extension.
        
        Args:
            path: File path
            new_extension: New extension (with or without dot)
        
        Returns:
            Path with new extension
        """
        ext = new_extension if new_extension.startswith('.') else f'.{new_extension}'
        return path.with_suffix(ext)

    @staticmethod
    def stem_without_suffix(path: Path) -> str:
        """
        Get filename without any extension.
        Handles multiple dots in filename.
        
        Args:
            path: File path
        
        Returns:
            Filename without extension
        """
        return path.name.split('.')[0]
