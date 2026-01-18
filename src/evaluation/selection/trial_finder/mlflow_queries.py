"""MLflow query utilities for trial finding."""

from typing import Any, Dict, List, Tuple

from mlflow.tracking import MlflowClient

from common.constants.mlflow import (
    DEFAULT_MLFLOW_MAX_RESULTS,
    LARGE_MLFLOW_MAX_RESULTS,
    SMALL_MLFLOW_MAX_RESULTS,
    SAMPLE_MLFLOW_MAX_RESULTS,
)
from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def query_runs_with_fallback(
    mlflow_client: MlflowClient,
    experiment_id: str,
    backbone_name: str,
    backbone_tag: str,
    stage_tag: str,
) -> List[Any]:
    """Query MLflow runs with fallback strategies for legacy runs.
    
    Tries multiple tag combinations:
    1. backbone + stage="hpo_trial" (new format)
    2. stage="hpo_trial" only (legacy without backbone tag)
    3. backbone + stage="hpo" (legacy format)
    4. stage="hpo" only (legacy without backbone tag)
    
    Args:
        mlflow_client: MLflow client instance
        experiment_id: Experiment ID to query
        backbone_name: Model backbone name
        backbone_tag: Tag key for backbone
        stage_tag: Tag key for stage
        
    Returns:
        List of MLflow runs
    """
    from infrastructure.tracking.mlflow.queries import query_runs_by_tags
    
    # Try "hpo_trial" first (new format), with backbone tag
    required_tags_with_backbone = {
        backbone_tag: backbone_name,
        stage_tag: "hpo_trial",
    }
    
    logger.debug(
        f"Querying runs with tags: {backbone_tag}={backbone_name}, "
        f"{stage_tag}=hpo_trial"
    )
    
    runs = query_runs_by_tags(
        client=mlflow_client,
        experiment_ids=[experiment_id],
        required_tags=required_tags_with_backbone,
        max_results=DEFAULT_MLFLOW_MAX_RESULTS,
    )
    
    # If no runs found, try without backbone tag (legacy runs may not have it)
    if not runs:
        logger.debug(
            f"No runs found with backbone tag, trying without backbone filter "
            f"(experiment is already backbone-specific)"
        )
        required_tags_stage_only = {stage_tag: "hpo_trial"}
        runs = query_runs_by_tags(
            client=mlflow_client,
            experiment_ids=[experiment_id],
            required_tags=required_tags_stage_only,
            max_results=DEFAULT_MLFLOW_MAX_RESULTS,
        )
    
    # If still no runs, try legacy "hpo" stage tag (with backbone)
    if not runs:
        logger.info(
            f"No runs found with stage='hpo_trial' for {backbone_name}, "
            f"trying legacy stage='hpo'"
        )
        required_tags_with_backbone = {
            backbone_tag: backbone_name,
            stage_tag: "hpo",
        }
        runs = query_runs_by_tags(
            client=mlflow_client,
            experiment_ids=[experiment_id],
            required_tags=required_tags_with_backbone,
            max_results=DEFAULT_MLFLOW_MAX_RESULTS,
        )
    
    # If still no runs, try legacy "hpo" stage tag (without backbone)
    if not runs:
        logger.debug(
            f"No runs found with backbone tag and stage='hpo', "
            f"trying stage-only filter"
        )
        required_tags_stage_only = {stage_tag: "hpo"}
        runs = query_runs_by_tags(
            client=mlflow_client,
            experiment_ids=[experiment_id],
            required_tags=required_tags_stage_only,
            max_results=DEFAULT_MLFLOW_MAX_RESULTS,
        )
    
    logger.info(
        f"Found {len(runs)} runs with stage tag for {backbone_name} "
        f"(backbone={backbone_name})"
    )
    
    return runs


def partition_runs_by_schema_version(
    runs: List[Any],
    study_key_tag: str,
    schema_version_tag: str,
) -> Tuple[Dict[str, List[Any]], Dict[str, List[Any]], int]:
    """Partition runs by study_key_hash and schema version.
    
    Args:
        runs: List of MLflow runs
        study_key_tag: Tag key for study_key_hash
        schema_version_tag: Tag key for schema version
        
    Returns:
        Tuple of (groups_v1, groups_v2, runs_without_study_key)
    """
    groups_v1: Dict[str, List[Any]] = {}
    groups_v2: Dict[str, List[Any]] = {}
    runs_without_study_key = 0
    
    for run in runs:
        study_key_hash = run.data.tags.get(study_key_tag)
        if not study_key_hash:
            runs_without_study_key += 1
            continue
        
        # Check schema version (default to "2.0" if missing)
        schema_version = run.data.tags.get(schema_version_tag, "2.0")
        
        # Partition by version (NEVER MIX if allow_mixed_schema_groups is False)
        if schema_version == "2.0":
            if study_key_hash not in groups_v2:
                groups_v2[study_key_hash] = []
            groups_v2[study_key_hash].append(run)
        else:
            # v1 or missing version
            if study_key_hash not in groups_v1:
                groups_v1[study_key_hash] = []
            groups_v1[study_key_hash].append(run)
    
    return groups_v1, groups_v2, runs_without_study_key


