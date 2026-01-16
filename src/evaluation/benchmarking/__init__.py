"""Benchmarking module.

This module provides benchmarking orchestration and utilities.
"""

# Lazy imports to avoid requiring torch at module level
# Only import CLI functions when actually needed (they require torch)
from .formatting import compare_models, format_results_table
from .orchestrator import benchmark_best_trials
from .utils import run_benchmarking

__all__ = [
    "benchmark_best_trials",
    "benchmark_model",
    "compare_models",
    "format_results_table",
    "run_benchmarking",
]


from typing import Any, Callable


def __getattr__(name: str) -> Callable[..., Any]:
    """Lazy import for CLI functions that require torch."""
    if name == "benchmark_model":
        from .cli import benchmark_model
        return benchmark_model
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")



