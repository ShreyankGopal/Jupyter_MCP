#!/usr/bin/env python3
"""Test script to check if jupyter_client provides kernel_id"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from Jupyter_MCP.KernelManager.manager import KernelManager

# Test kernel ID capture
print("Testing kernel ID capture...")
manager = KernelManager()

try:
    result = manager.start_kernel()
    print(f"Kernel started successfully!")
    print(f"Our kernel_id: {result.get('kernel_id')}")
    print(f"Jupyter kernel_id: {result.get('jupyter_kernel_id')}")
    print(f"Status: {result.get('status')}")
    
    # Check kernel manager attributes
    if manager.kernel_manager:
        print(f"\nJupyterKernelManager attributes:")
        print(f"Has kernel_id: {hasattr(manager.kernel_manager, 'kernel_id')}")
        if hasattr(manager.kernel_manager, 'kernel_id'):
            print(f"Actual kernel_id: {manager.kernel_manager.kernel_id}")
        print(f"Has _kernel_id: {hasattr(manager.kernel_manager, '_kernel_id')}")
        if hasattr(manager.kernel_manager, '_kernel_id'):
            print(f"Actual _kernel_id: {manager.kernel_manager._kernel_id}")
    
    # Cleanup
    manager.stop_kernel()
    print("\nKernel stopped successfully")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
