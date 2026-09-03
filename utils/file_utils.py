"""
File operation utilities.
Provides safe, atomic file operations.
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Tuple
import tempfile

from logging_ import get_logger

logger = get_logger(__name__)


class FileUtils:
    """
    Utilities for safe file operations.
    """

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """
        Compute SHA256 hash of a file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Hex digest of SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b''):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def file_exists(file_path: Path) -> bool:
        """
        Check if file exists.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file exists, False otherwise
        """
        return file_path.exists() and file_path.is_file()

    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
        
        Returns:
            File size in bytes, or -1 if error
        """
        try:
            return file_path.stat().st_size
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return -1

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
        
        Returns:
            Formatted string (e.g., "123.4 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def safe_remove(file_path: Path) -> bool:
        """
        Safely remove a file.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if removed, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.warning(f"Error removing file {file_path}: {e}")
            return False

    @staticmethod
    def safe_remove_dir(dir_path: Path) -> bool:
        """
        Safely remove a directory and all contents.
        
        Args:
            dir_path: Path to directory
        
        Returns:
            True if removed, False otherwise
        """
        try:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            return True
        except Exception as e:
            logger.warning(f"Error removing directory {dir_path}: {e}")
            return False

    @staticmethod
    def atomic_write(file_path: Path, content: bytes) -> bool:
        """
        Atomically write content to file using temp file.
        Ensures file is not partially written on failure.
        
        Args:
            file_path: Target file path
            content: Content to write (bytes)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create temp file in same directory (ensures same filesystem)
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent,
                prefix='.tmp_',
                suffix='.tmp'
            )
            try:
                os.write(temp_fd, content)
                os.close(temp_fd)
            except Exception as e:
                os.close(temp_fd)
                os.unlink(temp_path)
                raise e
            
            # Atomic rename (works on Windows and Unix)
            if file_path.exists():
                file_path.unlink()  # Remove target first on Windows
            os.rename(temp_path, file_path)
            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False

    @staticmethod
    def safe_copy(src: Path, dst: Path) -> bool:
        """
        Safely copy a file.
        
        Args:
            src: Source file path
            dst: Destination file path
        
        Returns:
            True if successful, False otherwise
        """
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"Error copying {src} to {dst}: {e}")
            return False

    @staticmethod
    def find_unique_filename(base_path: Path) -> Path:
        """
        Find a unique filename if base_path already exists.
        Appends _1, _2, etc. to stem.
        
        Args:
            base_path: Desired file path
        
        Returns:
            Unique file path
        """
        if not base_path.exists():
            return base_path
        
        counter = 1
        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent
        
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
