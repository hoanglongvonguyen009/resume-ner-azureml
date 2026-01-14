from __future__ import annotations

"""
@meta
name: artifact_unified_selectors
type: utility
domain: selection
responsibility:
  - Run selector with trial→refit mapping (SSOT)
  - Determine which MLflow run to use for artifact acquisition
  - Map trial runs to refit runs
inputs:
  - Trial run IDs
  - MLflow client
  - Experiment IDs
outputs:
  - Run selector results with artifact run IDs
tags:
  - utility
  - selection
  - artifacts
  - mlflow
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Run selector with trial→refit mapping (SSOT).

This module provides the single source of truth for trial→refit run mapping.
All artifact acquisition should use this module to determine which run to use.
"""
from typing import Any, Dict, Optional

from mlflow.tracking import MlflowClient

from pathlib import Path
from typing import Optional

from common.shared.logging_utils import get_logger
from evaluation.selection.artifact_unified.types import ArtifactRequest, RunSelectorResult

logger = get_logger(__name__)

# MLflow query limits
SMALL_MLFLOW_MAX_RESULTS = 10  # Small limit for targeted queries


def select_artifact_run(
    trial_run_id: str,
    mlflow_client: MlflowClient,
    experiment_id: str,
    trial_key_hash: Optional[str] = None,
    config_dir: Optional[Any] = None,
) -> RunSelectorResult:
    """
    Select the appropriate run for artifact acquisition (trial→refit mapping).
    
    This is the SINGLE SOURCE OF TRUTH for trial→refit mapping.
    All artifact acquisition should use this function to determine which run to use.
    
    Priority:
    1. Refit run (if available) - checkpoints are usually in refit runs
    2. Trial run (fallback) - use trial run if no refit exists
    
    Args:
        trial_run_id: MLflow run ID of the trial run
        mlflow_client: MLflow client instance
        experiment_id: MLflow experiment ID
        trial_key_hash: Optional trial key hash for more reliable refit lookup
        config_dir: Optional config directory for tag registry
        
    Returns:
        RunSelectorResult with artifact_run_id set to refit (if available) or trial
        
    Raises:
        ValueError: If trial run not found or critical errors occur
    """
    # Load tag registry if config_dir provided
    tags_registry = None
    if config_dir:
        try:
            from infrastructure.naming.mlflow.tags_registry import load_tags_registry
            tags_registry = load_tags_registry(config_dir)
        except Exception as e:
            logger.debug(f"Could not load tag registry: {e}")
    
    # Get tag keys
    refit_of_trial_tag = "code.refit.of_trial_run_id"
    stage_tag = "code.stage"
    trial_key_tag = "code.trial_key_hash"
    
    if tags_registry:
        try:
            refit_of_trial_tag = tags_registry.key("refit", "of_trial_run_id")
            stage_tag = tags_registry.key("process", "stage")
            trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
        except Exception:
            pass  # Use defaults
    
    refit_run_id = None
    refit_runs = []
    
    try:
        # Strategy 1: Search by trial_key_hash + stage (most reliable)
        if trial_key_hash:
            try:
                refit_runs = mlflow_client.search_runs(
                    experiment_ids=[experiment_id],
                    filter_string=(
                        f"tags.{trial_key_tag} = '{trial_key_hash}' "
                        f"AND tags.{stage_tag} = 'hpo_refit'"
                    ),
                    max_results=SMALL_MLFLOW_MAX_RESULTS,
                )
                if refit_runs:
                    logger.debug(
                        f"Found {len(refit_runs)} refit run(s) using trial_key_hash search"
                    )
            except Exception as search_error:
                logger.debug(f"Search by trial_key_hash failed: {search_error}")
                refit_runs = []
        
        # Strategy 2: Fallback - search by linking tag
        if not refit_runs:
            try:
                refit_runs = mlflow_client.search_runs(
                    experiment_ids=[experiment_id],
                    filter_string=f"tags.{refit_of_trial_tag} = '{trial_run_id}'",
                    max_results=SMALL_MLFLOW_MAX_RESULTS,
                )
                if refit_runs:
                    logger.debug(
                        f"Found {len(refit_runs)} refit run(s) using linking tag "
                        f"for trial {trial_run_id[:12]}..."
                    )
            except Exception as search_error:
                logger.debug(
                    f"Linking tag search failed (may be filter syntax issue): {search_error}"
                )
                refit_runs = []
        
        if refit_runs:
            # If multiple refit runs exist (reruns), pick the latest by start_time
            refit_runs_sorted = sorted(
                refit_runs,
                key=lambda r: r.info.start_time if r.info.start_time else 0,
                reverse=True,
            )
            refit_run_id = refit_runs_sorted[0].info.run_id
            logger.info(
                f"Found refit run {refit_run_id[:12]}... for trial {trial_run_id[:12]}... "
                f"(selected latest from {len(refit_runs)} refit run(s))"
            )
        else:
            # No refit found - this is OK for some workflows (e.g., CV-only trials)
            logger.debug(
                f"No refit run found for trial {trial_run_id[:12]}... "
                f"(will use trial run for artifact acquisition)"
            )
    
    except Exception as e:
        logger.warning(
            f"Error during refit run lookup for trial {trial_run_id[:12]}...: {e}. "
            f"Will use trial run as fallback."
        )
        refit_run_id = None
    
    # Determine artifact_run_id (prefer refit, fallback to trial)
    artifact_run_id = refit_run_id or trial_run_id
    
    return RunSelectorResult(
        trial_run_id=trial_run_id,
        refit_run_id=refit_run_id,
        artifact_run_id=artifact_run_id,
        metadata={
            "refit_found": refit_run_id is not None,
            "selection_strategy": "refit_preferred" if refit_run_id else "trial_fallback",
        },
    )


def select_artifact_run_from_request(
    request: ArtifactRequest,
    mlflow_client: MlflowClient,
    experiment_id: str,
    config_dir: Optional[Path] = None,
) -> RunSelectorResult:
    """
    Select artifact run from ArtifactRequest.
    
    Convenience wrapper around select_artifact_run() that extracts parameters from request.
    
    Args:
        request: ArtifactRequest instance
        mlflow_client: MLflow client instance
        experiment_id: MLflow experiment ID
        config_dir: Optional config directory for tag registry
        
    Returns:
        RunSelectorResult with artifact_run_id set appropriately
    """
    # If refit_run_id is already provided in request, use it directly
    if request.refit_run_id:
        return RunSelectorResult(
            trial_run_id=request.run_id,
            refit_run_id=request.refit_run_id,
            artifact_run_id=request.refit_run_id,
            metadata={
                "refit_found": True,
                "selection_strategy": "refit_provided",
            },
        )
    
    # Otherwise, perform lookup
    return select_artifact_run(
        trial_run_id=request.run_id,
        mlflow_client=mlflow_client,
        experiment_id=experiment_id,
        trial_key_hash=request.trial_key_hash,
        config_dir=config_dir,
    )

