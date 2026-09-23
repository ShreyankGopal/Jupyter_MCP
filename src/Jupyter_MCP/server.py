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
from Jupyter_MCP.Notebook.DependencyAnalyzer.astParser import MultiCellParser
from Jupyter_MCP.Notebook.DependencyAnalyzer.dependency import DependencyAnalyzer
from Jupyter_MCP.KernelManager.manager import KernelManager
from Jupyter_MCP.KernelManager.Registry import KernelRegistry 
# Create MCP server
mcp = FastMCP("jupyter-mcp")

# Initialize NotebookManager
notebook_manager = NotebookManager()

# Initialize dependency analyzers
multi_cell_parser = MultiCellParser()
dependency_analyzer = DependencyAnalyzer()

# Initialize KernelManager
kernel_manager = KernelManager()
kernel_registry = KernelRegistry()
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


@mcp.tool()
def analyze_dependencies(notebook_path: str) -> dict:
    """Analyze dependencies between cells in a notebook.
    
    Args:
        notebook_path: Path to the .ipynb file
        
    Returns:
        Dictionary with dependency graph using cell positions
        Format: {"Cell0": ["Cell1", "Cell2"], "Cell1": ["Cell3"], ...}
    """
    logger.info(f"analyze_dependencies called with notebook_path: {notebook_path}")
    
    try:
        # Get cells from notebook
        cells = notebook_manager.list_cells(notebook_path)
        
        # Prepare cell data for MultiCellParser
        cell_data = [{'cell_id': cell.cell_id, 'source': cell.source} for cell in cells]
        
        # Parse cells to get symbols
        multi_cell_parser.parse_cells(cell_data)
        all_symbols = multi_cell_parser.get_all_symbols()
        
        # Build dependency graph
        dependency_analyzer.build_dependency_graph(all_symbols)
        graph = dependency_analyzer.get_dependency_graph()
        
        # Convert to position-based format for easier understanding
        cell_id_to_position = {cell.cell_id: cell.position for cell in cells}
        position_based_graph = {}
        
        for cell_id, dependencies in graph.items():
            position = cell_id_to_position[cell_id]
            dep_positions = sorted([cell_id_to_position[dep_id] for dep_id in dependencies])
            position_based_graph[f"Cell{position}"] = [f"Cell{pos}" for pos in dep_positions]
        
        logger.info("Successfully analyzed dependencies")
        return position_based_graph
        
    except Exception as e:
        logger.error(f"Error in analyze_dependencies: {str(e)}")
        raise


@mcp.tool()
def get_downstream_cells(notebook_path: str, changed_positions: list[int]) -> list[str]:
    """Get cells that need re-execution using multi-source BFS.
    
    Args:
        notebook_path: Path to the .ipynb file
        changed_positions: List of cell positions that were changed (0-based)
        
    Returns:
        List of cell positions that need re-execution, in execution order
    """
    logger.info(f"get_downstream_cells called with notebook_path: {notebook_path}, changed_positions: {changed_positions}")
    
    try:
        # Get cells from notebook
        cells = notebook_manager.list_cells(notebook_path)
        
        # Build position to cell_id mapping
        position_to_cell_id = {cell.position: cell.cell_id for cell in cells}
        cell_id_to_position = {cell.cell_id: cell.position for cell in cells}
        
        # Parse cells and build dependency graph
        cell_data = [{'cell_id': cell.cell_id, 'source': cell.source} for cell in cells]
        multi_cell_parser.parse_cells(cell_data)
        all_symbols = multi_cell_parser.get_all_symbols()
        dependency_analyzer.build_dependency_graph(all_symbols)
        
        # Convert positions to cell_ids
        changed_cell_ids = [position_to_cell_id[pos] for pos in changed_positions if pos in position_to_cell_id]
        
        # Get downstream cells using BFS
        downstream_cell_ids = dependency_analyzer.get_downstream_cells(changed_cell_ids)
        
        # Convert back to positions and sort
        downstream_positions = sorted([cell_id_to_position[cell_id] for cell_id in downstream_cell_ids])
        
        logger.info(f"Found {len(downstream_positions)} downstream cells")
        return downstream_positions
        
    except Exception as e:
        logger.error(f"Error in get_downstream_cells: {str(e)}")
        raise


