"""Shared test fixtures and helpers.

This module provides reusable fixtures and utilities for tests across the codebase.
"""

from fixtures.datasets import tiny_dataset, create_dataset_structure
from fixtures.mlflow import (
    mock_mlflow_tracking,
    mock_mlflow_client,
    mock_mlflow_setup,
    mock_mlflow_run,
    mock_hpo_trial_run,
    mock_benchmark_run,
    mock_refit_run,
    mock_final_training_run,
    create_mock_mlflow_client,
    create_mock_run,
    clean_mlflow_db,
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
from fixtures.config_dirs import (
    config_dir,
    config_dir_minimal,
    config_dir_full,
    create_config_dir_files,
)
from fixtures.config_helpers import (
    create_minimal_training_config,
    create_minimal_data_config,
    create_minimal_experiment_config,
    create_minimal_model_config,
)

__all__ = [
    # Datasets
    "tiny_dataset",
    "create_dataset_structure",
    # MLflow
    "mock_mlflow_tracking",
    "mock_mlflow_client",
    "mock_mlflow_setup",
    "mock_mlflow_run",
    "mock_hpo_trial_run",
    "mock_benchmark_run",
    "mock_refit_run",
    "mock_final_training_run",
    "create_mock_mlflow_client",
    "create_mock_run",
    "clean_mlflow_db",
    # Configs
    "hpo_config_smoke",
    "hpo_config_minimal",
    "selection_config_default",
    "acquisition_config_default",
    "conversion_config_default",
    # Config directories
    "config_dir",
    "config_dir_minimal",
    "config_dir_full",
    "create_config_dir_files",
    # Config helpers
    "create_minimal_training_config",
    "create_minimal_data_config",
    "create_minimal_experiment_config",
    "create_minimal_model_config",
    # Validators
    "validate_path_structure",
    "validate_run_name",
    "validate_tags",
]

