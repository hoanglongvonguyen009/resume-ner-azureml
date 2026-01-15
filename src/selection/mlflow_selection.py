from __future__ import annotations

"""
@meta
name: mlflow_selection
type: utility
domain: selection
responsibility:
  - MLflow-based best model selection from benchmark and training runs
  - Join benchmark runs with training runs using hash-based matching
  - Compute composite scores (F1 + latency)
inputs:
  - Benchmark experiment (name, id)
  - HPO experiments (backbone -> experiment info)
  - Tags configuration
  - Selection configuration
outputs:
  - Best model information dictionary
tags:
  - utility
  - selection
  - mlflow
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: true
lifecycle:
  status: active
"""

"""MLflow-based best model selection from benchmark and training runs.

DEPRECATED: This module is a backward-compatibility wrapper around
`evaluation.selection.mlflow_selection`. Use `evaluation.selection.mlflow_selection`
directly for new code.

This module will be removed in a future release.
"""

import warnings
from typing import Any, Dict, Optional, Union

from infrastructure.naming.mlflow.tags_registry import TagsRegistry

from .types import BestModelInfo

# Import from SSOT
from evaluation.selection import mlflow_selection as _eval_mlflow_selection

# Re-export constants for backward compatibility
# Note: evaluation version uses different constant names
MAX_BENCHMARK_RUNS = 2000  # Maps to DEFAULT_MLFLOW_MAX_RESULTS
MAX_HPO_RUNS = 5000  # Maps to LARGE_MLFLOW_MAX_RESULTS


def find_best_model_from_mlflow(
    benchmark_experiment: Dict[str, str],
    hpo_experiments: Dict[str, Dict[str, str]],
    tags_config: Union[TagsRegistry, Dict[str, Any]],
    selection_config: Dict[str, Any],
    use_python_filtering: bool = True,
) -> Optional[BestModelInfo]:
    """
    Find best model by joining benchmark runs with training (refit) runs.

    DEPRECATED: Use `evaluation.selection.mlflow_selection.find_best_model_from_mlflow`
    directly instead.

    This function is a backward-compatibility wrapper that:
    - Handles the `use_python_filtering` parameter (ignored - evaluation version always uses Python filtering)
    - Converts non-optional `benchmark_experiment` to optional for evaluation version
    - Converts return type from `Dict[str, Any]` to `BestModelInfo` TypedDict

    Args:
        benchmark_experiment: Dict with 'name' and 'id' of benchmark experiment
        hpo_experiments: Dict mapping backbone -> experiment info (name, id)
        tags_config: TagsRegistry or Dict with tags configuration (for backward compatibility)
        selection_config: Selection configuration
        use_python_filtering: If True, fetch all runs and filter in Python (deprecated - always True)

    Returns:
        BestModelInfo dict with best run info or None if no matches found
    """
    warnings.warn(
        "selection.mlflow_selection is deprecated. "
        "Use evaluation.selection.mlflow_selection instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Note: use_python_filtering parameter is ignored - evaluation version always uses Python filtering
    # via infrastructure.tracking.mlflow.queries.query_runs_by_tags()

    # Call evaluation version (benchmark_experiment is Optional there, but we have non-optional)
    result = _eval_mlflow_selection.find_best_model_from_mlflow(
        benchmark_experiment=benchmark_experiment,  # type: ignore[arg-type]
        hpo_experiments=hpo_experiments,
        tags_config=tags_config,
        selection_config=selection_config,
    )

    # Convert return type from Dict[str, Any] to BestModelInfo TypedDict
    # Runtime: both are dicts, so this is just a type cast
    if result is None:
        return None

    # Type cast: evaluation version returns Dict[str, Any] but structure matches BestModelInfo
    return BestModelInfo(**result)  # type: ignore[arg-type]
