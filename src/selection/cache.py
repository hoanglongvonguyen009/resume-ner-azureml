from __future__ import annotations

"""
@meta
name: cache
type: utility
domain: selection
responsibility:
  - Cache management for best model selection
  - Validate cached selections against MLflow runs
  - Save and load selection cache with dual strategy
inputs:
  - Best model selection results
  - MLflow experiment IDs
  - Selection and tags configuration
outputs:
  - Cached selection data
  - Cache validation status
tags:
  - utility
  - selection
  - cache
  - caching
  - mlflow
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Cache management for best model selection with validation.

DEPRECATED: This module is a backward-compatibility wrapper around
`evaluation.selection.cache`. Use `evaluation.selection.cache`
directly for new code.

This module will be removed in a future release.
"""

import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .types import CacheData, BestModelInfo

# Import from SSOT
from evaluation.selection import cache as _eval_cache

# Re-export constants for backward compatibility
RUN_ID_DISPLAY_LENGTH = 12
HASH_LENGTH = 16


def load_cached_best_model(
    root_dir: Path,
    config_dir: Path,
    experiment_name: str,
    selection_config: Dict[str, Any],
    tags_config: Dict[str, Any],
    benchmark_experiment_id: str,
    tracking_uri: Optional[str] = None,
) -> Optional[CacheData]:
    """
    Load cached best model selection if available and valid.

    DEPRECATED: Use `evaluation.selection.cache.load_cached_best_model`
    directly instead.

    Respects run.mode from selection_config:
    - "force_new": Always returns None (skip cache)
    - "reuse_if_exists": Loads cache if available and valid (default)

    Validates:
    1. Run mode allows cache reuse
    2. Cache key matches current configs
    3. MLflow run still exists and is FINISHED
    4. Cache is not stale (optional: check benchmark run timestamps)

    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        experiment_name: Name of the experiment.
        selection_config: Selection configuration dict.
        tags_config: Tags configuration dict.
        benchmark_experiment_id: MLflow experiment ID for benchmark runs.
        tracking_uri: Optional MLflow tracking URI.

    Returns:
        CacheData dict if valid, None otherwise.
    """
    warnings.warn(
        "selection.cache is deprecated. "
        "Use evaluation.selection.cache instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )

    result = _eval_cache.load_cached_best_model(
        root_dir=root_dir,
        config_dir=config_dir,
        experiment_name=experiment_name,
        selection_config=selection_config,
        tags_config=tags_config,
        benchmark_experiment_id=benchmark_experiment_id,
        tracking_uri=tracking_uri,
    )

    # Convert return type from Dict[str, Any] to CacheData TypedDict
    if result is None:
        return None

    return CacheData(**result)  # type: ignore[arg-type]


def save_best_model_cache(
    root_dir: Path,
    config_dir: Path,
    best_model: BestModelInfo,
    experiment_name: str,
    selection_config: Dict[str, Any],
    tags_config: Dict[str, Any],
    benchmark_experiment: Dict[str, str],
    hpo_experiments: Dict[str, Dict[str, str]],
    tracking_uri: Optional[str] = None,
    inputs_summary: Optional[Dict[str, Any]] = None,
) -> Tuple[Path, Path, Path]:
    """
    Save best model selection to cache using dual strategy.

    DEPRECATED: Use `evaluation.selection.cache.save_best_model_cache`
    directly instead.

    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        best_model: Best model dict from find_best_model_from_mlflow.
        experiment_name: Name of the experiment.
        selection_config: Selection configuration dict.
        tags_config: Tags configuration dict.
        benchmark_experiment: Dict with 'name' and 'id' of benchmark experiment.
        hpo_experiments: Dict mapping backbone -> experiment info (name, id).
        tracking_uri: Optional MLflow tracking URI.
        inputs_summary: Optional summary of inputs (n_benchmark_runs_considered, n_candidates).

    Returns:
        Tuple of (timestamped_file, latest_file, index_file) paths.
    """
    warnings.warn(
        "selection.cache is deprecated. "
        "Use evaluation.selection.cache instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Convert BestModelInfo TypedDict to Dict[str, Any] for evaluation version
    best_model_dict: Dict[str, Any] = dict(best_model)  # type: ignore[arg-type]

    return _eval_cache.save_best_model_cache(
        root_dir=root_dir,
        config_dir=config_dir,
        best_model=best_model_dict,
        experiment_name=experiment_name,
        selection_config=selection_config,
        tags_config=tags_config,
        benchmark_experiment=benchmark_experiment,
        hpo_experiments=hpo_experiments,
        tracking_uri=tracking_uri,
        inputs_summary=inputs_summary,
    )
