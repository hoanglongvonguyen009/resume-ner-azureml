"""
@meta
name: benchmarking_orchestrator
type: script
domain: benchmarking
responsibility:
  - Orchestrate benchmarking for best HPO trials
  - Handle checkpoint selection and resolution
  - Run benchmarks on trial checkpoints
  - Manage backup and restore operations
inputs:
  - Best trial information
  - Test data path
  - Benchmark configuration
outputs:
  - Benchmark results (JSON files)
  - MLflow benchmark runs
tags:
  - orchestration
  - benchmarking
  - hpo
ci:
  runnable: true
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

"""Orchestrate benchmarking for best HPO trials.

This module provides utilities to run benchmarks on best trial checkpoints
from HPO runs, handling path resolution, checkpoint selection, and backup.

This module has been refactored into focused submodules:
- benchmarking.config: Parameter Objects (TypedDicts)
- benchmarking.existence_checker: Benchmark existence checking
- benchmarking.filter: Benchmark filtering
- benchmarking.path_resolver: Path resolution utilities
- benchmarking.checkpoint_resolver: Checkpoint resolution
- benchmarking.run_id_resolver: Run ID resolution

This file maintains backward compatibility by re-exporting all public APIs.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from common.shared.logging_utils import get_logger

# Re-export from extracted modules
from evaluation.benchmarking.existence_checker import (
    benchmark_already_exists,
    benchmark_exists_in_mlflow as _benchmark_exists_in_mlflow_impl,
    benchmark_exists_on_disk as _benchmark_exists_on_disk_impl,
    _is_valid_uuid,
)

from evaluation.benchmarking.filter import filter_missing_benchmarks

from evaluation.benchmarking.path_resolver import (
    build_benchmark_output_path as _build_benchmark_output_path_impl,
)

from evaluation.benchmarking.checkpoint_resolver import (
    extract_trial_id,
    validate_trial_info as _validate_trial_info_impl,
)

from evaluation.benchmarking.run_id_resolver import (
    resolve_run_ids as _resolve_run_ids_impl,
    check_benchmark_exists as _check_benchmark_exists_impl,
    build_benchmark_key_for_trial as _build_benchmark_key_for_trial_impl,
)

# Import original functions that haven't been extracted yet (for backward compatibility)
from evaluation.benchmarking.orchestrator_original import (
    _get_mlflow_client,
    _find_hpo_experiment_id,
    _lookup_trial_run_id,
    _lookup_refit_run_id,
    build_benchmark_key,
    get_benchmark_run_mode,
    benchmark_champions,
    benchmark_best_trials as _benchmark_best_trials_original,
)

logger = get_logger(__name__)

# Constants
CHECKPOINT_DIRNAME = "checkpoint"
DEFAULT_BENCHMARK_FILENAME = "benchmark.json"


# Re-export public functions for backward compatibility
def benchmark_best_trials(
    best_trials: Dict[str, Dict[str, Any]],
    test_data_path: Path,
    root_dir: Path,
    environment: str,
    data_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
    benchmark_config: Optional[Dict[str, Any]] = None,
    benchmark_batch_sizes: Optional[List[int]] = None,
    benchmark_iterations: int = 100,
    benchmark_warmup: int = 10,
    benchmark_max_length: int = 512,
    benchmark_device: Optional[str] = None,
    benchmark_tracker: Optional[Any] = None,
    backup_enabled: bool = True,
    backup_to_drive: Optional[Callable[[Path, bool], bool]] = None,
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
) -> Dict[str, Path]:
    """
    Run benchmarking on best trial checkpoints from HPO runs.
    
    Supports two modes:
    1. Champion mode: Uses complete champion data from Phase 2 (no lookups needed)
    2. Legacy mode: Uses best_trials format (requires lookups and checkpoint finding)

    Args:
        best_trials: Dictionary mapping backbone names to trial info dicts
        test_data_path: Path to test data JSON file
        root_dir: Root directory of the project
        environment: Platform environment (local, colab, kaggle)
        data_config: Data configuration dict
        hpo_config: HPO configuration dict
        benchmark_config: Optional benchmark configuration dict
        benchmark_batch_sizes: List of batch sizes to test (default: [1, 8, 16])
        benchmark_iterations: Number of iterations per batch size (default: 100)
        benchmark_warmup: Number of warmup iterations (default: 10)
        benchmark_max_length: Maximum sequence length (default: 512)
        benchmark_device: Device to use (None = auto-detect)
        benchmark_tracker: Optional MLflowBenchmarkTracker instance
        backup_enabled: Whether backup is enabled
        backup_to_drive: Function to backup files to Drive
        restore_from_drive: Function to restore files from Drive

    Returns:
        Dictionary mapping backbone names to benchmark output paths
    """
    return _benchmark_best_trials_original(
        best_trials=best_trials,
        test_data_path=test_data_path,
        root_dir=root_dir,
        environment=environment,
        data_config=data_config,
        hpo_config=hpo_config,
        benchmark_config=benchmark_config,
        benchmark_batch_sizes=benchmark_batch_sizes,
        benchmark_iterations=benchmark_iterations,
        benchmark_warmup=benchmark_warmup,
        benchmark_max_length=benchmark_max_length,
        benchmark_device=benchmark_device,
        benchmark_tracker=benchmark_tracker,
        backup_enabled=backup_enabled,
        backup_to_drive=backup_to_drive,
        restore_from_drive=restore_from_drive,
    )


