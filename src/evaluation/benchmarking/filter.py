"""Benchmark filtering utilities."""

from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.logging_utils import get_logger

from evaluation.benchmarking.existence_checker import benchmark_already_exists
from evaluation.benchmarking.orchestrator_original import build_benchmark_key

logger = get_logger(__name__)


def _get_mlflow_client() -> Optional[Any]:
    """
    Get MLflow client instance (shared utility).
    
    Returns:
        MLflowClient instance or None if creation fails
    """
    from infrastructure.tracking.mlflow.client import get_mlflow_client
    return get_mlflow_client()


def filter_missing_benchmarks(
    champions: Dict[str, Dict[str, Any]],  # From Phase 2 champion selection
    benchmark_experiment: Dict[str, str],
    benchmark_config: Dict[str, Any],
    data_fingerprint: str,  # From Phase 2
    eval_fingerprint: str,  # From Phase 2
    root_dir: Path,
    environment: str,
    mlflow_client: Optional[Any] = None,
    run_mode: Optional[str] = None,  # Run mode: "reuse_if_exists", "force_new", etc.
) -> Dict[str, Dict[str, Any]]:
    """
    Filter out champions that already have benchmarks.
    
    Uses stable benchmark_key to check:
    - MLflow: existing benchmark run with matching trial_key_hash and study_key_hash
    - Disk: cached benchmark_{key}.json
    
    Args:
        champions: Dict mapping backbone -> champion selection result from Phase 2
        benchmark_experiment: Benchmark experiment info (name, id)
        benchmark_config: Benchmark configuration dictionary
        data_fingerprint: Data fingerprint from Phase 2
        eval_fingerprint: Evaluation fingerprint from Phase 2
        root_dir: Root directory of the project
        environment: Platform environment (local, colab, kaggle)
        mlflow_client: Optional MLflow client instance
        run_mode: Run mode - if "force_new", skips filtering entirely
        
    Returns:
        Dict mapping backbone -> champion data for champions that need benchmarking
    """
    # If force_new, don't filter - benchmark everything
    if run_mode == "force_new":
        logger.info("Run mode is 'force_new' - skipping idempotency check, will benchmark all champions")
        return champions
    
    if mlflow_client is None:
        mlflow_client = _get_mlflow_client()
    
    champions_to_benchmark = {}
    
    for backbone, champion_data in champions.items():
        champion = champion_data.get("champion", {})
        champion_run_id = champion.get("run_id")
        
        if not champion_run_id:
            logger.warning(f"No run_id found for champion {backbone}, skipping idempotency check")
            champions_to_benchmark[backbone] = champion_data
            continue
        
        # Build stable key using champion run_id and fingerprints
        benchmark_key = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=benchmark_config,
        )
        
        # Check if benchmark exists (using trial_key_hash and study_key_hash for more reliable matching)
        trial_key_hash = champion.get("trial_key_hash")
        study_key_hash = champion.get("study_key_hash")
        
        if benchmark_already_exists(
            benchmark_key, 
            benchmark_experiment, 
            root_dir, 
            environment, 
            mlflow_client,
            trial_key_hash=trial_key_hash,
            study_key_hash=study_key_hash,
            config_dir=root_dir / "config",
        ):
            logger.info(f"Skipping {backbone} - benchmark already exists (trial_key_hash={trial_key_hash[:16] if trial_key_hash else 'N/A'}...)")
            continue
        
        champions_to_benchmark[backbone] = champion_data
    
    return champions_to_benchmark

