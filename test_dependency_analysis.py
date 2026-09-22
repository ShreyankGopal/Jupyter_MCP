"""
Test script for dependency analysis using sample.ipynb.
Demonstrates the full pipeline: NotebookManager -> MultiCellParser -> DependencyAnalyzer -> BFS
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from Jupyter_MCP.Notebook.manager import NotebookManager
from Jupyter_MCP.Notebook.DependencyAnalyzer.astParser import MultiCellParser
from Jupyter_MCP.Notebook.DependencyAnalyzer.dependency import DependencyAnalyzer


def main():
    """Test the complete dependency analysis pipeline."""
    
    notebook_path = "sample.ipynb"
    
    print("=" * 60)
    print("Dependency Analysis Test Script")
    print("=" * 60)
    
    # Step 1: Load notebook and get cells
    print("\nStep 1: Loading notebook and extracting cells...")
    manager = NotebookManager()
    cells = manager.list_cells(notebook_path)
    print(f"Found {len(cells)} cells in notebook")
    
    # Step 2: Parse cells with MultiCellParser
    print("\nStep 2: Parsing cells with MultiCellParser...")
    multi_parser = MultiCellParser()
    
    # Prepare cell data for MultiCellParser
    cell_data = []
    for cell in cells:
        cell_data.append({
            'cell_id': cell.cell_id,
            'source': cell.source
        })
    
    multi_parser.parse_cells(cell_data)
    print("Cells parsed successfully")
    
    # Show symbols for each cell
    print("\nCell Symbol Analysis:")
    for cell in cells:
        symbols = multi_parser.get_cell_symbols(cell.cell_id)
        if symbols:
            print(f"Cell{cell.position}:")
            print(f"  Store: {symbols['store']}")
            print(f"  Load:  {symbols['load']}")
    
    # Step 3: Build dependency graph
    print("\nStep 3: Building dependency graph...")
    dependency_analyzer = DependencyAnalyzer()
    all_symbols = multi_parser.get_all_symbols()
    dependency_analyzer.build_dependency_graph(all_symbols)
    print("Dependency graph built successfully")
    
    # Step 4: Print dependency graph in requested format
    print("\nStep 4: Dependency Graph (Parent:Child1,Child2,...):")
    graph = dependency_analyzer.get_dependency_graph()
    
    # Create mapping from cell_id to position
    cell_id_to_position = {cell.cell_id: cell.position for cell in cells}
    position_to_cell_id = {cell.position: cell.cell_id for cell in cells}
    
    # Sort by cell position for consistent output
    sorted_cells = sorted(graph.keys(), key=lambda x: cell_id_to_position.get(x, 999))
    
    for cell_id in sorted_cells:
        dependencies = graph[cell_id]
        parent_position = cell_id_to_position[cell_id]
        
        if dependencies:
            # Convert dependencies to positions and sort by position
            dep_positions = sorted([cell_id_to_position[dep_id] for dep_id in dependencies])
            deps_formatted = ",".join([f"Cell{pos}" for pos in dep_positions])
            print(f"Cell{parent_position}:{deps_formatted}")
        else:
            print(f"Cell{parent_position}:")
    
    # Step 5: Test BFS with different scenarios
    print("\nStep 5: Multi-source BFS Scenarios:")
    
    # Scenario 1: Change Cell 1
    print("\nScenario 1: Cell 0 changed")
    downstream = dependency_analyzer.get_downstream_cells([position_to_cell_id[0]])
    downstream_positions = sorted([cell_id_to_position[cell_id] for cell_id in downstream])
    print(f"Cells to re-execute: {[f'Cell{pos}' for pos in downstream_positions]}")
    
    # Scenario 2: Change Cell 2
    print("\nScenario 2: Cell 1 changed")
    downstream = dependency_analyzer.get_downstream_cells([position_to_cell_id[1]])
    downstream_positions = sorted([cell_id_to_position[cell_id] for cell_id in downstream])
    print(f"Cells to re-execute: {[f'Cell{pos}' for pos in downstream_positions]}")
    
    # Scenario 3: Change Cell 3
    print("\nScenario 3: Cell 2 changed")
    downstream = dependency_analyzer.get_downstream_cells([position_to_cell_id[2]])
    downstream_positions = sorted([cell_id_to_position[cell_id] for cell_id in downstream])
    print(f"Cells to re-execute: {[f'Cell{pos}' for pos in downstream_positions]}")
    
    # Scenario 4: Change multiple cells (Cell 1 and Cell 3)
    print("\nScenario 4: Cells 0 and 2 changed")
    downstream = dependency_analyzer.get_downstream_cells([position_to_cell_id[0], position_to_cell_id[2]])
    downstream_positions = sorted([cell_id_to_position[cell_id] for cell_id in downstream])
    print(f"Cells to re-execute: {[f'Cell{pos}' for pos in downstream_positions]}")
    
    # Scenario 5: Change Cell 5 (no downstream dependencies)
    print("\nScenario 5: Cell 4 changed")
    downstream = dependency_analyzer.get_downstream_cells([position_to_cell_id[4]])
    downstream_positions = sorted([cell_id_to_position[cell_id] for cell_id in downstream])
    print(f"Cells to re-execute: {[f'Cell{pos}' for pos in downstream_positions]}")
    
    print("\n" + "=" * 60)
    print("Dependency Analysis Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()