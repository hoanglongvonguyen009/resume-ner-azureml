"""
@meta
name: selection_workflow
type: utility
domain: selection
responsibility:
  - Orchestrate best model selection from MLflow
  - Coordinate checkpoint acquisition with fallback strategies
  - Cache selection results for idempotency
inputs:
  - MLflow benchmark and HPO experiments
  - Selection configuration
  - Artifact acquisition configuration
outputs:
  - Best model metadata
  - Checkpoint directory path
tags:
  - workflow
  - mlflow
  - selection
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Best model selection workflow."""

from pathlib import Path
from typing import Dict, Any, Optional, Callable, Tuple

import mlflow
from mlflow.tracking import MlflowClient

from evaluation.selection.mlflow_selection import find_best_model_from_mlflow
from evaluation.selection.cache import load_cached_best_model, save_best_model_cache
from evaluation.selection.artifact_acquisition import acquire_best_model_checkpoint
from evaluation.selection.workflows.utils import validate_checkpoint_for_reuse
from infrastructure.tracking.mlflow.queries import query_runs_by_tags
from common.shared.logging_utils import get_logger

logger = get_logger(__name__)

# Constants
MAX_MLFLOW_SEARCH_RESULTS = 100  # Maximum results to fetch from MLflow search


def run_selection_workflow(
    benchmark_experiment: Dict[str, str],
    hpo_experiments: Dict[str, Dict[str, str]],
    selection_config: Dict[str, Any],
    tags_config: Dict[str, Any],
    root_dir: Path,
    config_dir: Path,
    experiment_name: str,
    acquisition_config: Dict[str, Any],
    platform: str = "local",
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    drive_store: Optional[Callable[[Path, bool], bool]] = None,
    in_colab: bool = False,
    benchmarked_champions_by_refit: Optional[Dict[str, Dict[str, Any]]] = None,
    benchmarked_champions_by_keys: Optional[Dict[Tuple[str, str, str], Dict[str, Any]]] = None,
) -> Tuple[Dict[str, Any], Path]:
    """
    Run complete best model selection workflow.
    
    Steps:
    1. Check cache (if run.mode == reuse_if_exists)
    2. Find best model from MLflow (if not cached)
    3. Save to cache (if not cached)
    4. Acquire checkpoint (with reuse from benchmarking if available)
    5. Return best model and checkpoint path
    
    Args:
        benchmark_experiment: Benchmark experiment info (name, id)
        hpo_experiments: Dict mapping backbone -> experiment info (name, id)
        selection_config: Selection configuration dict
        tags_config: Tags configuration dict
        root_dir: Project root directory
        config_dir: Config directory
        experiment_name: Experiment name
        acquisition_config: Artifact acquisition configuration dict
        platform: Platform name (local, colab, kaggle)
        restore_from_drive: Function to restore files from Drive
        drive_store: Function to backup files to Drive
        in_colab: Whether running in Colab
        benchmarked_champions_by_refit: Optional dict mapping refit_run_id -> champion data
        benchmarked_champions_by_keys: Optional dict mapping (backbone, study_hash, trial_hash) -> champion data
        
    Returns:
        Tuple of (best_model dict, checkpoint_path Path)
        
    Raises:
        ValueError: If best model cannot be found
    """
    # Validate experiments
    if benchmark_experiment is None:
        raise ValueError("Benchmark experiment not found. Run benchmark jobs first.")
    if not hpo_experiments:
        raise ValueError("No HPO experiments found. Run HPO jobs first.")
    
    # Step 1: Check cache
    run_mode = selection_config.get("run", {}).get("mode", "reuse_if_exists")
    logger.info(f"Best Model Selection Mode: {run_mode}")
    
    best_model = None
    cache_data = None
    
    if run_mode == "reuse_if_exists":
        tracking_uri = mlflow.get_tracking_uri()
        cache_data = load_cached_best_model(
            root_dir=root_dir,
            config_dir=config_dir,
            experiment_name=experiment_name,
            selection_config=selection_config,
            tags_config=tags_config,
            benchmark_experiment_id=benchmark_experiment["id"],
            tracking_uri=tracking_uri,
        )
        
        if cache_data:
            best_model = cache_data["best_model"]
            logger.info("Using cached best model selection")
    
    # Step 2: Find best model from MLflow (if not cached)
    if best_model is None:
        if run_mode == "force_new":
            logger.info("Mode is 'force_new' - querying MLflow for fresh selection")
        else:
            logger.info("Cache not available or invalid - querying MLflow")
        
        best_model = find_best_model_from_mlflow(
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tags_config=tags_config,
            selection_config=selection_config,
        )
        
        if best_model is None:
            # Provide diagnostic information
            client = MlflowClient()
            from infrastructure.naming.mlflow.tags_registry import load_tags_registry
            tags_registry = load_tags_registry(config_dir)
            study_key_tag = tags_registry.key("grouping", "study_key_hash")
            trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
            
            # Check benchmark experiment (use queries SSOT)
            finished_benchmark_runs = query_runs_by_tags(
                client=client,
                experiment_ids=[benchmark_experiment["id"]],
                required_tags={},  # No tag filtering for diagnostics
                filter_string="",
                max_results=MAX_MLFLOW_SEARCH_RESULTS,
            )
            
            # Check HPO experiments
            hpo_run_counts = {}
            hpo_trial_runs = []
            hpo_refit_runs = []
            stage_tag = tags_registry.key("process", "stage")
            
            for backbone, exp_info in hpo_experiments.items():
                # Use queries SSOT for diagnostics
                finished_hpo_runs = query_runs_by_tags(
                    client=client,
                    experiment_ids=[exp_info["id"]],
                    required_tags={},  # No tag filtering for diagnostics
                    filter_string="",
                    max_results=MAX_MLFLOW_SEARCH_RESULTS,
                )
                hpo_run_counts[backbone] = len(finished_hpo_runs)
                
                for run in finished_hpo_runs:
                    stage = run.data.tags.get(stage_tag, "")
                    if stage == "hpo" or stage == "hpo_trial":
                        hpo_trial_runs.append(run)
                    elif stage == "hpo_refit":
                        hpo_refit_runs.append(run)
            
            # Collect unique pairs
            benchmark_pairs = set()
            for run in finished_benchmark_runs:
                study_hash = run.data.tags.get(study_key_tag)
                trial_hash = run.data.tags.get(trial_key_tag)
                if study_hash and trial_hash:
                    benchmark_pairs.add((study_hash, trial_hash))
            
            hpo_trial_pairs = set()
            for run in hpo_trial_runs:
                study_hash = run.data.tags.get(study_key_tag)
                trial_hash = run.data.tags.get(trial_key_tag)
                if study_hash and trial_hash:
                    hpo_trial_pairs.add((study_hash, trial_hash))
            
            hpo_refit_pairs = set()
            for run in hpo_refit_runs:
                study_hash = run.data.tags.get(study_key_tag)
                trial_hash = run.data.tags.get(trial_key_tag)
                if study_hash and trial_hash:
                    hpo_refit_pairs.add((study_hash, trial_hash))
            
            matching_pairs = benchmark_pairs & hpo_trial_pairs
            
            error_msg = (
                "Could not find best model from MLflow.\n\n"
                "Diagnostics:\n"
                f"  - Benchmark experiment '{benchmark_experiment['name']}': "
                f"{len(finished_benchmark_runs)} finished run(s) found\n"
                f"    - Unique (study_hash, trial_hash) pairs: {len(benchmark_pairs)}\n"
            )
            
            if hpo_run_counts:
                error_msg += "  - HPO experiments:\n"
                for backbone, count in hpo_run_counts.items():
                    error_msg += f"    - {backbone}: {count} finished run(s) found\n"
                error_msg += (
                    f"    - HPO trial runs: {len(hpo_trial_runs)} with {len(hpo_trial_pairs)} unique pairs\n"
                    f"    - HPO refit runs: {len(hpo_refit_runs)} with {len(hpo_refit_pairs)} unique pairs\n"
                )
            
            error_msg += (
                f"\n  - Matching pairs: {len(matching_pairs)} out of {len(benchmark_pairs)} benchmark pairs\n"
            )
            
            if len(matching_pairs) == 0 and len(benchmark_pairs) > 0 and len(hpo_trial_pairs) > 0:
                error_msg += "\n  Sample benchmark (study_hash, trial_hash) pairs:\n"
                for i, (s, t) in enumerate(list(benchmark_pairs)[:3]):
                    error_msg += f"    {i+1}. study={s[:16]}..., trial={t[:16]}...\n"
                
                error_msg += "\n  Sample HPO trial (study_hash, trial_hash) pairs:\n"
                for i, (s, t) in enumerate(list(hpo_trial_pairs)[:3]):
                    error_msg += f"    {i+1}. study={s[:16]}..., trial={t[:16]}...\n"
                
                error_msg += (
                    "\n  ⚠️  Hash mismatch detected! This usually means:\n"
                    "     - Benchmark runs were created from different trials than current HPO runs\n"
                    "     - Study or trial hashes changed between runs (e.g., Phase 2 migration)\n"
                    "     - Solution: Re-run benchmarking on champions to create new benchmark runs\n"
                )
            
            error_msg += (
                "\nPossible causes:\n"
                "  1. No benchmark runs have been executed yet. Run benchmark jobs first.\n"
                "  2. Benchmark runs exist but are missing required metrics or grouping tags.\n"
                "  3. HPO runs exist but are missing required metrics or grouping tags.\n"
                "  4. No matching runs found between benchmark and HPO experiments (hash mismatch).\n"
            )
            
            raise ValueError(error_msg)
        
        # Step 3: Save to cache
        tracking_uri = mlflow.get_tracking_uri()
        inputs_summary: Dict[str, Any] = {}
        
        save_best_model_cache(
            root_dir=root_dir,
            config_dir=config_dir,
            best_model=best_model,
            experiment_name=experiment_name,
            selection_config=selection_config,
            tags_config=tags_config,
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tracking_uri=tracking_uri,
            inputs_summary=inputs_summary,
        )
        logger.info("Saved best model selection to cache")
    
    # Step 4: Acquire checkpoint (with reuse from benchmarking if available)
    best_model_checkpoint_path = None
    reuse_reason = None
    
    # Initialize dictionaries if not provided
    if benchmarked_champions_by_refit is None:
        benchmarked_champions_by_refit = {}
    if benchmarked_champions_by_keys is None:
        benchmarked_champions_by_keys = {}
    
    # Primary match: refit_run_id
    best_refit_run_id = best_model.get("refit_run_id")
    if best_refit_run_id and best_refit_run_id in benchmarked_champions_by_refit:
        cached = benchmarked_champions_by_refit[best_refit_run_id]
        checkpoint_path = cached["checkpoint_path"]
        
        if validate_checkpoint_for_reuse(checkpoint_path, best_refit_run_id):
            best_model_checkpoint_path = checkpoint_path
            reuse_reason = f"refit_run_id={best_refit_run_id[:12]}..."
        else:
            logger.warning(f"Checkpoint validation failed for {best_refit_run_id[:12]}..., will re-acquire")
    
    # Fallback match: (backbone, study_key_hash, trial_key_hash)
    if best_model_checkpoint_path is None:
        fallback_backbone: Optional[str] = best_model.get("backbone")
        study_key_hash: Optional[str] = best_model.get("study_key_hash")
        trial_key_hash: Optional[str] = best_model.get("trial_key_hash")
        
        if fallback_backbone and study_key_hash and trial_key_hash:
            key = (fallback_backbone, study_key_hash, trial_key_hash)
            if key in benchmarked_champions_by_keys:
                cached = benchmarked_champions_by_keys[key]
                checkpoint_path = cached["checkpoint_path"]
                refit_run_id = cached.get("refit_run_id")
                
                if validate_checkpoint_for_reuse(checkpoint_path, refit_run_id):
                    best_model_checkpoint_path = checkpoint_path
                    reuse_reason = f"keys=(backbone={fallback_backbone}, study={study_key_hash[:8]}..., trial={trial_key_hash[:8]}...)"
                else:
                    logger.warning(f"Checkpoint validation failed for {fallback_backbone}/{study_key_hash[:8]}..., will re-acquire")
    
    # Use cached checkpoint or acquire new one
    if best_model_checkpoint_path:
        logger.info(f"Reusing checkpoint from benchmarking step ({reuse_reason})")
        best_checkpoint_dir = best_model_checkpoint_path
    else:
        logger.info("Acquiring checkpoint for best model...")
        best_checkpoint_dir = acquire_best_model_checkpoint(
            best_run_info=best_model,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config=selection_config,
            platform=platform,
            restore_from_drive=restore_from_drive,
            drive_store=drive_store,
            in_colab=in_colab,
        )
    
    logger.info(f"Best model checkpoint available at: {best_checkpoint_dir}")
    
    return best_model, Path(best_checkpoint_dir)