@mcp.tool()
def get_upstream_cells(notebook_path: str, position: int) -> list[int]:
    """Get cells that the given cell depends on.
    
    Args:
        notebook_path: Path to the .ipynb file
        position: Position of the cell to analyze (0-based)
        
    Returns:
        List of cell positions that this cell depends on
    """
    logger.info(f"get_upstream_cells called with notebook_path: {notebook_path}, position: {position}")
    
    try:
        # Get cells from notebook
        cells = notebook_manager.list_cells(notebook_path)
        
        # Build position to cell_id mapping
        position_to_cell_id = {cell.position: cell.cell_id for cell in cells}
        cell_id_to_position = {cell.cell_id: cell.position for cell in cells}
        
        # Parse cells and build dependency graph
        cell_data = [{'cell_id': cell.cell_id, 'source': cell.source} for cell in cells]
        multi_cell_parser.parse_cells(cell_data)
        all_symbols = multi_cell_parser.get_all_symbols()
        dependency_analyzer.build_dependency_graph(all_symbols)
        
        # Get upstream dependencies
        if position not in position_to_cell_id:
            raise ValueError(f"Position {position} not found in notebook")
        
        cell_id = position_to_cell_id[position]
        upstream_cell_ids = dependency_analyzer.get_upstream_cells(cell_id)
        
        # Convert to positions and sort
        upstream_positions = sorted([cell_id_to_position[cell_id] for cell_id in upstream_cell_ids])
        
        logger.info(f"Found {len(upstream_positions)} upstream cells")
        return upstream_positions
        
    except Exception as e:
        logger.error(f"Error in get_upstream_cells: {str(e)}")
        raise


@mcp.tool()
def delete_cell(notebook_path: str, cell_id: str) -> dict:
    """Delete a cell from the notebook by its stable ID.
    
    Args:
        notebook_path: Path to the .ipynb file
        cell_id: The stable cell ID to delete
        
    Returns:
        Dictionary with deleted cell info and status
    """
    logger.info(f"delete_cell called with notebook_path: {notebook_path}, cell_id: {cell_id}")
    
    try:
        result = notebook_manager.delete_cell(notebook_path, cell_id)
        logger.info(f"Successfully deleted cell {cell_id}")
        return result
    except Exception as e:
        logger.error(f"Error in delete_cell: {str(e)}")
        raise


@mcp.tool()
def move_cell(notebook_path: str, cell_id: str, new_position: int) -> dict:
    """Move a cell to a different position in the notebook.
    
    Args:
        notebook_path: Path to the .ipynb file
        cell_id: The stable cell ID to move
        new_position: The new position (0-based index)
        
    Returns:
        Dictionary with move info and status
    """
    logger.info(f"move_cell called with notebook_path: {notebook_path}, cell_id: {cell_id}, new_position: {new_position}")
    
    try:
        result = notebook_manager.move_cell(notebook_path, cell_id, new_position)
        logger.info(f"Successfully moved cell {cell_id} to position {new_position}")
        return result
    except Exception as e:
        logger.error(f"Error in move_cell: {str(e)}")
        raise


@mcp.tool()
def reject_edit(edit_id: str) -> dict:
    """Reject a pending edit proposal and remove it from pending edits.
    
    Args:
        edit_id: The edit ID to reject
        
    Returns:
        Dictionary with rejected edit info and status
    """
    logger.info(f"reject_edit called with edit_id: {edit_id}")
    
    try:
        result = notebook_manager.reject_edit(edit_id)
        logger.info(f"Successfully rejected edit {edit_id}")
        return result
    except Exception as e:
        logger.error(f"Error in reject_edit: {str(e)}")
        raise


#########################################################
#  MCP Tool for kernel management
#########################################################

@mcp.tool()
def start_kernel(Notebook_Path: str, kernel_name: str = "python3") -> dict:
    """Start a Jupyter kernel.
    
    Args:
        kernel_name: Name of the kernel to start (default: "python3")
        
    Returns:
        Dictionary with kernel info and status
    """
    logger.info(f"start_kernel called with kernel_name: {kernel_name}")
    
    try:
        result = kernel_registry.start_kernel(notebook_path=Notebook_Path, kernel_name=kernel_name)
        logger.info(f"Successfully started kernel {result['kernel_id']}")
        return result
    except Exception as e:
        logger.error(f"Error in start_kernel: {str(e)}")
        raise

@mcp.tool()
def stop_kernel(Notebook_Path: str) -> dict:
    """Stop the currently running Jupyter kernel.
    
    Returns:
        Dictionary with stop info and status
    """
    logger.info("stop_kernel called")
    
    try:
        result = kernel_registry.stop_kernel(notebook_path=Notebook_Path)
        logger.info(f"Successfully stopped kernel {result['kernel_id']}")
        return result
    except Exception as e:
        logger.error(f"Error in stop_kernel: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting Jupyter Notebook Manager MCP Server")
    mcp.run()
