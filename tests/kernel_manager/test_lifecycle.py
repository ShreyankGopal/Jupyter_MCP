"""
Tests for KernelManager kernel lifecycle functions.
Tests start_kernel, stop_kernel, and get_kernel_status.
"""

import sys
from pathlib import Path
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from Jupyter_MCP.KernelManager.manager import KernelManager


def test_start_kernel():
    """Test starting a Jupyter kernel."""
    print("Testing start_kernel...")
    
    manager = KernelManager()
    
    # Start kernel
    result = manager.start_kernel(kernel_name='python3')
    
    print(f"Kernel started successfully:")
    print(f"  Kernel ID: {result['kernel_id']}")
    print(f"  Status: {result['status']}")
    print(f"  Connection Info: {result['connection_info']}")
    
    # Add delay for kernel to fully initialize
    time.sleep(1)
    
    # Verify kernel is running
    status = manager.get_kernel_status()
    assert status['is_running'] == True, "Kernel should be running"
    assert status['kernel_id'] == result['kernel_id'], "Kernel ID should match"
    
    # Cleanup
    manager.stop_kernel()
    
    print("✓ start_kernel test passed")


def test_stop_kernel():
    """Test stopping a Jupyter kernel."""
    print("\nTesting stop_kernel...")
    
    manager = KernelManager()
    
    # Start kernel first
    manager.start_kernel(kernel_name='python3')
    print("Kernel started")
    
    # Add small delay for kernel to fully initialize
    time.sleep(1)
    
    # Stop kernel
    result = manager.stop_kernel()
    
    print(f"Kernel stopped successfully:")
    print(f"  Kernel ID: {result['kernel_id']}")
    print(f"  Status: {result['status']}")
    
    # Verify kernel is stopped
    status = manager.get_kernel_status()
    assert status['is_running'] == False, "Kernel should not be running"
    assert status['kernel_id'] is None, "Kernel ID should be None"
    
    print("✓ stop_kernel test passed")


def test_start_already_running():
    """Test that starting a kernel when one is already running raises an error."""
    print("\nTesting start_kernel when kernel already running...")
    
    manager = KernelManager()
    
    # Start first kernel
    manager.start_kernel(kernel_name='python3')
    print("First kernel started")
    
    # Add delay for kernel to fully initialize
    time.sleep(1)
    
    # Try to start second kernel (should fail)
    try:
        manager.start_kernel(kernel_name='python3')
        print("✗ Should have raised RuntimeError")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        print(f"✓ Correctly raised RuntimeError: {e}")
    
    # Cleanup
    manager.stop_kernel()
    # Add delay for cleanup
    time.sleep(1)
    print("✓ start_already_running test passed")


def test_stop_no_kernel():
    """Test that stopping a kernel when none is running raises an error."""
    print("\nTesting stop_kernel when no kernel is running...")
    
    manager = KernelManager()
    
    # Try to stop kernel without starting one (should fail)
    try:
        manager.stop_kernel()
        print("✗ Should have raised RuntimeError")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        print(f"✓ Correctly raised RuntimeError: {e}")
    
    print("✓ stop_no_kernel test passed")


def test_get_kernel_status():
    """Test getting kernel status."""
    print("\nTesting get_kernel_status...")
    
    manager = KernelManager()
    
    # Status when not running
    status = manager.get_kernel_status()
    print(f"Status when not running: {status}")
    assert status['is_running'] == False, "Should not be running"
    assert status['kernel_id'] is None, "Kernel ID should be None"
    
    # Start kernel
    manager.start_kernel(kernel_name='python3')
    
    # Status when running
    status = manager.get_kernel_status()
    print(f"Status when running: {status}")
    assert status['is_running'] == True, "Should be running"
    assert status['kernel_id'] is not None, "Kernel ID should not be None"
    
    # Cleanup
    manager.stop_kernel()
    
    print("✓ get_kernel_status test passed")


def test_kernel_lifecycle():
    """Test complete kernel lifecycle: start -> status -> stop."""
    print("\nTesting complete kernel lifecycle...")
    
    manager = KernelManager()
    
    # Initial status
    status = manager.get_kernel_status()
    print(f"Initial status: {status}")
    assert status['is_running'] == False
    
    # Start kernel
    start_result = manager.start_kernel(kernel_name='python3')
    print(f"Started: {start_result['kernel_id']}")
    
    # Add delay for kernel to fully initialize
    time.sleep(1)
    
    # Running status
    status = manager.get_kernel_status()
    print(f"Running status: {status}")
    assert status['is_running'] == True
    
    # Stop kernel
    stop_result = manager.stop_kernel()
    print(f"Stopped: {stop_result['kernel_id']}")
    
    # Final status
    status = manager.get_kernel_status()
    print(f"Final status: {status}")
    assert status['is_running'] == False
    
    print("✓ kernel_lifecycle test passed")


def main():
    """Run all kernel lifecycle tests."""
    print("=" * 60)
    print("KernelManager Lifecycle Tests")
    print("=" * 60)
    
    try:
        test_start_kernel()
        test_stop_kernel()
        test_start_already_running()
        test_stop_no_kernel()
        test_get_kernel_status()
        test_kernel_lifecycle()
        
        print("\n" + "=" * 60)
        print("All kernel lifecycle tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    main()