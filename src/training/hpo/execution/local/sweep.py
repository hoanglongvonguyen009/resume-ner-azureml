"""
@meta
name: local_hpo_sweep
type: script
domain: hpo
responsibility:
  - Run local HPO sweeps using Optuna
  - Coordinate trial execution
  - Manage MLflow tracking
  - Handle checkpoint cleanup
inputs:
  - HPO configuration
  - Training configuration
  - Dataset path
outputs:
  - Optuna study with completed trials
  - Trial checkpoints
  - MLflow HPO runs
tags:
  - orchestration
  - hpo
  - optuna
  - mlflow
ci:
  runnable: true
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

"""Local hyperparameter optimization using Optuna.

This module has been refactored into focused submodules:
- sweep.types: Parameter Objects (dataclasses)
- sweep.setup: Setup logic (to be extracted)
- sweep.execution: Execution logic (to be extracted)
- sweep.cleanup: Cleanup logic (to be extracted)
- sweep.cv_setup: CV setup logic (to be extracted)
- sweep.objective: Objective function creation (to be extracted)
- sweep.tagging: Tagging logic (to be extracted)

This file maintains backward compatibility by re-exporting all public APIs.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

# Re-export from original file for backward compatibility
# TODO: Extract functions into focused modules incrementally
from training.hpo.execution.local.sweep_original import (
    create_local_hpo_objective,
    run_local_hpo_sweep,
    _set_phase2_hpo_tags,
)

# Re-export other functions
from training.hpo.execution.local.trial import run_training_trial
from training.hpo.execution.local.cv import run_training_trial_with_cv
from training.hpo.execution.local.refit import run_refit_training
from training.hpo.core.optuna_integration import create_optuna_pruner

__all__ = [
    "run_training_trial",
    "run_training_trial_with_cv",
    "create_optuna_pruner",
    "create_local_hpo_objective",
    "run_refit_training",
    "run_local_hpo_sweep",
]