def select_groups_by_schema_version(
    groups_v1: Dict[str, List[Any]],
    groups_v2: Dict[str, List[Any]],
    allow_mixed_schema_groups: bool,
    prefer_schema_version: str,
) -> Tuple[Dict[str, List[Any]], str]:
    """Select groups based on schema version preferences.
    
    Args:
        groups_v1: v1 groups
        groups_v2: v2 groups
        allow_mixed_schema_groups: Whether to allow mixing v1 and v2
        prefer_schema_version: Preferred schema version ("2.0" or "auto")
        
    Returns:
        Tuple of (groups_to_use, schema_version_used)
    """
    if allow_mixed_schema_groups:
        # WARNING: This is dangerous - only allow if explicitly enabled
        logger.warning(
            f"allow_mixed_schema_groups=True is enabled. "
            f"This may compare non-comparable runs. Use with caution."
        )
        return {**groups_v1, **groups_v2}, "mixed"
    
    # Use v2 only (v1 no longer supported)
    if prefer_schema_version == "2.0" or (prefer_schema_version == "auto" and groups_v2):
        return groups_v2, "2.0"
    elif prefer_schema_version == "auto" and not groups_v2:
        # Auto mode with no v2 groups - return empty (v1 no longer supported)
        logger.warning("No v2 groups found and v1 is no longer supported. Returning empty groups.")
        return {}, "2.0"
    else:
        # Default to v2
        return groups_v2 if groups_v2 else {}, "2.0"


def compute_group_scores(
    groups_to_use: Dict[str, List[Any]],
    objective_metric: str,
    maximize: bool,
    min_trials_per_group: int,
    top_k_for_stable_score: int,
) -> Tuple[Dict[str, Dict[str, Any]], int]:
    """Compute stable scores for each group.
    
    Args:
        groups_to_use: Groups to score
        objective_metric: Objective metric name
        maximize: Whether to maximize the metric
        min_trials_per_group: Minimum trials required per group
        top_k_for_stable_score: Top K trials to use for stable score
        
    Returns:
        Tuple of (group_scores, groups_skipped_min_trials)
    """
    import math
    
    import numpy as np
    
    group_scores = {}
    groups_skipped_min_trials = 0
    
    for study_key_hash, group_runs in groups_to_use.items():
        # Extract metrics (handle missing/NaN deterministically)
        run_metrics = []
        valid_count = 0
        invalid_count = 0
        missing_metric_runs = []
        invalid_metric_runs = []
        
        for run in group_runs:
            if objective_metric not in run.data.metrics:
                invalid_count += 1
                missing_metric_runs.append(run.info.run_id[:12])
                # Log available metrics for debugging
                available_metrics = list(run.data.metrics.keys())[:5]  # First 5 metrics
                logger.debug(
                    f"Run {run.info.run_id[:12]}... missing {objective_metric}. "
                    f"Available metrics: {available_metrics}"
                )
                continue
            
            metric_value = run.data.metrics[objective_metric]
            
            # Handle NaN/Inf deterministically
            if not isinstance(metric_value, (int, float)) or not math.isfinite(metric_value):
                invalid_count += 1
                invalid_metric_runs.append(run.info.run_id[:12])
                logger.debug(
                    f"Run {run.info.run_id[:12]}... has invalid {objective_metric}={metric_value}"
                )
                continue
            
            valid_count += 1
            run_metrics.append((run.info.run_id, metric_value))
        
        # Log metric validity with details
        if invalid_count > 0:
            logger.warning(
                f"Group {study_key_hash[:16]}...: "
                f"{valid_count} valid metrics, {invalid_count} missing/invalid. "
                f"Missing metric runs: {missing_metric_runs[:3]}{'...' if len(missing_metric_runs) > 3 else ''}"
            )
        
        # Winner's curse guardrail: require minimum trials
        if len(run_metrics) < min_trials_per_group:
            groups_skipped_min_trials += 1
            logger.warning(
                f"Skipping group {study_key_hash[:16]}... - "
                f"only {len(run_metrics)} valid trials (minimum: {min_trials_per_group})"
            )
            continue
        
        # Extract metrics for scoring
        metrics = [m for _, m in run_metrics]
        
        # Best metric (for champion selection within group)
        best_metric = max(metrics) if maximize else min(metrics)
        
        # Stable score: median of top-K (reduces flukes)
        # CONSTRAINT: top_k is already clamped to <= min_trials_per_group in config helper
        top_k = min(top_k_for_stable_score, len(metrics))
        sorted_metrics = sorted(metrics, reverse=maximize)
        stable_score = float(np.median(sorted_metrics[:top_k])) if top_k > 0 else 0.0
        
        group_scores[study_key_hash] = {
            "stable_score": stable_score,
            "best_metric": best_metric,
            "n_trials": len(run_metrics),
            "n_valid": valid_count,
            "n_invalid": invalid_count,
            "run_metrics": run_metrics,  # Lightweight: (run_id, metric) tuples
        }
    
    return group_scores, groups_skipped_min_trials

