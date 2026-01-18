"""Parameter Objects (TypedDict) for sweep tracker functions."""

from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict


class SweepRunConfig(TypedDict, total=False):
    """Configuration for start_sweep_run."""
    run_name: str
    hpo_config: Dict[str, Any]
    backbone: str
    study_name: str
    checkpoint_config: Optional[Dict[str, Any]]
    storage_path: Optional[Any]
    should_resume: bool
    context: Optional[Any]  # NamingContext
    output_dir: Optional[Path]
    group_id: Optional[str]
    data_config: Optional[Dict[str, Any]]
    benchmark_config: Optional[Dict[str, Any]]
    train_config: Optional[Dict[str, Any]]
    config_dir: Optional[Path]


class SweepMetadataConfig(TypedDict, total=False):
    """Configuration for _log_sweep_metadata."""
    hpo_config: Dict[str, Any]
    backbone: str
    study_name: str
    checkpoint_config: Optional[Dict[str, Any]]
    storage_path: Optional[Any]
    should_resume: bool
    output_dir: Optional[Path]


class FinalMetricsConfig(TypedDict, total=False):
    """Configuration for log_final_metrics."""
    study: Any
    objective_metric: str
    parent_run_id: str
    run_name: Optional[str]
    should_resume: bool
    hpo_output_dir: Optional[Path]
    backbone: Optional[str]
    run_id: Optional[str]
    fold_splits: Optional[List]
    hpo_config: Optional[Dict[str, Any]]
    child_runs_map: Optional[List]
    upload_checkpoint: bool
    output_dir: Optional[Path]
    config_dir: Optional[Path]


class CheckpointLoggerConfig(TypedDict, total=False):
    """Configuration for checkpoint logging methods."""
    study: Any
    hpo_output_dir: Path
    backbone: str
    run_id: Optional[str]
    fold_splits: Optional[List]
    prefer_checkpoint_dir: Optional[Path]
    refit_ok: Optional[bool]
    parent_run_id: Optional[str]
    refit_run_id: Optional[str]
    config_dir: Optional[Path]

