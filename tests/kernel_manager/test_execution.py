"""
Tests for cell execution logic in KernelManager and KernelRegistry.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
import nbformat
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from Jupyter_MCP.KernelManager.manager import KernelManager
from Jupyter_MCP.KernelManager.Registry import KernelRegistry
from Jupyter_MCP.Notebook.manager import NotebookManager


def test_kernel_manager_execute_code():
    """Test KernelManager code execution and output collection."""
    manager = KernelManager()
    manager.start_kernel(kernel_name="python3")
    time.sleep(1)

    try:
        # Test basic print statement
        result = manager.execute_code("print('Hello Jupyter MCP')")
        assert result["status"] == "ok"
        assert len(result["outputs"]) > 0
        assert any("Hello Jupyter MCP" in out.get("text", "") for out in result["outputs"])
        assert result["execution_count"] is not None


        # Test state persistence
        result_def = manager.execute_code("x = 42")
        assert result_def["status"] == "ok"

        result_use = manager.execute_code("print(x + 8)")
        assert result_use["status"] == "ok"
        assert any("50" in out.get("text", "") for out in result_use["outputs"])

        # Test expression result
        result_expr = manager.execute_code("x * 2")
        assert result_expr["status"] == "ok"
        assert any(out.get("output_type") == "execute_result" for out in result_expr["outputs"])

        # Test error handling
        result_err = manager.execute_code("1 / 0")
        assert result_err["status"] == "error"
        assert result_err["ename"] == "ZeroDivisionError"
        assert any(out.get("output_type") == "error" for out in result_err["outputs"])

    finally:
        manager.stop_kernel()


def test_registry_execute_cell_and_save_notebook():
    """Test KernelRegistry execute_cell updates both kernel state and .ipynb file."""
    notebook_mgr = NotebookManager()
    registry = KernelRegistry()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ipynb", delete=False) as f:
        temp_notebook_path = f.name

    try:
        # Create a notebook with two cells
        nb = nbformat.v4.new_notebook()
        cell1 = nbformat.v4.new_code_cell(source="a = 100\nprint(f'a is {a}')")
        cell1["id"] = "cell_1"
        cell2 = nbformat.v4.new_code_cell(source="b = a * 2\nprint(f'b is {b}')")
        cell2["id"] = "cell_2"
        nb.cells.extend([cell1, cell2])
        nbformat.write(nb, temp_notebook_path)

        # Start kernel for notebook
        registry.start_kernel(temp_notebook_path)
        time.sleep(1)

        # Execute cell at position 0
        res1 = registry.execute_cell(temp_notebook_path, notebook_manager=notebook_mgr, position=0)
        assert res1["status"] == "ok"
        assert res1["position"] == 0
        assert res1["cell_id"] == "cell_1"
        assert res1["execution_count"] == 1
        assert any("a is 100" in out.get("text", "") for out in res1["outputs"])

        # Execute cell at position 1 (depends on cell 0's variable 'a')
        res2 = registry.execute_cell(temp_notebook_path, notebook_manager=notebook_mgr, position=1)
        assert res2["status"] == "ok"
        assert res2["position"] == 1
        assert res2["cell_id"] == "cell_2"
        assert res2["execution_count"] == 2
        assert any("b is 200" in out.get("text", "") for out in res2["outputs"])

        # Verify the notebook file on disk was updated with outputs and execution count
        updated_nb = nbformat.read(temp_notebook_path, as_version=4)
        assert updated_nb.cells[0].execution_count == 1
        assert len(updated_nb.cells[0].outputs) > 0
        assert any("a is 100" in out.get("text", "") for out in updated_nb.cells[0].outputs)

        assert updated_nb.cells[1].execution_count == 2
        assert len(updated_nb.cells[1].outputs) > 0
        assert any("b is 200" in out.get("text", "") for out in updated_nb.cells[1].outputs)

    finally:
        registry.stop_kernel(temp_notebook_path)
        if os.path.exists(temp_notebook_path):
            os.remove(temp_notebook_path)


