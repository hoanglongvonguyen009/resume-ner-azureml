"""
@meta
name: queries
type: utility
domain: tracking
responsibility:
  - MLflow query patterns for reusable querying logic
  - Extract common MLflow query patterns for reuse
inputs:
  - MLflow client
  - Experiment IDs
  - Tag filters
outputs:
  - Filtered MLflow runs
tags:
  - utility
  - tracking
  - mlflow
  - queries
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow query patterns for reusable querying logic.

Extracts common MLflow query patterns from mlflow_selection.py for reuse
across the codebase (DRY principle).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mlflow.tracking import MlflowClient


def query_runs_by_tags(
    client: MlflowClient,
    experiment_ids: List[str],
    required_tags: Dict[str, str],
    filter_string: str = "",
    max_results: int = 1000,
) -> List[Any]:
    """
    Query MLflow runs filtered by required tags.
    
    Reuses pattern from mlflow_selection.py.
    
    Args:
        client: MLflow client
        experiment_ids: List of experiment IDs to query
        required_tags: Dict of tag_key -> tag_value to filter by
        filter_string: Additional MLflow filter string
        max_results: Maximum number of results
    
    Returns:
        List of runs matching criteria (only FINISHED runs)
    """
    all_runs = client.search_runs(
        experiment_ids=experiment_ids,
        filter_string=filter_string,
        max_results=max_results,
    )
    
    # Filter for finished runs
    finished_runs = [r for r in all_runs if r.info.status == "FINISHED"]
    
    # Filter by required tags
    valid_runs = []
    for run in finished_runs:
        has_all_tags = all(
            run.data.tags.get(tag_key) == tag_value
            for tag_key, tag_value in required_tags.items()
        )
        if has_all_tags:
            valid_runs.append(run)
    
    return valid_runs


def find_best_run_by_metric(
    runs: List[Any],
    metric_name: str,
    maximize: bool = True,
) -> Optional[Any]:
    """
    Select best run by metric value.
    
    Args:
        runs: List of MLflow runs
        metric_name: Name of metric to optimize
        maximize: True to maximize, False to minimize
    
    Returns:
        Best run or None if no runs have metric
    """
    runs_with_metric = [
        r for r in runs
        if metric_name in r.data.metrics
    ]
    
    if not runs_with_metric:
        return None
    
    if maximize:
        return max(runs_with_metric, key=lambda r: r.data.metrics[metric_name])
    else:
        return min(runs_with_metric, key=lambda r: r.data.metrics[metric_name])


def group_runs_by_variant(
    runs: List[Any],
    variant_tag: str = "code.variant",
) -> Dict[str, List[Any]]:
    """
    Group runs by variant tag.
    
    Args:
        runs: List of MLflow runs
        variant_tag: Tag key for variant (default: "code.variant")
    
    Returns:
        Dict mapping variant -> list of runs
    """
    grouped = {}
    for run in runs:
        variant = run.data.tags.get(variant_tag, "default")
        if variant not in grouped:
            grouped[variant] = []
        grouped[variant].append(run)
    return grouped

