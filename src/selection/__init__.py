"""Compatibility shim for selection module.

This module provides backward compatibility by re-exporting from evaluation.selection.

DEPRECATED: Use 'from evaluation.selection import ...' instead.
This shim will be removed in 2 releases.
"""

import sys
import warnings
import importlib
from types import ModuleType
from typing import Any
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_loader

# Make this module act as a package by setting __path__
__path__ = []

# Custom import finder to handle submodule imports
class SelectionSubmoduleFinder(MetaPathFinder):
    """Custom finder for selection.* submodules."""
    
    def find_spec(self, name: str, path: Any, target: Any = None) -> Any:
        if name.startswith('selection.') and name != 'selection':
            # Redirect to evaluation.selection.*
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
_submodules = [
    'selection_logic',
    'mlflow_selection',
    'artifact_acquisition',
    'cache',
    'local_selection',
    'local_selection_v2',
    'disk_loader',
    'trial_finder',
    'study_summary',
    'selection',
]

def _create_submodule_proxy(name: str) -> ModuleType:
    """Create a proxy module for a submodule."""
    try:
        module = importlib.import_module(f'evaluation.selection.{name}')
        return module
    except ImportError:
        return ModuleType(f'selection.{name}')

# Register submodule proxies
_current_module = sys.modules[__name__]
for submodule_name in _submodules:
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
