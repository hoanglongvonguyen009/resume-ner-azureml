"""Hyperparameter Optimization (HPO) utilities.

DEPRECATED: This module is maintained for backward compatibility only.
Please import from `hpo` module directly instead.

Example:
    # Old (deprecated):
    from orchestration.jobs.hpo import run_local_hpo_sweep
    
    # New (preferred):
    from hpo import run_local_hpo_sweep
"""

from __future__ import annotations

import warnings

# Re-export all public functions from hpo/ module
from training.hpo import (
    # Checkpoint management
    get_storage_uri,
    resolve_storage_path,
    # HPO helpers
    create_mlflow_run_name,
    create_study_name,
    generate_run_id,
    setup_checkpoint_storage,
    # Local sweeps
    run_local_hpo_sweep,
    translate_search_space_to_optuna,
    # Search space
    SearchSpaceTranslator,
    create_search_space,
    # Study extraction
    extract_best_config_from_study,
    # Azure ML sweeps
    create_dry_run_sweep_job_for_backbone,
    create_hpo_sweep_job_for_backbone,
    validate_sweep_job,
    # Trial execution
    TrialExecutor,
)

# Re-export backup function (still in old location, not moved per plan)
from orchestration.jobs.hpo.local.backup import backup_hpo_study_to_drive

# Re-export trial meta function
from training.hpo.trial.meta import generate_missing_trial_meta_for_all_studies

# Issue deprecation warning on import
warnings.warn(
    "Importing from 'orchestration.jobs.hpo' is deprecated. "
    "Please use 'hpo' module directly instead. "
    "Example: 'from hpo import run_local_hpo_sweep'",
    DeprecationWarning,
    stacklevel=2,
)

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
    "translate_search_space",
    # Study extraction
    "extract_best_config_from_study",
    # Azure ML sweeps
    "create_dry_run_sweep_job_for_backbone",
    "create_hpo_sweep_job_for_backbone",
    "validate_sweep_job",
    # Trial execution
    "TrialExecutor",
    # Backup utilities
    "backup_hpo_study_to_drive",
    # Trial meta
    "generate_missing_trial_meta_for_all_studies",
]
