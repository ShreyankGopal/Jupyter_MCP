"""
AST Parser for analyzing Python code snippets.
This module provides functionality to create and analyze Abstract Syntax Trees from code.
"""

import ast
from typing import Optional, Dict, List


class ASTParser:
    """Class for parsing Python code into Abstract Syntax Trees."""
    
    def __init__(self):
        """Initialize the AST parser."""
        self.parser = ast
    
    def create_ast(self, code: str) -> Optional[ast.Module]:
        """
        Create an Abstract Syntax Tree from a code snippet.
        
        Args:
            code: The Python code snippet to parse
            
        Returns:
            AST object if parsing succeeds, None if parsing fails
            
        Raises:
            SyntaxError: If the code has invalid Python syntax
        """
        try:
            tree = self.parser.parse(code)
            return tree
        except SyntaxError as e:
            print(f"Syntax error in code: {e}")
            return None
    
    def validate_syntax(self, code: str) -> bool:
        """
        Validate if the code snippet has valid Python syntax.
        
        Args:
            code: The Python code snippet to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            self.parser.parse(code)
            return True
        except SyntaxError:
            return False
    
    def get_function_names(self, code: str) -> List[str]:
        """
        Extract function names from the code snippet.
        
        Args:
            code: The Python code snippet to analyze
            
        Returns:
            List of function names found in the code
        """
        tree = self.create_ast(code)
        if not tree:
            return []
        
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                function_names.append(node.name)
        
        return function_names
    
    def get_class_names(self, code: str) -> List[str]:
        """
        Extract class names from the code snippet.
        
        Args:
            code: The Python code snippet to analyze
            
        Returns:
            List of class names found in the code
        """
        tree = self.create_ast(code)
        if not tree:
            return []
        
        class_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.append(node.name)
        
        return class_names
    
    def get_global_symbols(self, code: str) -> Dict[str, List[str]]:
        """
        Get global symbols from the code snippet.
        
        Global symbols are top-level names that are defined or imported in the module scope.
        These include:
        - Variable assignments (x = 5, name = "value")
        - Function definitions (def my_func(): pass)
        - Class definitions (class MyClass: pass)
        - Import statements (import math, from os import path)
        - Global declarations (global x)
        
        Args:
            code: The Python code snippet to analyze
            
        Returns:
            Dictionary with categories of global symbols:
            {
                'variables': list of variable names,
                'functions': list of function names,
                'classes': list of class names,
                'imports': list of import statements
            }
        """
        tree = self.create_ast(code)
        if not tree:
            return {
                'variables': [],
                'functions': [],
                'classes': [],
                'imports': []
            }
        
        symbols: Dict[str, List[str]] = {
            'variables': [],
            'functions': [],
            'classes': [],
            'imports': []
        }
        
        for node in ast.walk(tree):
            # Get top-level assignments (module-level variables)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols['variables'].append(target.id)
            
            # Get function definitions
            elif isinstance(node, ast.FunctionDef):
                symbols['functions'].append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols['functions'].append(node.name)
            
            # Get class definitions
            elif isinstance(node, ast.ClassDef):
                symbols['classes'].append(node.name)
            
            # Get import statements
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols['imports'].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ''
                for alias in node.names:
                    symbols['imports'].append(f"from {module} import {alias.name}")
        
        return symbols
    
    def get_store_load_operations(self, code: str) -> Dict[str, List[str]]:
        """
        Get store and load operations for variables, functions, and classes using AST.
        
        Store operations: Operations that create or bind names (assignments, definitions)
        Load operations: Operations that read or use names (references, calls)
        
        Args:
            code: The Python code snippet to analyze
            
        Returns:
            Dictionary with store and load operations:
            {
                'store': list of names that are stored/defined,
                'load': list of names that are loaded/used
            }
        """
        tree = self.create_ast(code)
        if not tree:
            return {
                'store': [],
                'load': []
            }
        
        operations: Dict[str, List[str]] = {
            'store': [],
            'load': []
        }
        
        for node in ast.walk(tree):
            # Store operations - names that are created/bound
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                operations['store'].append(node.id)
            
            # Load operations - names that are read/used
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                operations['load'].append(node.id)
            
            # Function definitions store the function name
            elif isinstance(node, ast.FunctionDef):
                operations['store'].append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                operations['store'].append(node.name)
            
            # Class definitions store the class name
            elif isinstance(node, ast.ClassDef):
                operations['store'].append(node.name)
            
            # Function calls load the function name
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    operations['load'].append(node.func.id)
        
        # Remove duplicates while preserving order
        operations['store'] = list(dict.fromkeys(operations['store']))
        operations['load'] = list(dict.fromkeys(operations['load']))
        
        return operations

###
# parser for multi cell
###
class MultiCellParser:
    """Parser for analyzing multiple notebook cells and tracking dependencies."""
    
    def __init__(self):
        """Initialize the multi-cell parser."""
        self.parser = ASTParser()
        # Dictionary to store cell analysis results: {cell_id: {store: [...], load: [...]}}
        self.symbols: Dict[str, Dict[str, List[str]]] = {}
    
    def parse_cells(self, cell_data: List[Dict[str, str]]) -> None:
        """
        Parse multiple cells and add their symbols to the internal dictionary.
        
        Args:
            cell_data: List of dictionaries with 'cell_id' and 'source' keys
                      Example: [{'cell_id': 'abc123', 'source': 'x = 5'}, ...]
        """
        for cell in cell_data:
            cell_id = cell['cell_id']
            source = cell['source']
            
            # Get store and load operations for this cell
            operations = self.parser.get_store_load_operations(source)
            
            # Store in dictionary keyed by cell_id
            self.symbols[cell_id] = {
                'store': operations['store'],
                'load': operations['load']
            }
    
    def add_cell(self, cell_id: str, source: str) -> None:
        """
        Add a single cell to the analysis.
        
        Args:
            cell_id: The unique identifier for the cell
            source: The source code of the cell
        """
        operations = self.parser.get_store_load_operations(source)
        self.symbols[cell_id] = {
            'store': operations['store'],
            'load': operations['load']
        }
    
    def get_cell_symbols(self, cell_id: str) -> Optional[Dict[str, List[str]]]:
        """
        Get the store/load symbols for a specific cell.
        
        Args:
            cell_id: The cell identifier to look up
            
        Returns:
            Dictionary with 'store' and 'load' lists, or None if cell not found
        """
        return self.symbols.get(cell_id)
    
    def get_all_symbols(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Get all cell symbols.
        
        Returns:
            Dictionary mapping cell_id to their store/load symbols
        """
        return self.symbols
    
    