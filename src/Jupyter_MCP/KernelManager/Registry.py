###
# Kernel registry to manage a bunch of kernels with persistent storage.
# Uses SHA256-based kernel IDs for cross-platform kernel sharing.
###

from pathlib import Path
from typing import Optional, Dict, Any
from .manager import KernelManager
from .utils import (
    calculate_kernel_id,
    get_kernel_storage_dir,
    save_kernel_info,
    load_kernel_info,
    delete_kernel_info
)


class KernelRegistry:
    """Manages Jupyter kernels with persistent storage and SHA256-based IDs."""

    def __init__(self):
        self.kernels: dict[str, KernelManager] = {}

    def check_existing_kernel(
        self,
        notebook_path: str,
        verify_running: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Check if an existing kernel is available for the given notebook.
        
        Args:
            notebook_path: Path to the notebook file
            verify_running: Probe the kernel and remove stale metadata when the probe fails
            
        Returns:
            Dictionary with kernel info if exists and running, None otherwise
        """
        kernel_id = calculate_kernel_id(notebook_path)
        kernel_info = load_kernel_info(kernel_id)
        
        if kernel_info is None:
            return None
        
        # Check if kernel is marked as running
        if kernel_info.get('status') != 'running':
            return None

        # Status-only callers can inspect persisted metadata without a destructive probe.
        if not verify_running:
            return kernel_info
        
        # Verify kernel is actually running
        if kernel_info.get('connection_info'):
            temp_manager = KernelManager()
            if temp_manager.verify_kernel_running(kernel_info['connection_info']):
                return kernel_info
            else:
                # Kernel is dead, clean up stale info
                delete_kernel_info(kernel_id)
                return None
        
        return None

    def connect_to_kernel(self, notebook_path: str) -> KernelManager:
        """
        Connect to an existing kernel for the given notebook.
        
        Args:
            notebook_path: Path to the notebook file
            
        Returns:
            KernelManager instance connected to the existing kernel
            
        Raises:
            RuntimeError: If no existing kernel is available
        """
        kernel_info = self.check_existing_kernel(notebook_path)
        
        if kernel_info is None:
            raise RuntimeError("No existing kernel available for this notebook")
        
        kernel_id = calculate_kernel_id(notebook_path)
        
        # Check if already in memory
        if kernel_id in self.kernels:
            return self.kernels[kernel_id]
        
        # Create new manager and connect to existing kernel
        manager = KernelManager(custom_kernel_id=kernel_id)
        result = manager.connect_to_existing_kernel(
            kernel_info['connection_info'],
            kernel_info['jupyter_kernel_id']
        )
        
        # Store in memory
        self.kernels[kernel_id] = manager
        
        return manager

    def start_kernel(self, notebook_path: str, kernel_name: str = "python3"):
        """
        Start a kernel for the given notebook, reusing existing if available.
        
        Args:
            notebook_path: Path to the notebook file
            kernel_name: Name of the kernel to start (default: python3)
            
        Returns:
            Dictionary with kernel information
        """
        kernel_id = calculate_kernel_id(notebook_path)
        
        # Check if already in memory
        if kernel_id in self.kernels and self.kernels[kernel_id].is_running:
            return self.kernels[kernel_id].get_kernel_status()
        
        # Check for existing kernel in persistent storage
        existing_kernel = self.check_existing_kernel(notebook_path)
        if existing_kernel:
            try:
                manager = self.connect_to_kernel(notebook_path)
                return manager.get_kernel_status()
            except RuntimeError:
                # Existing kernel is not accessible, clean up and start new
                delete_kernel_info(kernel_id)
        
        # Start new kernel
        manager = KernelManager(custom_kernel_id=kernel_id)
        result = manager.start_kernel(kernel_name=kernel_name)
        
        # Store in memory
        self.kernels[kernel_id] = manager
        
        # Save to persistent storage
        kernel_info = {
            'kernel_id': kernel_id,
            'jupyter_kernel_id': result.get('jupyter_kernel_id'),
            'notebook_path': str(Path(notebook_path).resolve()),
            'kernel_name': kernel_name,
            'status': 'running',
            'connection_info': result.get('connection_info', {})
        }
        save_kernel_info(kernel_id, kernel_info)
        
        return result

    def get_kernel(self, notebook_path: str):
        """
        Get the kernel for the given notebook from memory or persistent storage.
        
        Args:
            notebook_path: Path to the notebook file
            
        Returns:
            KernelManager instance or None if not found
        """
        kernel_id = calculate_kernel_id(notebook_path)
        
        # Check memory first
        if kernel_id in self.kernels:
            return self.kernels[kernel_id]
        
        # Check persistent storage
        existing_kernel = self.check_existing_kernel(notebook_path)
        if existing_kernel:
            try:
                return self.connect_to_kernel(notebook_path)
            except RuntimeError:
                return None
        
        return None

    def stop_kernel(self, notebook_path: str):
        """
        Stop the kernel for the given notebook and clean up persistent storage.
        
        Args:
            notebook_path: Path to the notebook file
            
        Returns:
            Dictionary with stop status
        """
        kernel_id = calculate_kernel_id(notebook_path)
        
        # Stop kernel if in memory
        manager = self.kernels.pop(kernel_id, None)
        
        if manager is not None:
            result = manager.stop_kernel()
        else:
            # Try to stop via persistent storage info
            kernel_info = load_kernel_info(kernel_id)
            if kernel_info:
                result = {
                    'kernel_id': kernel_id,
                    'status': 'stopped'
                }
            else:
                raise RuntimeError("No kernel for notebook")
        
        # Clean up persistent storage
        delete_kernel_info(kernel_id)
        
        return result

    def save_kernel_state(self, notebook_path: str, kernel_info: Dict[str, Any]) -> None:
        """
        Save kernel state to persistent storage.
        
        Args:
            notebook_path: Path to the notebook file
            kernel_info: Dictionary containing kernel information
        """
        kernel_id = calculate_kernel_id(notebook_path)
        save_kernel_info(kernel_id, kernel_info)

    def cleanup_kernel_state(self, notebook_path: str) -> bool:
        """
        Remove kernel state from persistent storage.
        
        Args:
            notebook_path: Path to the notebook file
            
        Returns:
            True if state was removed, False if it didn't exist
        """
        kernel_id = calculate_kernel_id(notebook_path)
        return delete_kernel_info(kernel_id)

    def execute_cell(
        self,
        notebook_path: str,
        notebook_manager: Any,
        cell_id: Optional[str] = None,
        position: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a cell in the notebook using the running kernel and update the notebook file.

        Args:
            notebook_path: Path to the .ipynb file
            notebook_manager: NotebookManager instance
            cell_id: Optional stable ID of the cell to execute
            position: Optional 0-based position index of the cell to execute
            timeout: Optional execution timeout in seconds

        Returns:
            Dictionary containing cell_id, position, status, execution_count, outputs, and any error details
        """
        kernel_id = calculate_kernel_id(notebook_path)
        manager = self.kernels.get(kernel_id)

        if manager is None or not manager.is_running:
            self.start_kernel(notebook_path=notebook_path)
            manager = self.kernels.get(kernel_id)

        # Get cell source from notebook manager either by position or cell_id
        if position is not None:
            cell = notebook_manager.get_cell_by_position(notebook_path, position)
        elif cell_id is not None:
            cell = notebook_manager.get_cell(notebook_path, cell_id)
        else:
            raise ValueError("Either 'position' or 'cell_id' must be specified to execute a cell")

        # Execute code in kernel
        exec_result = manager.execute_code(cell.source, timeout=timeout)

        # Update notebook with outputs and execution count
        notebook_manager.update_cell_output(
            notebook_path=notebook_path,
            cell_id=cell.cell_id,
            outputs=exec_result.get("outputs", []),
            execution_count=exec_result.get("execution_count")
        )

        return {
            "cell_id": cell.cell_id,
            "position": cell.position,
            "status": exec_result.get("status"),
            "execution_count": exec_result.get("execution_count"),
            "outputs": exec_result.get("outputs", []),
            "ename": exec_result.get("ename"),
            "evalue": exec_result.get("evalue"),
            "traceback": exec_result.get("traceback")
        }
