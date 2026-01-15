from __future__ import annotations

"""
@meta
name: disk_loader
type: utility
domain: selection
responsibility:
  - Load trial data from disk-based HPO outputs
  - Read metrics and benchmark data from trial directories
  - Support v2 path structures
inputs:
  - HPO output directories
  - Trial directories
  - Metrics and benchmark JSON files
outputs:
  - Trial information dictionaries
tags:
  - utility
  - selection
  - disk-io
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Load trial data from disk-based HPO outputs.

DEPRECATED: This module is a backward-compatibility wrapper around
`evaluation.selection.disk_loader`. Use `evaluation.selection.disk_loader`
directly for new code.

This module will be removed in a future release.

This module provides utilities to read metrics.json, benchmark.json, and
trial_meta.json files from trial directories on disk.
"""

import warnings
from pathlib import Path
from typing import Optional

from .types import TrialInfo

# Import from SSOT
from evaluation.selection import disk_loader as _eval_disk_loader


def load_benchmark_speed_score(trial_dir: Path) -> Optional[float]:
    """
    Load speed score from benchmark.json if available.

    DEPRECATED: Use `evaluation.selection.disk_loader.load_benchmark_speed_score`
    directly instead.

    Args:
        trial_dir: Path to trial directory containing benchmark.json.

    Returns:
        Latency in milliseconds (batch_size=1 mean), or None if not available.
    """
    warnings.warn(
        "selection.disk_loader is deprecated. "
        "Use evaluation.selection.disk_loader instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_disk_loader.load_benchmark_speed_score(trial_dir=trial_dir)


def load_best_trial_from_disk(
    hpo_output_dir: Path,
    backbone: str,
    objective_metric: str = "macro-f1",
) -> Optional[TrialInfo]:
    """
    Load best trial configuration from saved HPO outputs on disk.

    DEPRECATED: Use `evaluation.selection.disk_loader.load_best_trial_from_disk`
    directly instead.

    Works by reading metrics.json files from trial directories.
    This allows selection even after notebook restart.

    Supports v2 paths (study-{study8}/trial-{trial8}) only.

    Args:
        hpo_output_dir: Path to HPO outputs directory (e.g., outputs/hpo).
        backbone: Model backbone name.
        objective_metric: Name of the objective metric to optimize.

    Returns:
        TrialInfo dict with best trial info, or None if no trials found.
    """
    warnings.warn(
        "selection.disk_loader is deprecated. "
        "Use evaluation.selection.disk_loader instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    result = _eval_disk_loader.load_best_trial_from_disk(
        hpo_output_dir=hpo_output_dir,
        backbone=backbone,
        objective_metric=objective_metric,
    )
    
    # Convert return type from Dict[str, Any] to TrialInfo TypedDict
    if result is None:
        return None
    
    return TrialInfo(**result)  # type: ignore[arg-type]
