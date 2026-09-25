###
# Kernel registry to manage a bunch of kernels. this is one per notebook
###

from pathlib import Path
from typing import Optional, Dict, Any
from .manager import KernelManager

class KernelRegistry:

    def __init__(self):
        self.kernels: dict[str, KernelManager] = {}

    def start_kernel(self, notebook_path: str, kernel_name: str = "python3"):
        path = str(Path(notebook_path).resolve())

        if path in self.kernels:
            raise RuntimeError("Kernel already exists for notebook")

        manager = KernelManager()
        result = manager.start_kernel(kernel_name=kernel_name)

        self.kernels[path] = manager
        return result

    def get_kernel(self, notebook_path: str):
        path = str(Path(notebook_path).resolve())
        return self.kernels.get(path)

    def stop_kernel(self, notebook_path: str):
        path = str(Path(notebook_path).resolve())

        manager = self.kernels.pop(path, None)

        if manager is None:
            raise RuntimeError("No kernel for notebook")

        return manager.stop_kernel()

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
        path = str(Path(notebook_path).resolve())
        manager = self.kernels.get(path)

        if manager is None or not manager.is_running:
            raise RuntimeError(f"No active kernel running for notebook: {notebook_path}")

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