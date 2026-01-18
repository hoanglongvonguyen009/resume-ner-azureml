"""Main sweep module - refactored to use extracted modules.

**Migration Status**: IN PROGRESS

This module wraps `sweep_original.py` to maintain backward compatibility while
incremental refactoring extracts functionality into focused submodules.

**Migration Plan**:
- Extract objective function creation logic
- Extract sweep execution orchestration
- Extract tagging logic
- Once extraction is complete, remove `sweep_original.py` and update this module

**Current State**:
- Functions are re-exported from `sweep_original.py` via wrapper pattern
- Top-level `sweep.py` also maintains backward compatibility
- Both wrapper files will be consolidated once migration is complete

**See**: `MASTER-20260118-1608-consolidate-remaining-dry-violations-src-unified.plan.md`
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)

# Import original functions for now (will be refactored incrementally)
# This maintains backward compatibility while we extract modules
# TODO: Complete migration - extract functions into focused modules and remove sweep_original.py
from training.hpo.execution.local.sweep_original import (
    create_local_hpo_objective as _create_local_hpo_objective_original,
    run_local_hpo_sweep as _run_local_hpo_sweep_original,
    _set_phase2_hpo_tags as _set_phase2_hpo_tags_original,
)

# Re-export for backward compatibility
def create_local_hpo_objective(
    dataset_path: str,
    config_dir: Path,
    backbone: str,
    hpo_config: Dict[str, Any],
    train_config: Dict[str, Any],
    output_base_dir: Path,
    mlflow_experiment_name: str,
    objective_metric: str = "macro-f1",
    k_folds: Optional[int] = None,
    fold_splits_file: Optional[Path] = None,
    run_id: Optional[str] = None,
    data_config: Optional[Dict[str, Any]] = None,
    benchmark_config: Optional[Dict[str, Any]] = None,
) -> Tuple[Callable[[Any], float], Callable[[], None]]:
    """Create Optuna objective function for local HPO."""
    return _create_local_hpo_objective_original(
        dataset_path=dataset_path,
        config_dir=config_dir,
        backbone=backbone,
        hpo_config=hpo_config,
        train_config=train_config,
        output_base_dir=output_base_dir,
        mlflow_experiment_name=mlflow_experiment_name,
        objective_metric=objective_metric,
        k_folds=k_folds,
        fold_splits_file=fold_splits_file,
        run_id=run_id,
        data_config=data_config,
        benchmark_config=benchmark_config,
    )


def run_local_hpo_sweep(
    dataset_path: str,
    config_dir: Path,
    backbone: str,
    hpo_config: Dict[str, Any],
    train_config: Dict[str, Any],
    output_dir: Path,
    mlflow_experiment_name: str,
    k_folds: Optional[int] = None,
    fold_splits_file: Optional[Path] = None,
    checkpoint_config: Optional[Dict[str, Any]] = None,
    restore_from_drive: Optional[Callable[[Path], bool]] = None,
    backup_to_drive: Optional[Callable[[Path, bool], bool]] = None,
    backup_enabled: bool = True,
    data_config: Optional[Dict[str, Any]] = None,
    benchmark_config: Optional[Dict[str, Any]] = None,
) -> Any:
    """Run a local hyperparameter optimization sweep using Optuna."""
    return _run_local_hpo_sweep_original(
        dataset_path=dataset_path,
        config_dir=config_dir,
        backbone=backbone,
        hpo_config=hpo_config,
        train_config=train_config,
        output_dir=output_dir,
        mlflow_experiment_name=mlflow_experiment_name,
        k_folds=k_folds,
        fold_splits_file=fold_splits_file,
        checkpoint_config=checkpoint_config,
        restore_from_drive=restore_from_drive,
        backup_to_drive=backup_to_drive,
        backup_enabled=backup_enabled,
        data_config=data_config,
        benchmark_config=benchmark_config,
    )

