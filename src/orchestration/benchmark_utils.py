"""Legacy facade for benchmark_utils module.

This module provides backward compatibility by re-exporting from evaluation.benchmarking.utils.
All imports from this module are deprecated.
"""

import warnings
from evaluation.benchmarking.utils import run_benchmarking

__all__ = [
    "run_benchmarking",
]

# Issue deprecation warning
warnings.warn(
    "Importing 'benchmark_utils' from 'orchestration' is deprecated. "
    "Please import from 'evaluation.benchmarking.utils' instead.",
    DeprecationWarning,
    stacklevel=2
)
