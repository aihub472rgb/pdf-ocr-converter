"""
Memory and resource monitoring utilities.
"""

import psutil
from typing import Dict
import logging

from config import constants

logger = logging.getLogger(__name__)


class MemoryUtils:
    """
    Utilities for memory and resource monitoring.
    """

    @staticmethod
    def get_available_ram_mb() -> float:
        """
        Get available system RAM in MB.
        
        Returns:
            Available RAM in MB
        """
        try:
            return psutil.virtual_memory().available / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error getting available RAM: {e}")
            return 0.0

    @staticmethod
    def get_total_ram_mb() -> float:
        """
        Get total system RAM in MB.
        
        Returns:
            Total RAM in MB
        """
        try:
            return psutil.virtual_memory().total / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error getting total RAM: {e}")
            return 0.0

    @staticmethod
    def get_used_ram_mb() -> float:
        """
        Get used system RAM in MB.
        
        Returns:
            Used RAM in MB
        """
        try:
            return psutil.virtual_memory().used / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error getting used RAM: {e}")
            return 0.0

    @staticmethod
    def get_available_disk_mb(path: str = '/') -> float:
        """
        Get available disk space in MB.
        
        Args:
            path: Path to check (default: root)
        
        Returns:
            Available disk space in MB
        """
        try:
            return psutil.disk_usage(path).free / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error getting available disk: {e}")
            return 0.0

    @staticmethod
    def get_cpu_count(logical: bool = True) -> int:
        """
        Get CPU core count.
        
        Args:
            logical: If True, count logical cores; else physical cores
        
        Returns:
            Core count
        """
        try:
            return psutil.cpu_count(logical=logical) or 1
        except Exception:
            return 1

    @staticmethod
    def calculate_optimal_workers(total_pages: int) -> int:
        """
        Calculate optimal number of workers based on system resources.
        
        Args:
            total_pages: Total pages to process
        
        Returns:
            Recommended worker count
        """
        available_ram_mb = MemoryUtils.get_available_ram_mb()
        cpu_cores = MemoryUtils.get_cpu_count(logical=True)
        
        # Conservative estimate: 200 MB per worker
        max_workers_by_ram = max(1, int(available_ram_mb / 200))
        
        # Use half the CPU cores, but at least 1
        max_workers_by_cpu = max(1, cpu_cores // 2)
        
        # Take minimum
        optimal = min(max_workers_by_ram, max_workers_by_cpu)
        
        # Respect limits
        optimal = max(constants.MIN_WORKER_COUNT, optimal)
        optimal = min(constants.MAX_WORKER_COUNT, optimal)
        
        return optimal

    @staticmethod
    def check_memory_available(required_mb: float) -> bool:
        """
        Check if required memory is available.
        
        Args:
            required_mb: Required memory in MB
        
        Returns:
            True if memory available, False otherwise
        """
        available = MemoryUtils.get_available_ram_mb()
        return available >= required_mb

    @staticmethod
    def check_disk_available(required_mb: float, path: str = '/') -> bool:
        """
        Check if required disk space is available.
        
        Args:
            required_mb: Required disk space in MB
            path: Path to check
        
        Returns:
            True if space available, False otherwise
        """
        available = MemoryUtils.get_available_disk_mb(path)
        return available >= required_mb

    @staticmethod
    def get_resource_status() -> Dict[str, float]:
        """
        Get current resource status.
        
        Returns:
            Dictionary with resource metrics
        """
        return {
            'available_ram_mb': MemoryUtils.get_available_ram_mb(),
            'total_ram_mb': MemoryUtils.get_total_ram_mb(),
            'used_ram_mb': MemoryUtils.get_used_ram_mb(),
            'available_disk_mb': MemoryUtils.get_available_disk_mb(),
            'cpu_count': MemoryUtils.get_cpu_count(),
        }
