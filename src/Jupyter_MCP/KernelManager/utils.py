"""
Utility functions for kernel management including SHA256-based kernel IDs and persistent storage.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import threading

# Global lock for file operations (cross-process safety not guaranteed, but prevents in-process race conditions)
_file_lock = threading.Lock()


def calculate_kernel_id(notebook_path: str) -> str:
    """
    Calculate a SHA256 hash-based kernel ID from the notebook's absolute path.
    
    Args:
        notebook_path: Path to the notebook file
        
    Returns:
        SHA256 hash of the absolute path as a hexadecimal string
    """
    absolute_path = str(Path(notebook_path).resolve())
    return hashlib.sha256(absolute_path.encode()).hexdigest()


def get_kernel_storage_dir() -> Path:
    """
    Get the cross-platform kernel storage directory.
    
    Returns:
        Path object for the kernel storage directory (~/.jupyter-mcp-kernel/)
    """
    kernel_dir = Path.home() / '.jupyter-mcp-kernel'
    kernel_dir.mkdir(exist_ok=True)
    return kernel_dir


def save_kernel_info(kernel_id: str, kernel_info: Dict[str, Any]) -> None:
    """
    Save kernel information to a JSON file with file locking for thread safety.
    
    Args:
        kernel_id: The SHA256-based kernel ID
        kernel_info: Dictionary containing kernel information
    """
    kernel_dir = get_kernel_storage_dir()
    kernel_file = kernel_dir / f"{kernel_id}.json"
    
    # Add timestamp if not present
    if "last_updated" not in kernel_info:
        kernel_info["last_updated"] = datetime.utcnow().isoformat() + "Z"
    if "created_at" not in kernel_info:
        kernel_info["created_at"] = kernel_info["last_updated"]
    
    # Write with thread-safe file operations
    with _file_lock:
        with open(kernel_file, 'w') as f:
            json.dump(kernel_info, f, indent=2)


def load_kernel_info(kernel_id: str) -> Optional[Dict[str, Any]]:
    """
    Load kernel information from a JSON file with file locking.
    
    Args:
        kernel_id: The SHA256-based kernel ID
        
    Returns:
        Dictionary containing kernel information, or None if file doesn't exist
    """
    kernel_dir = get_kernel_storage_dir()
    kernel_file = kernel_dir / f"{kernel_id}.json"
    
    if not kernel_file.exists():
        return None
    
    try:
        with _file_lock:
            with open(kernel_file, 'r') as f:
                kernel_info = json.load(f)
            return kernel_info
    except (json.JSONDecodeError, IOError) as e:
        # Handle corrupted JSON files
        print(f"Warning: Could not load kernel info for {kernel_id}: {e}")
        return None


def delete_kernel_info(kernel_id: str) -> bool:
    """
    Delete kernel information JSON file.
    
    Args:
        kernel_id: The SHA256-based kernel ID
        
    Returns:
        True if file was deleted, False if it didn't exist
    """
    kernel_dir = get_kernel_storage_dir()
    kernel_file = kernel_dir / f"{kernel_id}.json"
    
    if kernel_file.exists():
        kernel_file.unlink()
        return True
    return False


def cleanup_stale_kernels(max_age_days: int = 2) -> int:
    """
    Clean up kernel files that are older than specified days.
    
    Args:
        max_age_days: Maximum age in days before cleanup
        
    Returns:
        Number of files cleaned up
    """
    kernel_dir = get_kernel_storage_dir()
    cleaned_count = 0
    cutoff_time = datetime.utcnow().timestamp() - (max_age_days * 24 * 3600)
    
    for kernel_file in kernel_dir.glob("*.json"):
        try:
            file_mtime = kernel_file.stat().st_mtime
            if file_mtime < cutoff_time:
                kernel_file.unlink()
                cleaned_count += 1
        except (IOError, OSError) as e:
            print(f"Warning: Could not clean up {kernel_file}: {e}")
    
    return cleaned_count
