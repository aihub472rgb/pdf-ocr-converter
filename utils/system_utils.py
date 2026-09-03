"""
System utility functions.
Provides platform-specific and system-level utilities.
"""

import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SystemUtils:
    """
    Platform and system-level utilities.
    """

    @staticmethod
    def get_platform() -> str:
        """
        Get current platform.
        
        Returns:
            'windows', 'linux', 'darwin', or 'unknown'
        """
        system = platform.system().lower()
        if 'windows' in system:
            return 'windows'
        elif 'linux' in system:
            return 'linux'
        elif 'darwin' in system:
            return 'darwin'
        return 'unknown'

    @staticmethod
    def is_frozen() -> bool:
        """
        Check if running as PyInstaller frozen executable.
        
        Returns:
            True if frozen, False otherwise
        """
        return getattr(sys, 'frozen', False)

    @staticmethod
    def get_application_path() -> Path:
        """
        Get application root path.
        
        Returns:
            Path to application directory
        """
        if SystemUtils.is_frozen():
            return Path(sys.executable).parent
        return Path(__file__).parent.parent

    @staticmethod
    def run_command(
        command: list,
        timeout: Optional[int] = None,
        capture_output: bool = True
    ) -> Tuple[int, str, str]:
        """
        Run a system command.
        
        Args:
            command: Command as list (e.g., ['python', '--version'])
            timeout: Timeout in seconds
            capture_output: If True, capture stdout/stderr
        
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    @staticmethod
    def open_file_explorer(path: Path) -> bool:
        """
        Open file explorer at path.
        Platform-specific behavior.
        
        Args:
            path: Path to open
        
        Returns:
            True if successful, False otherwise
        """
        try:
            platform_name = SystemUtils.get_platform()
            if platform_name == 'windows':
                subprocess.Popen(['explorer', str(path)])
            elif platform_name == 'darwin':
                subprocess.Popen(['open', str(path)])
            elif platform_name == 'linux':
                subprocess.Popen(['xdg-open', str(path)])
            else:
                return False
            return True
        except Exception as e:
            logger.error(f"Error opening file explorer: {e}")
            return False

    @staticmethod
    def get_python_version() -> str:
        """
        Get Python version string.
        
        Returns:
            Version string (e.g., "3.9.7")
        """
        return platform.python_version()

    @staticmethod
    def get_system_info() -> dict:
        """
        Get system information.
        
        Returns:
            Dictionary with system info
        """
        return {
            'platform': SystemUtils.get_platform(),
            'platform_version': platform.platform(),
            'python_version': SystemUtils.get_python_version(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
        }
