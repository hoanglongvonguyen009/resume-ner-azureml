"""
Type definitions for selection module.

This module provides TypedDict classes for common dictionary shapes used
throughout the selection module, improving type safety and IDE support.
"""
from typing import TypedDict, Optional


class TrialInfo(TypedDict, total=False):
    """Trial information dictionary structure."""
    trial_name: str
    trial_dir: str
    trial_id: Optional[str]
    trial_number: Optional[int]
    trial_run_id: Optional[str]
    accuracy: Optional[float]
    metrics: dict[str, float]
    hyperparameters: dict[str, object]
    checkpoint_dir: Optional[str]
    checkpoint_type: Optional[str]
    backbone: Optional[str]
    study_name: Optional[str]
    study_key_hash: Optional[str]
    trial_key_hash: Optional[str]


class BestModelInfo(TypedDict, total=False):
    """Best model information dictionary structure."""
    run_id: str
    trial_run_id: Optional[str]
    experiment_name: str
    experiment_id: str
    backbone: str
    study_key_hash: Optional[str]
    trial_key_hash: Optional[str]
    f1_score: Optional[float]
    latency_ms: Optional[float]
    composite_score: Optional[float]
    tags: dict[str, str]
    params: dict[str, object]
    metrics: dict[str, float]
    has_refit_run: Optional[bool]


class SelectionConfig(TypedDict, total=False):
    """Selection configuration dictionary structure."""
    objective: dict[str, object]
    scoring: dict[str, object]
    benchmark: dict[str, object]
    selection: dict[str, object]


class CacheData(TypedDict, total=False):
    """Cache data dictionary structure."""
    schema_version: int
    timestamp: str
    experiment_name: str
    tracking_uri: Optional[str]
    benchmark_experiment: dict[str, str]
    hpo_experiments: dict[str, dict[str, str]]
    selection_config_hash: str
    tags_config_hash: str
    cache_key: str
    best_model: BestModelInfo
    inputs_summary: Optional[dict[str, object]]


class CandidateInfo(TypedDict, total=False):
    """Candidate configuration dictionary structure."""
    backbone: str
    accuracy: float
    config: dict[str, object]
    speed_score: float
    speed_data_source: str
    benchmark_latency_ms: Optional[float]

