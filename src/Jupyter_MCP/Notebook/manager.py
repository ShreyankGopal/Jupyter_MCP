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

    def get_cell_by_position(self, notebook_path: str, position: int) -> Cell:
        """Get a specific cell by its 0-based position index.
        
        Args:
            notebook_path: Path to the .ipynb file
            position: 0-based index of the cell
            
        Returns:
            A Cell object with complete source and metadata
            
        Raises:
            ValueError: If position is out of range
        """
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)
        
        if position < 0 or position >= len(notebook.cells):
            raise ValueError(f"Position {position} is out of range (notebook has {len(notebook.cells)} cells)")
            
        line_numbers = self._calculate_line_numbers(notebook)
        cell = notebook.cells[position]
        cell_id = cell['id']
        line_start, line_end = line_numbers[cell_id]
        
        return Cell(
            cell_id=cell_id,
            position=position,
            cell_type=cell['cell_type'],
            source=cell['source'],
            line_start=line_start,
            line_end=line_end,
            execution_count=cell.get('execution_count'),
            has_output=bool(cell.get('outputs'))
        )

    
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
    
    def delete_cell(self, notebook_path: str, cell_id: str) -> dict:
        """Delete a cell from the notebook by its stable ID.
        
        Args:
            notebook_path: Path to the .ipynb file
            cell_id: The stable cell ID to delete
            
        Returns:
            Dictionary with deleted cell info and status
            
        Raises:
            ValueError: If the cell_id does not exist in the notebook
        """
        # Load notebook and ensure cell IDs
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)
        
        # Find the cell by its stable ID and get its position
        target_index = None
        for index, cell in enumerate(notebook.cells):
            if cell['id'] == cell_id:
                target_index = index
                break
        
        if target_index is None:
            raise ValueError(f"Cell with ID '{cell_id}' not found in notebook")
        
        # Safety check: prevent deleting the only cell
        if len(notebook.cells) == 1:
            raise ValueError("Cannot delete the only cell in the notebook")
        
        # Remove the cell
        deleted_cell = notebook.cells.pop(target_index)
        
        # Save notebook
        self._save_notebook(notebook, notebook_path)
        
        # Return result
        return {
            "cell_id": cell_id,
            "original_position": target_index,
            "status": "deleted"
        }
    
    def move_cell(self, notebook_path: str, cell_id: str, new_position: int) -> dict:
        """Move a cell to a different position in the notebook.
        
        Args:
            notebook_path: Path to the .ipynb file
            cell_id: The stable cell ID to move
            new_position: The new position (0-based index)
            
        Returns:
            Dictionary with move info and status
            
        Raises:
            ValueError: If the cell_id does not exist or new_position is invalid
        """
        # Load notebook and ensure cell IDs
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)
        
        # Find the cell by its stable ID and get its current position
        current_position = None
        target_cell = None
        for index, cell in enumerate(notebook.cells):
            if cell['id'] == cell_id:
                current_position = index
                target_cell = cell
                break
        
        if target_cell is None:
            raise ValueError(f"Cell with ID '{cell_id}' not found in notebook")
        
        # Validate new position
        if new_position < 0 or new_position >= len(notebook.cells):
            raise ValueError(f"new_position must be between 0 and {len(notebook.cells) - 1}")
        
        # If position hasn't changed, return early
        if current_position == new_position:
            return {
                "cell_id": cell_id,
                "old_position": current_position,
                "new_position": new_position,
                "status": "no_change"
            }
        
        # Remove cell from current position
        notebook.cells.pop(current_position)
        
        # Insert at new position
        notebook.cells.insert(new_position, target_cell)
        
        # Save notebook
        self._save_notebook(notebook, notebook_path)
        
        # Return result
        return {
            "cell_id": cell_id,
            "old_position": current_position,
            "new_position": new_position,
            "status": "moved"
        }
    
    def reject_edit(self, edit_id: str) -> dict:
        """Reject a pending edit proposal and remove it from pending edits.
        
        Args:
            edit_id: The edit ID to reject
            
        Returns:
            Dictionary with rejected edit info and status
            
        Raises:
            ValueError: If the edit_id does not exist in pending edits
        """
        # Check if edit exists in pending edits
        if edit_id not in self.pending_edits:
            raise ValueError(f"Edit with ID '{edit_id}' not found in pending edits")
        
        # Get the edit details
        cell_edit = self.pending_edits[edit_id]
        
        # Remove from pending edits
        del self.pending_edits[edit_id]
        
        # Update status
        cell_edit.status = "rejected"
        
        # Return result
        return {
            "edit_id": edit_id,
            "cell_id": cell_edit.cell_id,
            "status": "rejected"
        }

    def update_cell_output(
        self,
        notebook_path: str,
        cell_id: str,
        outputs: List[dict],
        execution_count: Optional[int] = None
    ) -> dict:
        """Update the outputs and execution count of a specific cell and save to disk.

        Args:
            notebook_path: Path to the .ipynb file
            cell_id: The stable cell ID to update
            outputs: List of output dictionaries in nbformat format
            execution_count: Optional execution count to set

        Returns:
            Dictionary with cell_id, execution_count, outputs, and status

        Raises:
            ValueError: If the cell_id does not exist in the notebook
        """
        notebook = self._load_notebook(notebook_path)
        self._ensure_cell_ids(notebook)

        target_cell = None
        for cell in notebook.cells:
            if cell['id'] == cell_id:
                target_cell = cell
                break

        if target_cell is None:
            raise ValueError(f"Cell with ID '{cell_id}' not found in notebook")

        target_cell['outputs'] = [
            nbformat.from_dict(o) if isinstance(o, dict) and not isinstance(o, nbformat.NotebookNode) else o
            for o in outputs
        ]
        if execution_count is not None:
            target_cell['execution_count'] = execution_count

        self._save_notebook(notebook, notebook_path)


        return {
            "cell_id": cell_id,
            "execution_count": execution_count,
            "outputs": outputs,
            "status": "updated"
        }
