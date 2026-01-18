"""Parameter Objects (TypedDict/dataclass) for sweep functions."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional


@dataclass
class LocalHPOSweepConfig:
    """Configuration for run_local_hpo_sweep."""
    dataset_path: str
    config_dir: Path
    backbone: str
    hpo_config: Dict[str, Any]
    train_config: Dict[str, Any]
    output_dir: Path
    mlflow_experiment_name: str
    k_folds: Optional[int] = None
    fold_splits_file: Optional[Path] = None
    checkpoint_config: Optional[Dict[str, Any]] = None
    restore_from_drive: Optional[Callable[[Path], bool]] = None
    backup_to_drive: Optional[Callable[[Path, bool], bool]] = None
    backup_enabled: bool = True
    data_config: Optional[Dict[str, Any]] = None
    benchmark_config: Optional[Dict[str, Any]] = None


@dataclass
class LocalHPOObjectiveConfig:
    """Configuration for create_local_hpo_objective."""
    dataset_path: str
    config_dir: Path
    backbone: str
    hpo_config: Dict[str, Any]
    train_config: Dict[str, Any]
    output_base_dir: Path
    mlflow_experiment_name: str
    objective_metric: str = "macro-f1"
    k_folds: Optional[int] = None
    fold_splits_file: Optional[Path] = None
    run_id: Optional[str] = None
    data_config: Optional[Dict[str, Any]] = None
    benchmark_config: Optional[Dict[str, Any]] = None


@dataclass
class Phase2HPOTagsConfig:
    """Configuration for _set_phase2_hpo_tags."""
    parent_run_id: str
    data_config: Optional[Dict[str, Any]]
    hpo_config: Dict[str, Any]
    train_config: Dict[str, Any]
    backbone: str
    config_dir: Optional[Path] = None

