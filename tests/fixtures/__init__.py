"""Shared test fixtures and helpers.

This module provides reusable fixtures and utilities for tests across the codebase.
"""

from fixtures.datasets import tiny_dataset, create_dataset_structure
from fixtures.mlflow import (
    mock_mlflow_tracking,
    mock_mlflow_client,
    mock_mlflow_run,
)
from fixtures.configs import (
    hpo_config_smoke,
    hpo_config_minimal,
    selection_config_default,
    acquisition_config_default,
    conversion_config_default,
)
from fixtures.validators import (
    validate_path_structure,
    validate_run_name,
    validate_tags,
)

__all__ = [
    # Datasets
    "tiny_dataset",
    "create_dataset_structure",
    # MLflow
    "mock_mlflow_tracking",
    "mock_mlflow_client",
    "mock_mlflow_run",
    # Configs
    "hpo_config_smoke",
    "hpo_config_minimal",
    "selection_config_default",
    "acquisition_config_default",
    "conversion_config_default",
    # Validators
    "validate_path_structure",
    "validate_run_name",
    "validate_tags",
]

