"""Compatibility shim for benchmarking module.

This module provides backward compatibility by re-exporting from evaluation.benchmarking.

DEPRECATED: Use 'from evaluation.benchmarking import ...' instead.
This shim will be removed in 2 releases.
"""

import sys
import warnings
import importlib
from types import ModuleType
from importlib.abc import MetaPathFinder
from importlib.util import spec_from_loader

# Make this module act as a package by setting __path__
__path__ = []

# Custom import finder to handle submodule imports
class BenchmarkingSubmoduleFinder(MetaPathFinder):
    """Custom finder for benchmarking.* submodules."""
    
    def find_spec(self, name, path, target=None):
        if name.startswith('benchmarking.') and name != 'benchmarking':
            # Redirect to evaluation.benchmarking.*
            submodule_name = name.replace('benchmarking.', 'evaluation.benchmarking.', 1)
            try:
                spec = importlib.util.find_spec(submodule_name)
                if spec is not None:
                    loader = importlib.util.LazyLoader(spec.loader)
                    return spec_from_loader(name, loader)
            except (ImportError, ValueError):
                pass
        return None

# Install the finder if not already installed
_finder_installed = False
for finder in sys.meta_path:
    if isinstance(finder, BenchmarkingSubmoduleFinder):
        _finder_installed = True
        break

if not _finder_installed:
    sys.meta_path.insert(0, BenchmarkingSubmoduleFinder())

# Create submodule proxies for backward compatibility
_submodules = [
    'orchestrator',
    'utils',
    'cli',
    'data_loader',
    'execution',
    'model_loader',
    'statistics',
    'formatting',
]

def _create_submodule_proxy(name: str) -> ModuleType:
    """Create a proxy module for a submodule."""
    try:
        module = importlib.import_module(f'evaluation.benchmarking.{name}')
        return module
    except ImportError:
        return ModuleType(f'benchmarking.{name}')

# Register submodule proxies
_current_module = sys.modules[__name__]
for submodule_name in _submodules:
    submodule = _create_submodule_proxy(submodule_name)
    sys.modules[f'benchmarking.{submodule_name}'] = submodule
    setattr(_current_module, submodule_name, submodule)

warnings.warn(
    "benchmarking is deprecated, use evaluation.benchmarking instead. "
    "This shim will be removed in 2 releases.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from evaluation.benchmarking
from evaluation.benchmarking import *  # noqa: F403, F401
