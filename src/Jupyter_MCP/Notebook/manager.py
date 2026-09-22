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
    
    def propose_edit(self, notebook_path: str, cell_id: str, new_source: str) -> CellEdit:
        """Propose an edit to a cell without modifying the notebook.
        
        Args:
            notebook_path: Path to the .ipynb file
            cell_id: The stable cell ID to edit
            new_source: The proposed new source code
            
        Returns:
            A CellEdit object with status "pending"
            
        Raises:
            ValueError: If the cell_id does not exist in the notebook
            TypeError: If new_source is not a string
        """
        # Validate new_source is a string
        if not isinstance(new_source, str):
            raise TypeError("new_source must be a string")
        
        # Load notebook and ensure cell IDs
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)
        
        # Find the cell by its stable ID
        target_cell = None
        for cell in notebook.cells:
            if cell['id'] == cell_id:
                target_cell = cell
                break
        
        if target_cell is None:
            raise ValueError(f"Cell with ID '{cell_id}' not found in notebook")
        
        # Get current source
        old_source = target_cell['source']
        
        # Generate diff
        diff = generate_diff(old_source, new_source)
        
        # Create edit ID
        edit_id = f"edit_{str(uuid.uuid4())[:8]}"
        
        # Create CellEdit object
        cell_edit = CellEdit(
            edit_id=edit_id,
            notebook_path=notebook_path,
            cell_id=cell_id,
            old_source=old_source,
            new_source=new_source,
            diff=diff,
            status="pending"
        )
        
        # Store in pending edits
        self.pending_edits[edit_id] = cell_edit
        
        return cell_edit
    
    def edit_cell(self, notebook_path: str, cell_id: str, new_source: str) -> dict:
        """Directly edit a cell and return the diff.
        
        Args:
            notebook_path: Path to the .ipynb file
            cell_id: The stable cell ID to edit
            new_source: The new source code
            
        Returns:
            Dictionary with edit details and diff
            
        Raises:
            ValueError: If the cell_id does not exist in the notebook
            TypeError: If new_source is not a string
        """
        # Validation
        if not isinstance(new_source, str):
            raise TypeError("new_source must be a string")
        
        # Load and find cell
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)
        
        target_cell = None
        for cell in notebook.cells:
            if cell['id'] == cell_id:
                target_cell = cell
                break
        
        if target_cell is None:
            raise ValueError(f"Cell with ID '{cell_id}' not found in notebook")
        
        # Generate diff before modification
        old_source = target_cell['source']
        diff = generate_diff(old_source, new_source)
        
        # Apply change
        target_cell['source'] = new_source
        
        # Save notebook
        self._save_notebook(notebook, notebook_path)
        
        # Return result
        return {
            "cell_id": cell_id,
            "old_source": old_source,
            "new_source": new_source,
            "diff": diff,
            "status": "applied"
        }
    
    def insert_cell(self, notebook_path: str, position: int, cell_type: str, source: str) -> dict:
        """Insert a new cell at the specified position.
        
        Args:
            notebook_path: Path to the .ipynb file
            position: Position to insert the cell (0-based index)
            cell_type: Type of cell ('code', 'markdown', or 'raw')
            source: The source code/content for the cell
            
        Returns:
            Dictionary with cell_id, position, cell_type, and source
            
        Raises:
            ValueError: If position is invalid or cell_type is not supported
            TypeError: If source is not a string
        """
        # Validate inputs
        if not isinstance(source, str):
            raise TypeError("source must be a string")
        
        supported_cell_types = ['code', 'markdown', 'raw']
        if cell_type not in supported_cell_types:
            raise ValueError(f"cell_type must be one of {supported_cell_types}")
        
        # Load notebook
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)
        
        # Validate position
        if position < 0 or position > len(notebook.cells):
            raise ValueError(f"position must be between 0 and {len(notebook.cells)}")
        
        # Create new cell based on type
        if cell_type == 'code':
            new_cell = nbformat.v4.new_code_cell(source=source)
        elif cell_type == 'markdown':
            new_cell = nbformat.v4.new_markdown_cell(source=source)
        elif cell_type == 'raw':
            new_cell = nbformat.v4.new_raw_cell(source=source)
        
        # Ensure cell has ID
        new_cell['id'] = str(uuid.uuid4())[:8]
        
        # Insert at specified position
        notebook.cells.insert(position, new_cell)
        
        # Save notebook
        self._save_notebook(notebook, notebook_path)
        
        # Return result
        return {
            "cell_id": new_cell['id'],
            "position": position,
            "cell_type": cell_type,
            "source": source
        }
