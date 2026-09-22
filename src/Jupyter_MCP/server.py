#!/usr/bin/env python3
"""
MCP Server for Jupyter Notebook Management
"""

import logging
from mcp.server.fastmcp import FastMCP
from pathlib import Path
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Jupyter_MCP.Notebook.manager import NotebookManager
from Jupyter_MCP.Notebook.diff import generate_diff
from Jupyter_MCP.Notebook.models import Cell, CellEdit

# Create MCP server
mcp = FastMCP("jupyter-mcp")

# Initialize NotebookManager
notebook_manager = NotebookManager()


@mcp.tool()
def list_cells(notebook_path: str) -> list[dict]:
    """List all cells in a Jupyter notebook.
    
    Args:
        notebook_path: Path to the .ipynb file
        
    Returns:
        List of cell objects with metadata
    """
    logger.info(f"list_cells called with notebook_path: {notebook_path}")
    
    try:
        cells = notebook_manager.list_cells(notebook_path)
        logger.info(f"Successfully listed {len(cells)} cells")
        
        # Convert Cell objects to dictionaries for JSON serialization
        cells_dict = [
            {
                "cell_id": cell.cell_id,
                "position": cell.position,
                "cell_type": cell.cell_type,
                "source": cell.source,
                "line_start": cell.line_start,
                "line_end": cell.line_end,
                "execution_count": cell.execution_count,
                "has_output": cell.has_output
            }
            for cell in cells
        ]
        
        return cells_dict
        
    except Exception as e:
        logger.error(f"Error in list_cells: {str(e)}")
        raise


@mcp.tool()
def get_cell(notebook_path: str, cell_id: str) -> dict:
    """Get a specific cell by its stable ID.
    
    Args:
        notebook_path: Path to the .ipynb file
        cell_id: The stable cell ID to retrieve
        
    Returns:
        Cell object with complete source and metadata
    """
    logger.info(f"get_cell called with notebook_path: {notebook_path}, cell_id: {cell_id}")
    
    try:
        cell = notebook_manager.get_cell(notebook_path, cell_id)
        logger.info(f"Successfully retrieved cell {cell_id}")
        
        # Convert Cell object to dictionary for JSON serialization
        cell_dict = {
            "cell_id": cell.cell_id,
            "position": cell.position,
            "cell_type": cell.cell_type,
            "source": cell.source,
            "line_start": cell.line_start,
            "line_end": cell.line_end,
            "execution_count": cell.execution_count,
            "has_output": cell.has_output
        }
        
        return cell_dict
        
    except Exception as e:
        logger.error(f"Error in get_cell: {str(e)}")
        raise


@mcp.tool()
def generate_diff_tool(old_source: str, new_source: str) -> str:
    """Generate a unified diff between two source strings.
    
    Args:
        old_source: The original source code
        new_source: The modified source code
        
    Returns:
        A unified diff string
    """
    logger.info("generate_diff_tool called")
    logger.info(f"Old source length: {len(old_source)} characters")
    logger.info(f"New source length: {len(new_source)} characters")
    
    try:
        diff = generate_diff(old_source, new_source)
        logger.info("Successfully generated diff")
        return diff
        
    except Exception as e:
        logger.error(f"Error in generate_diff_tool: {str(e)}")
        raise


@mcp.tool()
def propose_edit(notebook_path: str, cell_id: str, new_source: str) -> dict:
    """Propose an edit to a cell without modifying the notebook.
    
    Args:
        notebook_path: Path to the .ipynb file
        cell_id: The stable cell ID to edit
        new_source: The proposed new source code
        
    Returns:
        CellEdit object with edit details and status "pending"
    """
    logger.info(f"propose_edit called with notebook_path: {notebook_path}, cell_id: {cell_id}")
    logger.info(f"New source length: {len(new_source)} characters")
    
    try:
        cell_edit = notebook_manager.propose_edit(notebook_path, cell_id, new_source)
        logger.info(f"Successfully proposed edit {cell_edit.edit_id}")
        
        # Convert CellEdit object to dictionary for JSON serialization
        cell_edit_dict = {
            "edit_id": cell_edit.edit_id,
            "notebook_path": cell_edit.notebook_path,
            "cell_id": cell_edit.cell_id,
            "old_source": cell_edit.old_source,
            "new_source": cell_edit.new_source,
            "diff": cell_edit.diff,
            "status": cell_edit.status
        }
        
        return cell_edit_dict
        
    except Exception as e:
        logger.error(f"Error in propose_edit: {str(e)}")
        raise


@mcp.tool()
def edit_cell(notebook_path: str, cell_id: str, new_source: str) -> dict:
    """Directly edit a cell and return the diff.
    
    Args:
        notebook_path: Path to the .ipynb file
        cell_id: The stable cell ID to edit
        new_source: The new source code
        
    Returns:
        Dictionary with edit details and diff
    """
    logger.info(f"edit_cell called with notebook_path: {notebook_path}, cell_id: {cell_id}")
    
    try:
        result = notebook_manager.edit_cell(notebook_path, cell_id, new_source)
        logger.info(f"Successfully edited cell {cell_id}")
        return result
    except Exception as e:
        logger.error(f"Error in edit_cell: {str(e)}")
        raise


@mcp.tool()
def insert_cell(notebook_path: str, position: int, cell_type: str, source: str) -> dict:
    """Insert a new cell at the specified position.
    
    Args:
        notebook_path: Path to the .ipynb file
        position: Position to insert the cell (0-based index)
        cell_type: Type of cell ('code', 'markdown', or 'raw')
        source: The source code/content for the cell
        
    Returns:
        Dictionary with cell_id, position, cell_type, and source
    """
    logger.info(f"insert_cell called with notebook_path: {notebook_path}, position: {position}, cell_type: {cell_type}")
    
    try:
        result = notebook_manager.insert_cell(notebook_path, position, cell_type, source)
        logger.info(f"Successfully inserted cell at position {position}")
        return result
    except Exception as e:
        logger.error(f"Error in insert_cell: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info("Starting Jupyter Notebook Manager MCP Server")
    mcp.run()
