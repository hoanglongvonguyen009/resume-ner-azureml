from __future__ import annotations

"""
@meta
name: experiment_discovery
type: utility
domain: evaluation
responsibility:
  - Discover HPO and benchmark experiments from MLflow
  - Serve as single source of truth for experiment discovery
inputs:
  - Experiment names
  - MLflow client instances
outputs:
  - Experiment dictionaries
tags:
  - utility
  - evaluation
  - mlflow
lifecycle:
  status: active
"""

"""MLflow experiment discovery utilities.

This module provides functions to discover HPO and benchmark experiments
from MLflow, serving as a single source of truth for experiment discovery.
"""

from typing import Any, Dict, Optional

from mlflow.tracking import MlflowClient

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def discover_hpo_experiments(
    experiment_name: str,
    mlflow_client: Optional[MlflowClient] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Discover HPO experiments from MLflow.
    
    Finds all experiments matching the pattern: {experiment_name}-hpo-{backbone}
    
    Args:
        experiment_name: Base experiment name
        mlflow_client: MLflow client instance (creates new one if None)
    
    Returns:
        Dict mapping backbone -> {name, id}
        Example: {
            "distilbert": {"name": "exp-hpo-distilbert", "id": "123"},
            "roberta": {"name": "exp-hpo-roberta", "id": "456"}
        }
    """
    if mlflow_client is None:
        mlflow_client = MlflowClient()
    
    hpo_experiments = {}
    all_experiments = mlflow_client.search_experiments()
    
    for exp in all_experiments:
        if exp.name.startswith(f"{experiment_name}-hpo-"):
            backbone = exp.name.replace(f"{experiment_name}-hpo-", "")
            hpo_experiments[backbone] = {
                "name": exp.name,
                "id": exp.experiment_id
            }
    
    logger.info(f"Discovered {len(hpo_experiments)} HPO experiment(s) for {experiment_name}")
    return hpo_experiments


def discover_benchmark_experiment(
    experiment_name: str,
    mlflow_client: Optional[MlflowClient] = None,
    create_if_missing: bool = False,
) -> Optional[Dict[str, str]]:
    """
    Discover benchmark experiment from MLflow.
    
    Finds experiment matching: {experiment_name}-benchmark
    
    Args:
        experiment_name: Base experiment name
        mlflow_client: MLflow client instance (creates new one if None)
        create_if_missing: If True, create the experiment if it doesn't exist
    
    Returns:
        Dict with 'name' and 'id' keys, or None if not found and not created
    """
    if mlflow_client is None:
        mlflow_client = MlflowClient()
    
    benchmark_experiment_name = f"{experiment_name}-benchmark"
    all_experiments = mlflow_client.search_experiments()
    
    for exp in all_experiments:
        if exp.name == benchmark_experiment_name:
            logger.info(f"Found benchmark experiment: {benchmark_experiment_name}")
            return {
                "name": exp.name,
                "id": exp.experiment_id
            }
    
    # Not found - create if requested
    if create_if_missing:
        logger.info(f"Creating benchmark experiment: {benchmark_experiment_name}")
        benchmark_experiment_id = mlflow_client.create_experiment(benchmark_experiment_name)
        return {
            "name": benchmark_experiment_name,
            "id": benchmark_experiment_id
        }
    
    logger.debug(f"Benchmark experiment not found: {benchmark_experiment_name}")
    return None


def discover_all_experiments(
    experiment_name: str,
    mlflow_client: Optional[MlflowClient] = None,
    create_benchmark_if_missing: bool = False,
) -> Dict[str, Any]:
    """
    Discover all experiments (HPO and benchmark) in one call.
    
    This is the recommended function to use as it ensures consistency
    and serves as the single source of truth.
    
    Args:
        experiment_name: Base experiment name
        mlflow_client: MLflow client instance (creates new one if None)
        create_benchmark_if_missing: If True, create benchmark experiment if missing
    
    Returns:
        Dict with keys:
            - 'hpo_experiments': Dict[backbone, {name, id}]
            - 'benchmark_experiment': Dict with 'name' and 'id', or None
    """
    hpo_experiments = discover_hpo_experiments(experiment_name, mlflow_client)
    benchmark_experiment = discover_benchmark_experiment(
        experiment_name,
        mlflow_client,
        create_if_missing=create_benchmark_if_missing,
    )
    
    return {
        "hpo_experiments": hpo_experiments,
        "benchmark_experiment": benchmark_experiment,
    }