# Re-export helper functions for backward compatibility
def _extract_trial_id(trial_info: Dict[str, Any]) -> str:
    """Extract trial ID from trial_info."""
    return extract_trial_id(trial_info)


def _validate_trial_info(trial_info: Dict[str, Any], backbone: str) -> Optional[Path]:
    """Validate trial_info and extract checkpoint_dir."""
    return _validate_trial_info_impl(trial_info, backbone)


def _build_benchmark_output_path(
    trial_info: Dict[str, Any],
    backbone: str,
    root_dir: Path,
    environment: str,
    benchmark_config: Optional[Dict[str, Any]],
    data_config: Optional[Dict[str, Any]],
    hpo_config: Optional[Dict[str, Any]],
) -> Path:
    """Build benchmark output path for a trial."""
    return _build_benchmark_output_path_impl(
        trial_info=trial_info,
        backbone=backbone,
        root_dir=root_dir,
        environment=environment,
        benchmark_config=benchmark_config,
        data_config=data_config,
        hpo_config=hpo_config,
    )


def _resolve_run_ids(
    trial_info: Dict[str, Any],
    is_champion: bool,
    benchmark_tracker: Optional[Any],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Resolve HPO run IDs (trial, refit, sweep) from trial_info or MLflow."""
    return _resolve_run_ids_impl(
        trial_info=trial_info,
        is_champion=is_champion,
        benchmark_tracker=benchmark_tracker,
    )


def _check_benchmark_exists(
    benchmark_output: Path,
    restore_from_drive: Optional[Callable[[Path, bool], bool]],
) -> bool:
    """Check if benchmark already exists (local or Drive)."""
    return _check_benchmark_exists_impl(benchmark_output, restore_from_drive)


def _build_benchmark_key_for_trial(
    trial_info: Dict[str, Any],
    benchmark_config: Optional[Dict[str, Any]],
    data_config: Optional[Dict[str, Any]],
    hpo_config: Optional[Dict[str, Any]],
    hpo_refit_run_id: Optional[str],
) -> Optional[str]:
    """Build benchmark key for idempotency checking."""
    return _build_benchmark_key_for_trial_impl(
        trial_info=trial_info,
        benchmark_config=benchmark_config,
        data_config=data_config,
        hpo_config=hpo_config,
        hpo_refit_run_id=hpo_refit_run_id,
    )


def _benchmark_exists_in_mlflow(
    benchmark_key: str,
    benchmark_experiment: Dict[str, str],
    mlflow_client: Any,
    trial_key_hash: Optional[str] = None,
    study_key_hash: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> bool:
    """Check if benchmark run exists in MLflow with matching benchmark_key."""
    return _benchmark_exists_in_mlflow_impl(
        benchmark_key=benchmark_key,
        benchmark_experiment=benchmark_experiment,
        mlflow_client=mlflow_client,
        trial_key_hash=trial_key_hash,
        study_key_hash=study_key_hash,
        config_dir=config_dir,
    )


def _benchmark_exists_on_disk(
    benchmark_key: str,
    root_dir: Path,
    environment: str,
) -> bool:
    """Check if benchmark file exists on disk."""
    return _benchmark_exists_on_disk_impl(benchmark_key, root_dir, environment)


__all__ = [
    "benchmark_already_exists",
    "benchmark_best_trials",
    "benchmark_champions",
    "build_benchmark_key",
    "filter_missing_benchmarks",
    "get_benchmark_run_mode",
]
