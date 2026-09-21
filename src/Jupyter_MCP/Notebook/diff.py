import difflib


def generate_diff(old_source: str, new_source: str) -> str:
    """Generate a unified diff between two strings.
    
    Args:
        old_source: The original source code
        new_source: The modified source code
        
    Returns:
        A unified diff string in standard format
    """
    old_lines = old_source.splitlines(keepends=True)
    new_lines = new_source.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="before",
        tofile="after",
        lineterm=""
    )
    
    return "".join(diff)
