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
"""

from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Tuple
import hashlib
import json

from common.shared.logging_utils import get_logger
from .utils import run_benchmarking
from infrastructure.paths import (
    resolve_output_path_for_colab,
    validate_path_before_mkdir,
)
from infrastructure.naming import create_naming_context
from infrastructure.paths import build_output_path
from infrastructure.config.loader import compute_config_hash
from infrastructure.config.run_mode import get_run_mode
from infrastructure.naming.mlflow.hpo_keys import (
    compute_data_fingerprint,
    compute_eval_fingerprint,
)

logger = get_logger(__name__)

# Constants
CHECKPOINT_DIRNAME = "checkpoint"
# BENCHMARK_FILENAME is now loaded from benchmark_config["output"]["filename"]
# Default fallback value
DEFAULT_BENCHMARK_FILENAME = "benchmark.json"


# Phase 3: Shared Utilities (DRY)

def _get_mlflow_client() -> Optional[Any]:
    """
    Get MLflow client instance (shared utility).
    
    Returns:
        MLflowClient instance or None if creation fails
    """
    try:
        from mlflow.tracking import MlflowClient
        return MlflowClient()
    except Exception as e:
        logger.warning(f"Could not create MLflow client: {e}")
        return None


# Phase 3: Idempotent Benchmarking Functions

def build_benchmark_key(
    champion_run_id: str,  # MLflow run_id of champion
    data_fingerprint: str,  # From Phase 2
    eval_fingerprint: str,  # From Phase 2
    benchmark_config: Dict[str, Any],
) -> str:
    """
    Build stable benchmark identity key.
    
    Reuses fingerprints from Phase 2 (DRY).
    
    Key format: {champion_run_id}:{data_fp}:{eval_fp}:{bench_fp}
    
    Note: Uses champion_run_id (MLflow handle) as primary identifier.
    This ensures idempotency even if trial_key_hash changes.
    
    Args:
        champion_run_id: MLflow run_id of the champion trial
        data_fingerprint: Data fingerprint from Phase 2
        eval_fingerprint: Evaluation fingerprint from Phase 2
        benchmark_config: Benchmark configuration dictionary
        
    Returns:
        Stable benchmark key string
    """
    # Benchmark config hash (reuse existing utility)
    bench_fp = compute_config_hash(benchmark_config)
    
    # Build key using champion run_id and fingerprints from Phase 2
    key = f"{champion_run_id}:{data_fingerprint}:{eval_fingerprint}:{bench_fp}"
    
    return key


def benchmark_already_exists(
    benchmark_key: str,
    benchmark_experiment: Dict[str, str],
    root_dir: Path,
    environment: str,
    mlflow_client: Optional[Any] = None,
    trial_key_hash: Optional[str] = None,
    study_key_hash: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> bool:
    """
    Check if benchmark exists (MLflow or disk).
    
    Args:
        benchmark_key: Stable benchmark key (from build_benchmark_key)
        benchmark_experiment: Benchmark experiment info (name, id)
        root_dir: Root directory of the project
        environment: Platform environment (local, colab, kaggle)
        mlflow_client: Optional MLflow client instance
        trial_key_hash: Optional trial key hash (fallback only)
        study_key_hash: Optional study key hash (fallback only)
        config_dir: Optional config directory path. If provided, used directly instead of inferring.
                    This avoids issues when checkpoint_dir is in Drive but project root is elsewhere (e.g., Colab).
        
    Returns:
        True if benchmark already exists, False otherwise
    """
    # Derive config_dir from root_dir if not provided
    if config_dir is None:
        config_dir = root_dir / "config"
    
    # Check MLflow first (authoritative)
    if mlflow_client:
        try:
            if _benchmark_exists_in_mlflow(
                benchmark_key, 
                benchmark_experiment, 
                mlflow_client,
                trial_key_hash=trial_key_hash,
                study_key_hash=study_key_hash,
                config_dir=config_dir,
            ):
                return True
        except Exception as e:
            logger.debug(f"MLflow check failed: {e}, falling back to disk check")
    
    # Fallback to disk
    if _benchmark_exists_on_disk(benchmark_key, root_dir, environment):
        return True
    
    return False


def _benchmark_exists_in_mlflow(
    benchmark_key: str,
    benchmark_experiment: Dict[str, str],
    mlflow_client: Any,
    trial_key_hash: Optional[str] = None,  # Fallback only
    study_key_hash: Optional[str] = None,  # Fallback only
    config_dir: Optional[Path] = None,
) -> bool:
    """
    Check if benchmark run exists in MLflow with matching benchmark_key.
    
    Priority:
    1. benchmark_key tag (PRIMARY - includes config hash)
    2. trial_key_hash + study_key_hash (FALLBACK - backward compatibility)
    
    Args:
        benchmark_key: Stable benchmark key (includes config hash)
        benchmark_experiment: Benchmark experiment info (name, id)
        mlflow_client: MLflow client instance
        trial_key_hash: Optional trial key hash (fallback only)
        study_key_hash: Optional study key hash (fallback only)
        config_dir: Optional config directory path. If provided, used directly instead of inferring.
                    This avoids issues when checkpoint_dir is in Drive but project root is elsewhere (e.g., Colab).
        
    Returns:
        True if benchmark run exists and is finished, False otherwise
    """
    # PRIMARY: Check by benchmark_key tag (most reliable - includes config hash)
    try:
        runs = mlflow_client.search_runs(
            experiment_ids=[benchmark_experiment["id"]],
            filter_string=f"tags.benchmark_key = '{benchmark_key}'",
            max_results=10,
        )
        finished_runs = [r for r in runs if r.info.status == "FINISHED"]
        if finished_runs:
            logger.debug(
                f"Found {len(finished_runs)} finished benchmark run(s) with benchmark_key={benchmark_key[:32]}..."
            )
            return True
    except Exception as e:
        logger.debug(f"benchmark_key tag search failed: {e}")
    
    # FALLBACK: Check by trial_key_hash + study_key_hash (backward compatibility)
    # Only use this if benchmark_key tag is not set (older runs)
    if trial_key_hash and study_key_hash:
        try:
            trial_key_tag = "code.grouping.trial_key_hash"
            study_key_tag = "code.grouping.study_key_hash"
            
            try:
                from infrastructure.naming.mlflow.tags_registry import load_tags_registry
                tags_registry = load_tags_registry(config_dir=config_dir)
                trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
                study_key_tag = tags_registry.key("grouping", "study_key_hash")
            except Exception:
                # Fallback to hardcoded keys (backward compatibility)
                pass
            
            filter_string = f"tags.{trial_key_tag} = '{trial_key_hash}' AND tags.{study_key_tag} = '{study_key_hash}'"
            runs = mlflow_client.search_runs(
                experiment_ids=[benchmark_experiment["id"]],
                filter_string=filter_string,
                max_results=10,
            )
            
            finished_runs = [r for r in runs if r.info.status == "FINISHED"]
            if finished_runs:
                logger.warning(
                    f"Found {len(finished_runs)} finished benchmark run(s) by hash (fallback). "
                    f"Consider setting benchmark_key tag for more reliable idempotency. "
                    f"trial_key_hash={trial_key_hash[:16]}..."
                )
                return True
        except Exception as e:
            logger.debug(f"Hash-based fallback search failed: {e}")
    
    return False


def _benchmark_exists_on_disk(
    benchmark_key: str,
    root_dir: Path,
    environment: str,
) -> bool:
    """
    Check if benchmark file exists on disk.
    
    Args:
        benchmark_key: Stable benchmark key
        root_dir: Root directory of the project
        environment: Platform environment (local, colab, kaggle)
        
    Returns:
        True if benchmark file exists, False otherwise
    """
    cache_dir = root_dir / "outputs" / "benchmarking" / environment / "cache"
    benchmark_file = cache_dir / f"benchmark_{benchmark_key}.json"
    
    return benchmark_file.exists() if benchmark_file else False


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


def get_benchmark_run_mode(
    benchmark_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
) -> str:
    """
    Get benchmark run mode (independent of HPO config).
    
    Uses shared run_mode.py utility (DRY).
    
    Args:
        benchmark_config: Benchmark configuration dictionary
        hpo_config: HPO configuration dictionary (unused - kept for compatibility)
        
    Returns:
        Run mode string: "reuse_if_exists", "force_new", or "resume_if_incomplete"
    """
    # Get run mode from benchmark config (defaults to "reuse_if_exists" if not specified)
    # Note: HPO no longer uses run.mode, so benchmark mode is independent
    return get_run_mode(benchmark_config, default="reuse_if_exists")


def benchmark_champions(
    champions: Dict[str, Dict[str, Any]],  # From Phase 2
    test_data_path: Path,
    root_dir: Path,
    environment: str,
    data_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
    benchmark_config: Optional[Dict[str, Any]] = None,
    benchmark_experiment: Optional[Dict[str, str]] = None,
    benchmark_batch_sizes: Optional[List[int]] = None,
    benchmark_iterations: int = 100,
    benchmark_warmup: int = 10,
    benchmark_max_length: int = 512,
    benchmark_device: Optional[str] = None,
    benchmark_tracker: Optional[Any] = None,
    backup_enabled: bool = True,
    backup_to_drive: Optional[Callable[[Path, bool], bool]] = None,
    ensure_restored_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    mlflow_client: Optional[Any] = None,
) -> Dict[str, Path]:
    """
    Benchmark champions selected in Phase 2.
    
    Each champion represents the best trial from the best configuration group
    for that backbone. We only benchmark champions, not all variants.
    
    This function converts champions to best_trials format and calls
    benchmark_best_trials() internally.
    
    Args:
        champions: Dict mapping backbone -> champion selection result from Phase 2
        test_data_path: Path to test data JSON file
        root_dir: Root directory of the project
        environment: Platform environment (local, colab, kaggle)
        data_config: Data configuration dict
        hpo_config: HPO configuration dict
        benchmark_config: Optional benchmark configuration dict
        benchmark_experiment: Optional benchmark experiment info (name, id)
        benchmark_batch_sizes: List of batch sizes to test (default: [1, 8, 16])
        benchmark_iterations: Number of iterations per batch size (default: 100)
        benchmark_warmup: Number of warmup iterations (default: 10)
        benchmark_max_length: Maximum sequence length (default: 512)
        benchmark_device: Device to use (None = auto-detect)
        benchmark_tracker: Optional MLflowBenchmarkTracker instance
        backup_enabled: Whether backup is enabled
        backup_to_drive: Function to backup files to Drive
        ensure_restored_from_drive: Function to restore files from Drive
        mlflow_client: Optional MLflow client instance
        
    Returns:
        Dictionary mapping backbone names to benchmark output paths
    """
    # Convert champions to best_trials format for benchmark_best_trials()
    best_trials = {}
    
    for backbone, champion_data in champions.items():
        champion = champion_data.get("champion", {})
        
        # Extract checkpoint path from champion
        checkpoint_path = champion.get("checkpoint_path")
        if not checkpoint_path:
            logger.warning(f"No checkpoint_path found for champion {backbone}, skipping")
            continue
        
        # Build trial_info dict with ALL champion data (no need for lookups)
        trial_info = {
            "backbone": backbone,
            "run_id": champion.get("run_id"),  # MLflow run_id (primary)
            "trial_run_id": champion.get("trial_run_id"),  # CV trial run_id
            "refit_run_id": champion.get("refit_run_id") or champion.get("run_id"),  # Refit run_id
            "sweep_run_id": champion.get("sweep_run_id"),  # Parent HPO run_id
            "trial_key_hash": champion.get("trial_key_hash"),
            "study_key_hash": champion.get("study_key_hash"),
            "checkpoint_dir": str(checkpoint_path),  # Already resolved path
            "trial_name": champion.get("trial_key_hash", "unknown")[:16],
            "metric": champion.get("metric"),
            # Mark as champion-based to skip redundant lookups
            "_is_champion": True,
        }
        
        best_trials[backbone] = trial_info
    
    # Call existing benchmark_best_trials() function
    return benchmark_best_trials(
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
        ensure_restored_from_drive=ensure_restored_from_drive,
    )


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
    ensure_restored_from_drive: Optional[Callable[[Path, bool], bool]] = None,
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
        ensure_restored_from_drive: Function to restore files from Drive

    Returns:
        Dictionary mapping backbone names to benchmark output paths
    """
    if benchmark_batch_sizes is None:
        benchmark_batch_sizes = [1, 8, 16]

    if not test_data_path or not test_data_path.exists():
        logger.info("Skipping benchmarking (test data not available)")
        return {}

    benchmark_results = {}

    for backbone, trial_info in best_trials.items():
        is_champion = trial_info.get("_is_champion", False)
        
        # Use checkpoint_dir directly from champion data (required)
        checkpoint_dir: Optional[Path] = None
        if "checkpoint_dir" in trial_info and trial_info["checkpoint_dir"]:
            checkpoint_dir = Path(trial_info["checkpoint_dir"])
        else:
            # Legacy format no longer supported - require champion format
            logger.warning(
                f"Skipping {backbone}: missing 'checkpoint_dir' in trial_info. "
                f"Legacy format (trial_dir) is no longer supported. "
                f"Please use champion format from Phase 2."
            )
            continue
        
        # At this point, checkpoint_dir must be a Path (not None)
        assert checkpoint_dir is not None, "checkpoint_dir should be set by this point"

        backbone_name = backbone.split("-")[0] if "-" in backbone else backbone

        trial_id_raw = trial_info.get(
            "trial_id") or trial_info.get("trial_name", "unknown")
        # Handle both old format (trial_1_20251231_161745) and new format (trial-25d03eeb)
        if trial_id_raw.startswith("trial_"):
            trial_id = trial_id_raw[6:]  # Remove "trial_" prefix
        elif trial_id_raw.startswith("trial-"):
            trial_id = trial_id_raw  # Keep full "trial-25d03eeb" format
        else:
            trial_id = trial_id_raw
        
        logger.debug(f"[BENCHMARK] Extracted trial_id: {trial_id} from trial_info (trial_id={trial_info.get('trial_id')}, trial_name={trial_info.get('trial_name')})")

        # Use hashes directly from champion data (required)
        study_key_hash = trial_info.get("study_key_hash")
        trial_key_hash = trial_info.get("trial_key_hash")
        
        if not study_key_hash or not trial_key_hash:
            # Legacy format no longer supported - require champion format
            logger.warning(
                f"Skipping {backbone}: missing 'study_key_hash' or 'trial_key_hash' in trial_info. "
                f"Legacy format is no longer supported. "
                f"Please use champion format from Phase 2."
            )
            continue
        
        # Champion mode: hashes already available, compute study_family_hash if needed
        study_family_hash = None
        if study_key_hash and trial_key_hash:
            try:
                from infrastructure.naming.mlflow.hpo_keys import (
                    build_hpo_study_family_key,
                    build_hpo_study_family_hash,
                )
                if data_config and hpo_config:
                    study_family_key = build_hpo_study_family_key(
                        data_config=data_config,
                        hpo_config=hpo_config,
                        benchmark_config=benchmark_config,
                    )
                    study_family_hash = build_hpo_study_family_hash(study_family_key)
            except Exception:
                pass

        # Compute benchmark_config_hash if benchmark_config is available
        benchmark_config_hash = None
        if benchmark_config:
            try:
                from common.shared.hash_utils import compute_json_hash
                # Normalize and hash benchmark_config for stable identity
                benchmark_config_hash = compute_json_hash(benchmark_config, length=64)
            except Exception as e:
                logger.debug(f"Could not compute benchmark_config_hash: {e}")

        # Build benchmarking output path with hashes
        benchmarking_context = create_naming_context(
            process_type="benchmarking",
            model=backbone_name,
            trial_id=trial_id,
            environment=environment,
            study_key_hash=study_key_hash,
            trial_key_hash=trial_key_hash,
            benchmark_config_hash=benchmark_config_hash,
        )
        benchmarking_path = build_output_path(root_dir, benchmarking_context)
        # Redirect to Drive on Colab for persistence (similar to checkpoints)
        benchmarking_path = resolve_output_path_for_colab(benchmarking_path)
        # Validate path before creating directory
        benchmarking_path = validate_path_before_mkdir(
            benchmarking_path, context="benchmarking directory"
        )
        benchmarking_path.mkdir(parents=True, exist_ok=True)

        # Get output filename from config, with fallback to default
        output_filename = DEFAULT_BENCHMARK_FILENAME
        if benchmark_config and "output" in benchmark_config:
            output_filename = benchmark_config["output"].get("filename", DEFAULT_BENCHMARK_FILENAME)
        
        benchmark_output = benchmarking_path / output_filename

        if not checkpoint_dir.exists():
            logger.warning(
                f"Checkpoint not found for {backbone} {trial_info['trial_name']} at {checkpoint_dir}"
            )
            # Log trial directory contents for debugging
            if "trial_dir" in trial_info and trial_info["trial_dir"]:
                trial_dir = Path(trial_info["trial_dir"])
                if trial_dir.exists():
                    try:
                        contents = [
                            item.name for item in trial_dir.iterdir() if item.is_dir()]
                        logger.debug(
                            f"Trial directory {trial_dir} contains: {contents}")
                    except Exception as e:
                        logger.debug(f"Could not list trial directory: {e}")
            continue

        # Check if benchmark already exists (handle both local and Drive paths)
        if str(benchmark_output).startswith("/content/drive"):
            # File is in Drive - check directly
            if benchmark_output.exists():
                logger.info(
                    f"Benchmark results already exist in Drive - "
                    f"skipping benchmarking for {backbone}"
                )
                benchmark_results[backbone] = benchmark_output
                continue
        else:
            # File is local - check and restore from Drive if needed
            if ensure_restored_from_drive and ensure_restored_from_drive(
                benchmark_output, False
            ):
                logger.info(
                    f"Restored benchmark results from Drive - "
                    f"skipping benchmarking for {backbone}"
                )
                benchmark_results[backbone] = benchmark_output
                continue

        logger.info(f"Benchmarking {backbone} ({trial_info['trial_name']})...")

        # Use run_ids directly if available (champion mode)
        hpo_trial_run_id = trial_info.get("trial_run_id")
        hpo_refit_run_id = trial_info.get("refit_run_id") or trial_info.get("run_id")
        hpo_sweep_run_id = trial_info.get("sweep_run_id")

        if not is_champion:
            # Legacy mode: validate and potentially look up run IDs from MLflow
            import re
            uuid_pattern = re.compile(
                r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                re.IGNORECASE
            )

            # Validate and potentially look up run IDs from MLflow
            if trial_key_hash:
                # Check if we need to look up trial run
                if not hpo_trial_run_id or not uuid_pattern.match(hpo_trial_run_id):
                    try:
                        client = _get_mlflow_client()
                        if client is None:
                            logger.warning("Could not create MLflow client for trial run lookup")
                            continue
                        
                        # Get experiment ID from benchmark tracker if available
                        experiment_ids_to_search = None
                        if benchmark_tracker and hasattr(benchmark_tracker, 'experiment_name'):
                            # Find HPO experiment by study_key_hash (most reliable)
                            if study_key_hash:
                                try:
                                    temp_runs = client.search_runs(
                                        filter_string=f"tags.code.study_key_hash = '{study_key_hash}'",
                                        max_results=1
                                    )
                                    if temp_runs:
                                        experiment_ids_to_search = [temp_runs[0].info.experiment_id]
                                        logger.info(
                                            f"[BENCHMARK] Found HPO experiment via study_key_hash: "
                                            f"experiment_id={experiment_ids_to_search[0]}"
                                        )
                                except Exception as e:
                                    logger.debug(f"Could not find HPO experiment via study_key_hash: {e}")
                        
                        # Search for trial run by trial_key_hash (CV trial, not refit)
                        runs = client.search_runs(
                            experiment_ids=experiment_ids_to_search if experiment_ids_to_search is not None else [],
                            filter_string=f"tags.code.trial_key_hash = '{trial_key_hash}' AND tags.code.stage = 'hpo'",
                            max_results=5
                        )
                        
                        if runs:
                            # Filter out refit runs manually (keep only hpo stage, exclude hpo_refit)
                            runs = [r for r in runs if r.data.tags.get("code.stage") == "hpo"]
                            if runs:
                                trial_run = runs[0]
                                hpo_trial_run_id = trial_run.info.run_id
                                logger.info(
                                    f"[BENCHMARK] Found trial run ID from MLflow: {hpo_trial_run_id[:12]}... "
                                    f"(via trial_key_hash={trial_key_hash[:16]}...)"
                                )
                            else:
                                logger.warning(
                                    f"[BENCHMARK] Could not find trial run in MLflow for trial_key_hash={trial_key_hash[:16]}..."
                                )
                        else:
                            logger.warning(
                                f"[BENCHMARK] Could not find trial run in MLflow for trial_key_hash={trial_key_hash[:16]}..."
                            )
                    except Exception as e:
                        logger.warning(f"Could not query MLflow for trial run ID: {e}", exc_info=True)

                # Check if we need to look up refit run
                if not hpo_refit_run_id or not uuid_pattern.match(hpo_refit_run_id):
                    try:
                        client = _get_mlflow_client()
                        if client is None:
                            logger.warning("Could not create MLflow client for refit run lookup")
                            continue
                        
                        # Get experiment ID from benchmark tracker if available
                        experiment_ids_to_search = None
                        if benchmark_tracker and hasattr(benchmark_tracker, 'experiment_name') and study_key_hash:
                            try:
                                temp_runs = client.search_runs(
                                    filter_string=f"tags.code.study_key_hash = '{study_key_hash}'",
                                    max_results=1
                                )
                                if temp_runs:
                                    experiment_ids_to_search = [temp_runs[0].info.experiment_id]
                            except Exception:
                                pass
                        
                        # Find refit run (same trial_key_hash with refit tag)
                        refit_runs = client.search_runs(
                            experiment_ids=experiment_ids_to_search if experiment_ids_to_search is not None else [],
                            filter_string=f"tags.code.trial_key_hash = '{trial_key_hash}' AND tags.code.stage = 'hpo_refit'",
                            max_results=1
                        )
                        if refit_runs:
                            refit_run = refit_runs[0]
                            hpo_refit_run_id = refit_run.info.run_id
                            logger.info(
                                f"[BENCHMARK] Found refit run ID from MLflow: {hpo_refit_run_id[:12]}..."
                            )
                        else:
                            logger.debug(
                                f"[BENCHMARK] Could not find refit run in MLflow for trial_key_hash={trial_key_hash[:16]}..."
                            )
                    except Exception as e:
                        logger.warning(f"Could not query MLflow for refit run ID: {e}", exc_info=True)

        logger.info(
            f"[BENCHMARK] Final run IDs: trial={hpo_trial_run_id[:12] if hpo_trial_run_id else None}..., "
            f"refit={hpo_refit_run_id[:12] if hpo_refit_run_id else None}..., "
            f"sweep={hpo_sweep_run_id[:12] if hpo_sweep_run_id else None}..."
        )

        # Build benchmark_key for idempotency (includes config hash)
        benchmark_key = None
        if benchmark_config and hpo_refit_run_id:
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
            except Exception as e:
                logger.warning(f"Could not build benchmark_key: {e}")

        success = run_benchmarking(
            checkpoint_dir=checkpoint_dir,
            test_data_path=test_data_path,
            output_path=benchmark_output,
            batch_sizes=benchmark_batch_sizes,
            iterations=benchmark_iterations,
            warmup_iterations=benchmark_warmup,
            max_length=benchmark_max_length,
            device=benchmark_device,
            project_root=root_dir,
            tracker=benchmark_tracker,
            backbone=backbone,
            benchmark_source="hpo_trial",
            study_key_hash=study_key_hash,
            trial_key_hash=trial_key_hash,
            trial_id=trial_id,
            hpo_trial_run_id=hpo_trial_run_id,
            hpo_refit_run_id=hpo_refit_run_id,
            hpo_sweep_run_id=hpo_sweep_run_id,
            benchmark_config_hash=benchmark_config_hash,
            benchmark_key=benchmark_key,
        )

        if success:
            benchmark_results[backbone] = benchmark_output
            logger.info(f"Benchmark completed: {benchmark_output}")

            # Note: On Colab, benchmark_output is already in Drive (via resolve_output_path_for_colab)
            # No need to backup again unless it's a local path
            if backup_enabled and backup_to_drive and not str(benchmark_output).startswith("/content/drive"):
                backup_to_drive(benchmark_output, False)
                logger.info("Backed up benchmark results to Drive")
            elif str(benchmark_output).startswith("/content/drive"):
                logger.info(
                    "Benchmark results are already in Drive (no backup needed)")
        else:
            logger.error(f"Benchmark failed for {backbone}")

    logger.info(
        f"Benchmarking complete. {len(benchmark_results)}/{len(best_trials)} trials benchmarked."
    )
    return benchmark_results
