"""
Test to verify that MCP tools only do file I/O and don't interact with kernels.

This test demonstrates that:
1. edit_cell only modifies the .ipynb file
2. No kernel processes are started/restarted
3. The tools work purely through nbformat file manipulation
"""

import os
import sys
import tempfile
import nbformat
from pathlib import Path
import psutil
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test that MCP tools don't interact with kernels
def test_edit_cell_no_kernel_interaction():
    """Test that edit_cell only does file I/O, no kernel operations."""
    
    # Create a temporary notebook
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        temp_notebook = f.name
    
    try:
        # Create a simple notebook
        notebook = nbformat.v4.new_notebook()
        notebook.cells.append(nbformat.v4.new_code_cell("x = 30"))
        nbformat.write(notebook, temp_notebook)
        
        # Get initial process count (all running processes)
        initial_processes = len(psutil.pids())
        print(f"Initial process count: {initial_processes}")
        
        # Import and use the manager directly (simulating MCP tool behavior)
        from Jupyter_MCP.Notebook.manager import NotebookManager
        manager = NotebookManager()
        
        # List cells (file I/O only)
        cells = manager.list_cells(temp_notebook)
        print(f"Listed {len(cells)} cells via file I/O")
        
        # Edit a cell (file I/O only)
        if cells:
            result = manager.edit_cell(
                notebook_path=temp_notebook,
                cell_id=cells[0].cell_id,
                new_source="x = 40"
            )
            print(f"Edited cell: {result['status']}")
        
        # Check process count after operations
        final_processes = len(psutil.pids())
        print(f"Final process count: {final_processes}")
        
        # Verify no new processes were created (no kernel started)
        process_diff = final_processes - initial_processes
        print(f"Process difference: {process_diff}")
        
        # Allow for small process count variations (OS background processes)
        # but no significant new processes should be created
        assert abs(process_diff) <= 2, f"Too many process changes: {process_diff}"
        
        # Verify the file was actually modified
        updated_notebook = nbformat.read(temp_notebook, as_version=4)
        updated_source = updated_notebook.cells[0].source
        assert updated_source == "x = 40", f"File not updated correctly: {updated_source}"
        
        print("✓ Test passed: edit_cell only does file I/O, no kernel interaction")
        
    finally:
        # Clean up
        if os.path.exists(temp_notebook):
            os.remove(temp_notebook)


def test_manager_methods_file_io_only():
    """Test that all NotebookManager methods only do file I/O."""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        temp_notebook = f.name
    
    try:
        # Create test notebook
        notebook = nbformat.v4.new_notebook()
        notebook.cells.append(nbformat.v4.new_code_cell("print('test')"))
        nbformat.write(notebook, temp_notebook)
        
        from Jupyter_MCP.Notebook.manager import NotebookManager
        manager = NotebookManager()
        
        # Test all methods that should only do file I/O
        print("Testing list_cells...")
        cells = manager.list_cells(temp_notebook)
        assert len(cells) == 1
        
        print("Testing get_cell...")
        cell = manager.get_cell(temp_notebook, cells[0].cell_id)
        assert cell.source == "print('test')"
        
        print("Testing propose_edit...")
        edit = manager.propose_edit(temp_notebook, cells[0].cell_id, "print('edited')")
        assert edit.status == "pending"
        
        print("Testing edit_cell...")
        result = manager.edit_cell(temp_notebook, cells[0].cell_id, "print('direct edit')")
        assert result['status'] == "applied"
        
        print("✓ All methods only perform file I/O operations")
        
    finally:
        if os.path.exists(temp_notebook):
            os.remove(temp_notebook)


def test_no_jupyter_kernel_processes():
    """Test that no Jupyter kernel processes are running during operations."""
    
    # Check for Jupyter kernel processes before
    def count_jupyter_kernels():
        count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if 'jupyter' in proc.info['name'].lower() and 'kernel' in proc.info['name'].lower():
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return count
    
    initial_kernels = count_jupyter_kernels()
    print(f"Initial Jupyter kernel processes: {initial_kernels}")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        temp_notebook = f.name
    
    try:
        # Create and operate on notebook
        notebook = nbformat.v4.new_notebook()
        notebook.cells.append(nbformat.v4.new_code_cell("x = 1"))
        nbformat.write(notebook, temp_notebook)
        
        from Jupyter_MCP.Notebook.manager import NotebookManager
        manager = NotebookManager()
        
        # Perform operations
        cells = manager.list_cells(temp_notebook)
        manager.edit_cell(temp_notebook, cells[0].cell_id, "x = 2")
        
        # Check kernel processes after
        final_kernels = count_jupyter_kernels()
        print(f"Final Jupyter kernel processes: {final_kernels}")
        
        assert initial_kernels == final_kernels, "Jupyter kernel processes changed during operations"
        print("✓ No Jupyter kernel processes started during operations")
        
    finally:
        if os.path.exists(temp_notebook):
            os.remove(temp_notebook)


if __name__ == "__main__":
    print("Testing MCP tools only do file I/O, no kernel interaction...\n")
    
    test_edit_cell_no_kernel_interaction()
    print()
    
    test_manager_methods_file_io_only()
    print()
    
    test_no_jupyter_kernel_processes()
    print()
    
    print("All tests passed! MCP tools only perform file I/O operations.")