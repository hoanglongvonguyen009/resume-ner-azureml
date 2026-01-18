"""Configuration TypedDicts for trial finder functions."""

from pathlib import Path
from typing import Any, Dict, Optional, TypedDict


class TrialFinderConfig(TypedDict, total=False):
    """Configuration for find_best_trial_from_study."""
    study: Any  # Optuna study
    backbone_name: str
    dataset_version: str
    objective_metric: str
    hpo_backbone_dir: Path
    hpo_config: Optional[Dict[str, Any]]
    data_config: Optional[Dict[str, Any]]


class BackboneTrialFinderConfig(TypedDict, total=False):
    """Configuration for find_best_trials_for_backbones."""
    backbone_values: list[str]
    hpo_studies: Optional[Dict[str, Any]]
    hpo_config: Dict[str, Any]
    data_config: Dict[str, Any]
    root_dir: Path
    environment: str


class ChampionSelectorConfig(TypedDict, total=False):
    """Configuration for select_champion_per_backbone."""
    backbone: str
    hpo_experiment: Dict[str, str]
    selection_config: Dict[str, Any]
    mlflow_client: Any  # MlflowClient
    root_dir: Optional[Path]
    config_dir: Optional[Path]

