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
    