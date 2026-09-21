import nbformat
from typing import List, Optional
import uuid
from .models import Cell, CellEdit
from .diff import generate_diff


class NotebookManager:
    """Manages Jupyter notebook state without kernel execution."""
    
    def __init__(self):
        self.pending_edits: dict[str, CellEdit] = {}
    
    def _load_notebook(self, notebook_path: str) -> nbformat.NotebookNode:
        """Load a notebook from disk."""
        return nbformat.read(notebook_path, as_version=4)
    
    def _save_notebook(self, notebook: nbformat.NotebookNode, notebook_path: str) -> None:
        """Save a notebook to disk."""
        nbformat.write(notebook, notebook_path)
    
    def _ensure_cell_ids(self, notebook: nbformat.NotebookNode) -> None:
        """Ensure all cells have stable IDs."""
        for cell in notebook.cells:
            if 'id' not in cell or not cell['id']:
                cell['id'] = str(uuid.uuid4())[:8]
    
    def _calculate_line_numbers(self, notebook: nbformat.NotebookNode) -> dict[str, tuple[int, int]]:
        """Calculate line_start and line_end for each cell."""
        line_numbers = {}
        current_line = 1
        
        for cell in notebook.cells:
            cell_id = cell['id']
            source_lines = len(cell['source'].split('\n'))
            line_numbers[cell_id] = (current_line, current_line + source_lines - 1)
            current_line += source_lines
        
        return line_numbers
    
    def list_cells(self, notebook_path: str) -> List[Cell]:
        """List all cells in a notebook.
        
        Args:
            notebook_path: Path to the .ipynb file
            
        Returns:
            List of Cell objects representing all cells in the notebook
        """
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)
        line_numbers = self._calculate_line_numbers(notebook)
        
        cells = []
        for position, cell in enumerate(notebook.cells):
            cell_id = cell['id']
            line_start, line_end = line_numbers[cell_id]
            
            cell_obj = Cell(
                cell_id=cell_id,
                position=position,
                cell_type=cell['cell_type'],
                source=cell['source'],
                line_start=line_start,
                line_end=line_end,
                execution_count=cell.get('execution_count'),
                has_output=bool(cell.get('outputs'))
            )
            cells.append(cell_obj)
        
        return cells
    
    def get_cell(self, notebook_path: str, cell_id: str) -> Cell:
        """Get a specific cell by its stable ID.
        
        Args:
            notebook_path: Path to the .ipynb file
            cell_id: The stable cell ID to retrieve
            
        Returns:
            A Cell object with complete source and metadata
            
        Raises:
            ValueError: If the cell_id does not exist in the notebook
        """
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)
        line_numbers = self._calculate_line_numbers(notebook)
        
        # Find the cell by its stable ID
        for position, cell in enumerate(notebook.cells):
            if cell['id'] == cell_id:
                line_start, line_end = line_numbers[cell_id]
                
                cell_obj = Cell(
                    cell_id=cell_id,
                    position=position,
                    cell_type=cell['cell_type'],
                    source=cell['source'],
                    line_start=line_start,
                    line_end=line_end,
                    execution_count=cell.get('execution_count'),
                    has_output=bool(cell.get('outputs'))
                )
                return cell_obj
        
        # Cell not found
        raise ValueError(f"Cell with ID '{cell_id}' not found in notebook")
