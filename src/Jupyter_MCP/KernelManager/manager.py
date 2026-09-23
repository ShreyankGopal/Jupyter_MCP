"""
KernelManager for Jupyter notebook execution.
Manages kernel lifecycle, cell execution, and runtime state.
"""

from jupyter_client import KernelManager as JupyterKernelManager, KernelClient
from typing import Optional, Dict, Any
import time


class KernelManager:
    """Manages Jupyter kernel lifecycle and execution."""
    
    def __init__(self):
        """Initialize the KernelManager."""
        self.kernel_manager: Optional[KernelManager] = None
        self.kernel_client: Optional[KernelClient] = None
        self.kernel_id: Optional[str] = None
        self.is_running = False
    
    def start_kernel(self, kernel_name: str = 'python3') -> Dict[str, Any]:
        """
        Start a Jupyter kernel and establish connection.
        
        Args:
            kernel_name: Name of the kernel to start (default: python3)
            
        Returns:
            Dictionary with kernel information:
            {
                'kernel_id': str,
                'kernel_name': str,
                'status': 'running',
                'connection_info': dict
            }
            
        Raises:
            RuntimeError: If kernel is already running or fails to start
        """
        if self.is_running:
            raise RuntimeError("Kernel is already running")
        
        try:
            # Create kernel manager without parameters
            self.kernel_manager = JupyterKernelManager()
            
            # Start the kernel (will use default kernel)
            self.kernel_manager.start_kernel()
            
            # Create kernel client
            self.kernel_client = self.kernel_manager.client()
            self.kernel_client.start_channels()
            
            # Generate kernel ID
            self.kernel_id = f"kernel_{int(time.time())}"
            self.is_running = True
            
            # Get connection info
            connection_info = {
                'ip': self.kernel_manager.ip if hasattr(self.kernel_manager, 'ip') else None,
                'ports': self.kernel_manager.ports if hasattr(self.kernel_manager, 'ports') else None,
                'transport': self.kernel_manager.transport if hasattr(self.kernel_manager, 'transport') else None
            }
            
            return {
                'kernel_id': self.kernel_id,
                'status': 'running',
                'connection_info': connection_info
            }
            
        except Exception as e:
            # Cleanup on failure
            self._cleanup_kernel()
            raise RuntimeError(f"Failed to start kernel: {str(e)}")
    
    def stop_kernel(self) -> Dict[str, Any]:
        """
        Stop the running kernel and clean up resources.
        
        Returns:
            Dictionary with shutdown status:
            {
                'kernel_id': str,
                'status': 'stopped'
            }
            
        Raises:
            RuntimeError: If no kernel is running
        """
        if not self.is_running:
            raise RuntimeError("No kernel is currently running")
        
        try:
            # Interrupt any running execution (using kernel manager's interrupt)
            if self.kernel_manager:
                try:
                    self.kernel_manager.interrupt_kernel()
                except Exception:
                    print(Exception)
                    pass  # Interrupt may fail if nothing is running
            
            # Stop communication channels
            if self.kernel_client:
                self.kernel_client.stop_channels()
            
            # Shutdown kernel
            if self.kernel_manager:
                self.kernel_manager.shutdown_kernel()
            
            kernel_id = self.kernel_id
            
            # Cleanup
            self._cleanup_kernel()
            
            return {
                'kernel_id': kernel_id,
                'status': 'stopped'
            }
            
        except Exception as e:
            # Force cleanup even if shutdown fails
            self._cleanup_kernel()
            raise RuntimeError(f"Failed to stop kernel: {str(e)}")
    
    def _cleanup_kernel(self) -> None:
        """Internal method to clean up kernel resources."""
        try:
            if self.kernel_client:
                self.kernel_client.stop_channels()
                self.kernel_client = None
        except Exception:
            pass
        
        try:
            if self.kernel_manager:
                self.kernel_manager.shutdown_kernel()
                self.kernel_manager = None
        except Exception:
            pass
        
        self.kernel_id = None
        self.is_running = False
    
    def get_kernel_status(self) -> Dict[str, Any]:
        """
        Get the current status of the kernel.
        
        Returns:
            Dictionary with kernel status:
            {
                'is_running': bool,
                'kernel_id': Optional[str]
            }
        """
        return {
            'is_running': self.is_running,
            'kernel_id': self.kernel_id
        }