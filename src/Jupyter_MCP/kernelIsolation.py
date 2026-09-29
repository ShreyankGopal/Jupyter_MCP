"""
Script to demonstrate that MCP tools only do file I/O, no kernel interaction.
This script changes the second cell from print(x) to print(x+5) using the NotebookManager.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Jupyter_MCP.Notebook.manager import NotebookManager

def change_second_cell():
    """Change the second cell from print(x) to print(x+5)."""
    
    notebook_path = "sample.ipynb"
    
    # Initialize manager
    manager = NotebookManager()
    
    # List cells to find the second cell
    cells = manager.list_cells(notebook_path)
    print(f"Found {len(cells)} cells in notebook")
    
    # Find the second cell (position 1)
    second_cell = None
    for cell in cells:
        if cell.position == 1:
            second_cell = cell
            break
    
    if second_cell:
        print(f"Second cell found: {second_cell.cell_id}")
        print(f"Current source: {second_cell.source}")
        
        # Change the second cell from print(x) to print(x+5)
        result = manager.edit_cell(
            notebook_path=notebook_path,
            cell_id=second_cell.cell_id,
            new_source="print(x+10)"
        )
        
        print(f"Edit status: {result['status']}")
        print(f"Diff: {result['diff']}")
        print("✓ Successfully changed second cell from print(x) to print(x+5)")
        
        # Verify the change
        updated_cell = manager.get_cell(notebook_path, second_cell.cell_id)
        print(f"Updated source: {updated_cell.source}")
        
    else:
        print("Second cell not found")

if __name__ == "__main__":
    print("Changing second cell from print(x) to print(x+5)...\n")
    change_second_cell()