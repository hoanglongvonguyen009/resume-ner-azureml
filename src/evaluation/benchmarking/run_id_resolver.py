"""Run ID resolution utilities for benchmarking."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def _get_mlflow_client() -> Optional[Any]:
    """
    Get MLflow client instance (shared utility).
    
    Returns:
        MLflowClient instance or None if creation fails
    """
    from infrastructure.tracking.mlflow.client import get_mlflow_client
    return get_mlflow_client()


def _is_valid_uuid(run_id: Optional[str]) -> bool:
    """
    Check if a run_id is a valid UUID format.
    
    Args:
        run_id: Run ID string to validate
        
    Returns:
        True if valid UUID format, False otherwise
    """
    if not run_id:
        return False
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(run_id))


def resolve_run_ids(
    trial_info: Dict[str, Any],
    is_champion: bool,
    benchmark_tracker: Optional[Any],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Resolve HPO run IDs (trial, refit, sweep) from trial_info or MLflow.
    
    Args:
        trial_info: Trial info dictionary
        is_champion: Whether this is champion mode (has complete data)
        benchmark_tracker: Optional benchmark tracker
        
    Returns:
        Tuple of (trial_run_id, refit_run_id, sweep_run_id)
    """
    from evaluation.benchmarking.orchestrator_original import (
        _lookup_refit_run_id,
        _lookup_trial_run_id,
    )
    
    hpo_trial_run_id = trial_info.get("trial_run_id")
    hpo_refit_run_id = trial_info.get("refit_run_id") or trial_info.get("run_id")
    hpo_sweep_run_id = trial_info.get("sweep_run_id")
    
    # In champion mode, run IDs are already available
    if is_champion:
        return hpo_trial_run_id, hpo_refit_run_id, hpo_sweep_run_id
    
    # Legacy mode: validate and potentially look up run IDs from MLflow
    trial_key_hash = trial_info.get("trial_key_hash")
    study_key_hash = trial_info.get("study_key_hash")
    
    if not trial_key_hash:
        return hpo_trial_run_id, hpo_refit_run_id, hpo_sweep_run_id
    
    client = _get_mlflow_client()
    if client is None:
        logger.warning("Could not create MLflow client for run ID lookup")
        return hpo_trial_run_id, hpo_refit_run_id, hpo_sweep_run_id
    
    # Look up trial run if needed
    if not hpo_trial_run_id or not _is_valid_uuid(hpo_trial_run_id):
        looked_up_trial_id = _lookup_trial_run_id(
            client, trial_key_hash, study_key_hash, benchmark_tracker
        )
        if looked_up_trial_id:
            hpo_trial_run_id = looked_up_trial_id
    
    # Look up refit run if needed
    if not hpo_refit_run_id or not _is_valid_uuid(hpo_refit_run_id):
        looked_up_refit_id = _lookup_refit_run_id(
            client, trial_key_hash, study_key_hash, benchmark_tracker
        )
        if looked_up_refit_id:
            hpo_refit_run_id = looked_up_refit_id
    
    return hpo_trial_run_id, hpo_refit_run_id, hpo_sweep_run_id


def check_benchmark_exists(
    benchmark_output: Path,
    restore_from_drive: Optional[Any],
) -> bool:
    """
    Check if benchmark already exists (local or Drive).
    
    Args:
        benchmark_output: Path to benchmark output file
        restore_from_drive: Optional function to restore from Drive
        
    Returns:
        True if benchmark exists, False otherwise
    """
    from common.shared.platform_detection import is_drive_path
    
    if is_drive_path(benchmark_output):
        # File is in Drive - check directly
        return benchmark_output.exists()
    else:
        # File is local - check and restore from Drive if needed
        if restore_from_drive and restore_from_drive(benchmark_output, False):
            return True
        return False


def build_benchmark_key_for_trial(
    trial_info: Dict[str, Any],
    benchmark_config: Optional[Dict[str, Any]],
    data_config: Optional[Dict[str, Any]],
    hpo_config: Optional[Dict[str, Any]],
    hpo_refit_run_id: Optional[str],
) -> Optional[str]:
    """
    Build benchmark key for idempotency checking.
    
    Args:
        trial_info: Trial info dictionary
        benchmark_config: Optional benchmark configuration
        data_config: Optional data configuration
        hpo_config: Optional HPO configuration
        hpo_refit_run_id: Refit run ID (used as champion_run_id)
        
    Returns:
        Benchmark key string if successful, None otherwise
    """
    from evaluation.benchmarking.orchestrator_original import build_benchmark_key
    from infrastructure.naming.mlflow.hpo_keys import (
        compute_data_fingerprint,
        compute_eval_fingerprint,
    )
    
    if not benchmark_config or not hpo_refit_run_id:
        return None
    
    try:
        # Compute fingerprints from configs
        data_fingerprint = compute_data_fingerprint(data_config) if data_config else ""
        eval_fingerprint = compute_eval_fingerprint(hpo_config) if hpo_config else ""
        
        # Use refit_run_id as champion_run_id (artifact parent)
        champion_run_id = hpo_refit_run_id
        
        # Build stable benchmark key
        benchmark_key = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=benchmark_config,
        )
        logger.debug(
            f"[BENCHMARK] Built benchmark_key={benchmark_key[:32]}... for idempotency"
        )
        return benchmark_key
    except Exception as e:
        logger.warning(f"Could not build benchmark_key: {e}")
        return None

