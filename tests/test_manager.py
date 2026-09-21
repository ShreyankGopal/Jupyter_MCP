import pytest
import nbformat
import tempfile
import os
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from Jupyter_MCP.Notebook.manager import NotebookManager
from Jupyter_MCP.Notebook.models import Cell
from Jupyter_MCP.Notebook.diff import generate_diff


@pytest.fixture
def sample_notebook():
    """Create a sample notebook for testing."""
    notebook = nbformat.v4.new_notebook()
    
    # Add a markdown cell
    markdown_cell = nbformat.v4.new_markdown_cell("# Training")
    notebook.cells.append(markdown_cell)
    
    # Add a code cell
    code_cell = nbformat.v4.new_code_cell("import torch")
    code_cell.execution_count = 1
    notebook.cells.append(code_cell)
    
    # Add another code cell with output
    code_cell2 = nbformat.v4.new_code_cell("x = 10\nprint(x)")
    code_cell2.execution_count = 2
    code_cell2.outputs = [
        nbformat.v4.new_output("stream", name="stdout", text="10\n")
    ]
    notebook.cells.append(code_cell2)
    
    return notebook


@pytest.fixture
def temp_notebook_file(sample_notebook):
    """Create a temporary notebook file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
        nbformat.write(sample_notebook, f.name)
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


class TestNotebookManager:
    """Test the NotebookManager class."""
    
    def test_list_cells(self, temp_notebook_file):
        """Test listing all cells in a notebook."""
        manager = NotebookManager()
        cells = manager.list_cells(temp_notebook_file)
        
        assert len(cells) == 3
        assert cells[0].cell_type == "markdown"
        assert cells[0].source == "# Training"
        assert cells[0].position == 0
        
        assert cells[1].cell_type == "code"
        assert cells[1].source == "import torch"
        assert cells[1].position == 1
        assert cells[1].execution_count == 1
        assert cells[1].has_output is False
        
        assert cells[2].cell_type == "code"
        assert cells[2].source == "x = 10\nprint(x)"
        assert cells[2].position == 2
        assert cells[2].execution_count == 2
        assert cells[2].has_output is True
    
    def test_list_cells_generates_stable_ids(self, temp_notebook_file):
        """Test that list_cells generates stable IDs for cells without them."""
        manager = NotebookManager()
        
        # First call should generate IDs
        cells_first = manager.list_cells(temp_notebook_file)
        cell_ids_first = [cell.cell_id for cell in cells_first]
        
        # Second call should return the same IDs
        cells_second = manager.list_cells(temp_notebook_file)
        cell_ids_second = [cell.cell_id for cell in cells_second]
        
        assert cell_ids_first == cell_ids_second
        assert all(len(cell_id) > 0 for cell_id in cell_ids_first)
    
    def test_list_cells_calculates_line_numbers(self, temp_notebook_file):
        """Test that list_cells correctly calculates line numbers."""
        manager = NotebookManager()
        cells = manager.list_cells(temp_notebook_file)
        
        # First cell (markdown) should start at line 1
        assert cells[0].line_start == 1
        assert cells[0].line_end == 1
        
        # Second cell (code) should start after first cell
        assert cells[1].line_start == 2
        assert cells[1].line_end == 2
        
        # Third cell (multiline code) should span multiple lines
        assert cells[2].line_start == 3
        assert cells[2].line_end == 4
    
    def test_get_cell_by_id(self, temp_notebook_file):
        """Test getting a specific cell by its ID."""
        manager = NotebookManager()
        
        # First, list all cells to get a valid cell ID
        cells = manager.list_cells(temp_notebook_file)
        first_cell_id = cells[0].cell_id
        
        # Get the specific cell
        cell = manager.get_cell(temp_notebook_file, first_cell_id)
        
        # Verify it matches the first cell from list_cells
        assert cell.cell_id == first_cell_id
        assert cell.position == 0
        assert cell.cell_type == "markdown"
        assert cell.source == "# Training"
        assert cell.line_start == 1
        assert cell.line_end == 1
    
    def test_get_cell_nonexistent_id(self, temp_notebook_file):
        """Test that get_cell raises error for non-existent cell ID."""
        manager = NotebookManager()
        
        # Try to get a cell with a non-existent ID
        with pytest.raises(ValueError, match="Cell with ID 'nonexistent' not found"):
            manager.get_cell(temp_notebook_file, "nonexistent")
    
    def test_get_cell_with_sample_notebook(self):
        """Test get_cell with the actual sample notebook."""
        manager = NotebookManager()
        sample_path = "sample.ipynb"
        
        # First list cells to get valid IDs
        cells = manager.list_cells(sample_path)
        assert len(cells) == 2
        
        # Get each cell by ID
        for expected_cell in cells:
            retrieved_cell = manager.get_cell(sample_path, expected_cell.cell_id)
            
            # Verify all fields match
            assert retrieved_cell.cell_id == expected_cell.cell_id
            assert retrieved_cell.position == expected_cell.position
            assert retrieved_cell.cell_type == expected_cell.cell_type
            assert retrieved_cell.source == expected_cell.source
            assert retrieved_cell.line_start == expected_cell.line_start
            assert retrieved_cell.line_end == expected_cell.line_end
            assert retrieved_cell.execution_count == expected_cell.execution_count
            assert retrieved_cell.has_output == expected_cell.has_output


class TestDiffGeneration:
    """Test the diff generation functionality."""
    
    def test_generate_diff_simple_change(self):
        """Test generating a diff for a simple change."""
        old_source = "x = 10\ny = x + 5\nprint(y)"
        new_source = "x = 10\ny = x + 10\nprint(y)"
        
        diff = generate_diff(old_source, new_source)
        
        assert "--- before" in diff
        assert "+++ after" in diff
        assert "-y = x + 5" in diff
        assert "+y = x + 10" in diff
    
    def test_generate_diff_no_change(self):
        """Test generating a diff when there's no change."""
        old_source = "x = 10\ny = x + 5"
        new_source = "x = 10\ny = x + 5"
        
        diff = generate_diff(old_source, new_source)
        
        # Should be empty or minimal when no changes
        assert diff == "" or "--- before" in diff
    
    def test_generate_diff_addition(self):
        """Test generating a diff for an addition."""
        old_source = "x = 10"
        new_source = "x = 10\ny = 20"
        
        diff = generate_diff(old_source, new_source)
        
        assert "+y = 20" in diff
    
    def test_generate_diff_deletion(self):
        """Test generating a diff for a deletion."""
        old_source = "x = 10\ny = 20"
        new_source = "x = 10"
        
        diff = generate_diff(old_source, new_source)
        
        assert "-y = 20" in diff
