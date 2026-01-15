"""Compatibility shim for selection module.

This module provides backward compatibility by re-exporting from evaluation.selection.

DEPRECATED: Use 'from evaluation.selection import ...' instead.
This shim will be removed in 2 releases.

Note: This module contains unique logic in:
- selection.py: AzureML sweep job selection (not a wrapper)
- selection_logic.py: Selection algorithm logic (not a wrapper)
- types.py: Type definitions used by selection modules

All other submodules are proxied to evaluation.selection.* equivalents.
"""

import sys
import warnings
import importlib
from types import ModuleType
from typing import Any
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_loader

# Make this module act as a package by setting __path__
# Include the directory containing selection modules so local wrapper files can be found
from pathlib import Path
__path__ = [str(Path(__file__).parent)]

# Custom import finder to handle submodule imports
class SelectionSubmoduleFinder(MetaPathFinder):
    """Custom finder for selection.* submodules."""
    
    def find_spec(self, name: str, path: Any, target: Any = None) -> Any:
        if name.startswith('selection.') and name != 'selection':
            # First check if a local file exists (for wrapper modules)
            # This allows wrapper files in selection/ to take precedence over proxy
            try:
                from pathlib import Path
                submodule_file = name.replace('selection.', 'selection/').replace('.', '/') + '.py'
                local_file = Path(__file__).parent / submodule_file.split('/', 1)[1]
                if local_file.exists():
                    # Local file exists, let Python's normal import handle it
                    return None
            except Exception:
                pass
            
            # No local file, redirect to evaluation.selection.*
            submodule_name = name.replace('selection.', 'evaluation.selection.', 1)
            try:
                # Try to import the actual module
                spec = importlib.util.find_spec(submodule_name)
                if spec is not None and spec.loader is not None:
                    # Create a loader that loads from evaluation.selection
                    loader = importlib.util.LazyLoader(spec.loader)
                    return spec_from_loader(name, loader)
            except (ImportError, ValueError):
                pass
        return None

# Install the finder if not already installed
_finder_installed = False
for finder in sys.meta_path:
    if isinstance(finder, SelectionSubmoduleFinder):
        _finder_installed = True
        break

if not _finder_installed:
    sys.meta_path.insert(0, SelectionSubmoduleFinder())

# Create submodule proxies for backward compatibility
# Note: selection.py and selection_logic.py contain unique logic (not wrappers) and are kept.
# All other submodules are proxied to evaluation.selection.*
_submodules = [
    'selection_logic',  # Unique logic - kept
    'selection',  # Unique AzureML logic - kept
    # Deprecated wrapper modules removed - now proxied to evaluation.selection.*
    'artifact_acquisition',
    'cache',
    'local_selection',
    'local_selection_v2',
    'disk_loader',
    'trial_finder',
    'study_summary',
    'mlflow_selection',
]

def _create_submodule_proxy(name: str) -> ModuleType:
    """Create a proxy module for a submodule."""
    # Check if a local wrapper file exists first
    try:
        from pathlib import Path
        local_file = Path(__file__).parent / f"{name}.py"
        if local_file.exists():
            # Local wrapper file exists, import it instead of proxying
            try:
                module = importlib.import_module(f'selection.{name}')
                return module
            except ImportError:
                pass
    except Exception:
        pass
    
    # No local file, proxy to evaluation.selection
    try:
        module = importlib.import_module(f'evaluation.selection.{name}')
        return module
    except ImportError:
        return ModuleType(f'selection.{name}')

# Register submodule proxies (only for modules without local wrapper files)
_current_module = sys.modules[__name__]
for submodule_name in _submodules:
    # Check if local wrapper file exists
    from pathlib import Path
    local_file = Path(__file__).parent / f"{submodule_name}.py"
    if local_file.exists():
        # Local wrapper exists - don't pre-register proxy, let it load naturally
        # But still set attribute for backward compatibility
        try:
            # Try to import the local module
            submodule = importlib.import_module(f'selection.{submodule_name}')
            sys.modules[f'selection.{submodule_name}'] = submodule
            setattr(_current_module, submodule_name, submodule)
        except ImportError:
            # If import fails, fall back to proxy
            submodule = _create_submodule_proxy(submodule_name)
            sys.modules[f'selection.{submodule_name}'] = submodule
            setattr(_current_module, submodule_name, submodule)
    else:
        # No local file, create proxy
        submodule = _create_submodule_proxy(submodule_name)
        sys.modules[f'selection.{submodule_name}'] = submodule
        setattr(_current_module, submodule_name, submodule)

warnings.warn(
    "selection is deprecated, use evaluation.selection instead. "
    "This shim will be removed in 2 releases.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from evaluation.selection
from evaluation.selection import *  # noqa: F403, F401
