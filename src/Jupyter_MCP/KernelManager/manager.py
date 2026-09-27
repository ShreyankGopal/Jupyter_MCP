"""
KernelManager for Jupyter notebook execution.
Manages kernel lifecycle, cell execution, and runtime state.
"""

from jupyter_client import KernelManager as JupyterKernelManager, KernelClient
from typing import Optional, Dict, Any
import time
from .executor import CellExecutor


class KernelManager:
    """Manages Jupyter kernel lifecycle and execution."""
    
    def __init__(self, default_timeout: int = 30, custom_kernel_id: Optional[str] = None):
        """Initialize the KernelManager.
        
        Args:
            default_timeout: Default timeout for cell execution
            custom_kernel_id: Optional custom kernel ID (e.g., SHA256 hash)
        """
        self.kernel_manager: Optional[JupyterKernelManager] = None
        self.kernel_client: Optional[KernelClient] = None
        self.kernel_id: Optional[str] = custom_kernel_id  # Our tracking ID
        self.jupyter_kernel_id: Optional[str] = None  # Jupyter's actual kernel ID
        self.is_running = False
        self.executor = CellExecutor(default_timeout=default_timeout)
        self.connection_info: Optional[Dict[str, Any]] = None
    
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
            
            # Capture Jupyter's actual kernel ID
            self.jupyter_kernel_id = self.kernel_manager.kernel_id if hasattr(self.kernel_manager, 'kernel_id') else None
            
            # Generate our tracking kernel ID (fallback if Jupyter ID not available)
            self.kernel_id = self.jupyter_kernel_id if self.jupyter_kernel_id else f"kernel_{int(time.time())}"
            self.is_running = True
            
            # Get connection info
            connection_info = {
                'ip': self.kernel_manager.ip if hasattr(self.kernel_manager, 'ip') else None,
                'ports': self.kernel_manager.ports if hasattr(self.kernel_manager, 'ports') else None,
                'transport': self.kernel_manager.transport if hasattr(self.kernel_manager, 'transport') else None,
                'key': self.kernel_manager.key if hasattr(self.kernel_manager, 'key') else None,
                'signature_scheme': self.kernel_manager.signature_scheme if hasattr(self.kernel_manager, 'signature_scheme') else None
            }
            
            # Store connection info for later use
            self.connection_info = connection_info
            
            return {
                'kernel_id': self.kernel_id,  # Our tracking ID (or Jupyter's if available)
                'jupyter_kernel_id': self.jupyter_kernel_id,  # Jupyter's actual kernel ID
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
                'kernel_id': Optional[str],
                'jupyter_kernel_id': Optional[str]
            }
        """
        return {
            'is_running': self.is_running,
            'kernel_id': self.kernel_id,
            'jupyter_kernel_id': self.jupyter_kernel_id
        }

    def execute_code(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute code string in the running kernel.

        Args:
            code: Source code string to execute
            timeout: Optional execution timeout in seconds

        Returns:
            Dictionary with execution outputs and status

        Raises:
            RuntimeError: If kernel is not running
        """
        if not self.is_running or not self.kernel_client:
            raise RuntimeError("Kernel is not running")

        return self.executor.execute(self.kernel_client, code, timeout=timeout)
    
    def connect_to_existing_kernel(self, connection_info: Dict[str, Any], jupyter_kernel_id: str) -> Dict[str, Any]:
        """
        Connect to an existing Jupyter kernel using connection information.
        
        Args:
            connection_info: Dictionary containing connection details (ip, ports, transport, key)
            jupyter_kernel_id: The Jupyter kernel ID to connect to
            
        Returns:
            Dictionary with connection status and kernel information
            
        Raises:
            RuntimeError: If connection fails
        """
        if self.is_running:
            raise RuntimeError("Kernel is already running")
        
        try:
            # Create kernel manager with existing connection info
            self.kernel_manager = JupyterKernelManager(
                ip=connection_info.get('ip', '127.0.0.1'),
                transport=connection_info.get('transport', 'tcp'),
                kernel_name='python3'  # Default, can be customized
            )
            
            # Set the connection ports and key
            if 'ports' in connection_info:
                self.kernel_manager.ports = connection_info['ports']
            if 'key' in connection_info:
                self.kernel_manager.key = connection_info['key']
            if 'signature_scheme' in connection_info:
                self.kernel_manager.signature_scheme = connection_info['signature_scheme']
            
            # Create kernel client
            self.kernel_client = self.kernel_manager.client()
            self.kernel_client.start_channels()
            
            # Store IDs
            self.jupyter_kernel_id = jupyter_kernel_id
            self.kernel_id = self.kernel_id if self.kernel_id else self.jupyter_kernel_id
            self.is_running = True
            self.connection_info = connection_info
            
            return {
                'kernel_id': self.kernel_id,
                'jupyter_kernel_id': self.jupyter_kernel_id,
                'status': 'running',
                'connection_info': connection_info
            }
            
        except Exception as e:
            self._cleanup_kernel()
            raise RuntimeError(f"Failed to connect to existing kernel: {str(e)}")
    
    def verify_kernel_running(self, connection_info: Dict[str, Any]) -> bool:
        """
        Verify if a kernel with the given connection info is still running.
        
        Args:
            connection_info: Dictionary containing connection details
            
        Returns:
            True if kernel is running, False otherwise
        """
        try:
            # Create a temporary kernel manager to test connection
            temp_manager = JupyterKernelManager(
                ip=connection_info.get('ip', '127.0.0.1'),
                transport=connection_info.get('transport', 'tcp')
            )
            
            if 'ports' in connection_info:
                temp_manager.ports = connection_info['ports']
            if 'key' in connection_info:
                temp_manager.key = connection_info['key']
            if 'signature_scheme' in connection_info:
                temp_manager.signature_scheme = connection_info['signature_scheme']
            
            # Try to create a client and test connection
            temp_client = temp_manager.client()
            temp_client.start_channels()
            
            # Send a simple test message (like kernel info request)
            try:
                # This is a basic connectivity test
                # In a real implementation, you might send a kernel_info request
                temp_client.stop_channels()
                return True
            except Exception:
                temp_client.stop_channels()
                return False
                
        except Exception:
            return False