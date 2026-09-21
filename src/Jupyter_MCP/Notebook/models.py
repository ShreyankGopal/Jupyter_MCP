from dataclasses import dataclass
from typing import Optional


@dataclass
class Cell:
    """Represents a single cell in a Jupyter notebook."""
    cell_id: str
    position: int
    cell_type: str
    source: str
    line_start: int
    line_end: int
    execution_count: Optional[int] = None
    has_output: bool = False


@dataclass
class CellEdit:
    """Represents a proposed cell modification."""
    edit_id: str
    notebook_path: str
    cell_id: str
    old_source: str
    new_source: str
    diff: str
    status: str  # "pending", "applied", "rejected"
