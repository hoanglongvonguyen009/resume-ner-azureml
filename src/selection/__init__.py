"""Selection package.

This package contains selection modules for configuration selection.
Active submodules:
- selection.selection: AzureML sweep job selection
- selection.selection_logic: Selection algorithm logic
- selection.types: Type definitions

Note: Direct imports from this package are deprecated. Use specific submodules or evaluation.selection instead.
"""

# Make this module act as a package by setting __path__
from pathlib import Path
__path__ = [str(Path(__file__).parent)]

# Minimal package structure - submodules contain active logic
__all__ = []
