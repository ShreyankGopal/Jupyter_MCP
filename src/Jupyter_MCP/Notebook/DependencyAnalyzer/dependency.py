"""
Dependency analysis for notebook cells.
Builds dependency graphs and performs multi-source BFS to find cells that need re-execution.
"""

from typing import Dict, List, Set
from collections import deque


class DependencyAnalyzer:
    """Analyzes dependencies between notebook cells and finds cells needing re-execution."""
    
    def __init__(self):
        """Initialize the dependency analyzer."""
        # Adjacency list for dependency graph: {cell_id: [dependent_cell_ids]}
        # If cell B depends on cell A, then graph[A] = [B]
        self.dependency_graph: Dict[str, List[str]] = {}
        # Reverse mapping for finding dependencies: {cell_id: [cells_this_depends_on]}
        self.reverse_dependencies: Dict[str, List[str]] = {}
    
    def build_dependency_graph(self, cell_symbols: Dict[str, Dict[str, List[str]]]) -> None:
        """
        Build the dependency graph from cell symbol analysis.
        
        For each cell, determine which other cells it depends on based on symbol usage.
        If cell B depends on cell A (B uses symbols stored in A), create edge A -> B.
        This means if A changes, B needs to be re-executed.
        
        Args:
            cell_symbols: Dictionary mapping cell_id to their store/load symbols
                         {cell_id: {'store': [...], 'load': [...]}}
        """
        self.dependency_graph = {}
        self.reverse_dependencies = {}
        
        # Initialize graph with all cells
        for cell_id in cell_symbols.keys():
            self.dependency_graph[cell_id] = []
            self.reverse_dependencies[cell_id] = []
        
        # Build dependencies based on symbol usage
        for cell_id, symbols in cell_symbols.items():
            load_symbols = set(symbols['load'])
            
            # Find which cells this cell depends on
            for other_cell_id, other_symbols in cell_symbols.items():
                if other_cell_id == cell_id:
                    continue
                
                other_store_symbols = set(other_symbols['store'])
                
                # If this cell loads symbols that other cell stores, it depends on other cell
                if load_symbols & other_store_symbols:  # Intersection of symbols
                    # Create edge: other_cell -> cell_id
                    # (if other_cell changes, cell_id needs re-execution)
                    if other_cell_id not in self.dependency_graph:
                        self.dependency_graph[other_cell_id] = []
                    if cell_id not in self.dependency_graph:
                        self.dependency_graph[cell_id] = []
                        
                    self.dependency_graph[other_cell_id].append(cell_id)
                    self.reverse_dependencies[cell_id].append(other_cell_id)
    
    def get_downstream_cells(self, changed_cells: List[str]) -> List[str]:
        """
        Perform multi-source BFS to find all cells that need re-execution.
        
        Given a list of changed cells, find all downstream cells that depend on them.
        Uses BFS instead of DFS for layer-by-layer execution order.
        
        Args:
            changed_cells: List of cell_ids that were modified
            
        Returns:
            List of cell_ids that need to be re-executed, in execution order
        """
        if not changed_cells:
            return []
        
        # Multi-source BFS queue
        queue = deque(changed_cells)
        visited: Set[str] = set(changed_cells)  # Mark changed cells as visited
        execution_order: List[str] = []
        
        while queue:
            current_cell = queue.popleft()
            
            # Add to execution order (excluding the initial changed cells)
            if current_cell not in changed_cells:
                execution_order.append(current_cell)
            
            # Add all downstream cells to queue
            if current_cell in self.dependency_graph:
                for dependent_cell in self.dependency_graph[current_cell]:
                    if dependent_cell not in visited:
                        visited.add(dependent_cell)
                        queue.append(dependent_cell)
        
        return execution_order
    
    def get_upstream_cells(self, cell_id: str) -> List[str]:
        """
        Find all cells that the given cell depends on (upstream dependencies).
        
        Args:
            cell_id: The cell to analyze
            
        Returns:
            List of cell_ids that this cell depends on
        """
        if cell_id not in self.reverse_dependencies:
            return []
        
        return self.reverse_dependencies[cell_id].copy()
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get the current dependency graph.
        
        Returns:
            Dictionary mapping cell_id to list of dependent cell_ids
        """
        return self.dependency_graph
    
    def clear_graph(self) -> None:
        """Clear the dependency graph."""
        self.dependency_graph = {}
        self.reverse_dependencies = {}