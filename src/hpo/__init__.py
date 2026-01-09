"""Hyperparameter Optimization (HPO) module.

This module provides HPO functionality for both local (Optuna) and Azure ML execution.
"""

from __future__ import annotations

# Core exports
from hpo.core import (
    SearchSpaceTranslator,
    create_search_space,
    create_optuna_pruner,
    extract_best_config_from_study,
    import_optuna,
    translate_search_space_to_optuna,
)
from hpo.utils.helpers import (
    create_mlflow_run_name,
    create_study_name,
    generate_run_id,
    setup_checkpoint_storage,
)

# Checkpoint management
from hpo.checkpoint.storage import get_storage_uri, resolve_storage_path

# Execution
from hpo.execution.local.sweep import run_local_hpo_sweep
from hpo.execution.local.trial import TrialExecutor

# Azure ML-dependent imports (optional)
try:
    from hpo.execution.azureml.sweeps import (
        create_dry_run_sweep_job_for_backbone,
        create_hpo_sweep_job_for_backbone,
        validate_sweep_job,
    )
except ImportError:
    # Azure ML SDK not available; skip Azure-specific helpers.
    create_dry_run_sweep_job_for_backbone = None
    create_hpo_sweep_job_for_backbone = None
    validate_sweep_job = None

__all__ = [
    # Checkpoint management
    "get_storage_uri",
    "resolve_storage_path",
    # HPO helpers
    "create_mlflow_run_name",
    "create_study_name",
    "generate_run_id",
    "setup_checkpoint_storage",
    # Local sweeps
    "run_local_hpo_sweep",
    "translate_search_space_to_optuna",
    # Search space
    "SearchSpaceTranslator",
    "create_search_space",
    # Study extraction
    "extract_best_config_from_study",
    # Azure ML sweeps
    "create_dry_run_sweep_job_for_backbone",
    "create_hpo_sweep_job_for_backbone",
    "validate_sweep_job",
    # Trial execution
    "TrialExecutor",
]

