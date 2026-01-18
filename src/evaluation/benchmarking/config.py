"""Parameter Objects (TypedDict) for benchmarking functions."""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict


class BenchmarkExistenceConfig(TypedDict, total=False):
    """Configuration for benchmark_already_exists."""
    benchmark_key: str
    benchmark_experiment: Dict[str, str]
    root_dir: Path
    environment: str
    mlflow_client: Optional[Any]
    trial_key_hash: Optional[str]
    study_key_hash: Optional[str]
    config_dir: Optional[Path]


class MLflowBenchmarkQueryConfig(TypedDict, total=False):
    """Configuration for _benchmark_exists_in_mlflow."""
    benchmark_key: str
    benchmark_experiment: Dict[str, str]
    mlflow_client: Any
    trial_key_hash: Optional[str]
    study_key_hash: Optional[str]
    config_dir: Optional[Path]


class BenchmarkFilterConfig(TypedDict, total=False):
    """Configuration for filter_missing_benchmarks."""
    champions: Dict[str, Dict[str, Any]]
    benchmark_experiment: Dict[str, str]
    benchmark_config: Dict[str, Any]
    data_fingerprint: str
    eval_fingerprint: str
    root_dir: Path
    environment: str
    mlflow_client: Optional[Any]
    run_mode: Optional[str]


class BenchmarkConfig(TypedDict, total=False):
    """Configuration for benchmark_best_trials."""
    best_trials: Dict[str, Dict[str, Any]]
    test_data_path: Path
    root_dir: Path
    environment: str
    data_config: Dict[str, Any]
    hpo_config: Dict[str, Any]
    benchmark_config: Optional[Dict[str, Any]]
    benchmark_batch_sizes: Optional[List[int]]
    benchmark_iterations: int
    benchmark_warmup: int
    benchmark_max_length: int
    benchmark_device: Optional[str]
    benchmark_tracker: Optional[Any]
    backup_enabled: bool
    backup_to_drive: Optional[Callable[[Path, bool], bool]]
    restore_from_drive: Optional[Callable[[Path, bool], bool]]

