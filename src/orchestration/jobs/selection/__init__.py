"""Configuration selection utilities.

This module provides functionality for selecting the best configuration from HPO results,
supporting both local (Optuna) and Azure ML selection methods.
"""

from __future__ import annotations

from .disk_loader import load_benchmark_speed_score, load_best_trial_from_disk
from .local_selection import (
    extract_best_config_from_study,
    load_best_trial_from_disk as load_best_trial,
    select_best_configuration_across_studies,
)
from .selection import select_best_configuration

# Alias for backward compatibility
select_production_configuration = select_best_configuration
from .selection_logic import MODEL_SPEED_SCORES, SelectionLogic

__all__ = [
    # Disk loading
    "load_benchmark_speed_score",
    "load_best_trial_from_disk",
    "load_best_trial",
    # Local selection
    "extract_best_config_from_study",
    "select_best_configuration_across_studies",
    # Azure ML selection
    "select_production_configuration",
    # Selection logic
    "MODEL_SPEED_SCORES",
    "SelectionLogic",
]

