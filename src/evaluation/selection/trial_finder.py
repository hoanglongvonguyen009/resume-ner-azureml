"""
@meta
name: trial_finder
type: utility
domain: selection
responsibility:
  - Find best trials from HPO studies or disk
  - Locate trial directories by hash or number
  - Extract trial information from Optuna studies
inputs:
  - Optuna study objects
  - HPO output directories
  - Trial metadata
outputs:
  - Best trial information dictionaries
tags:
  - utility
  - selection
  - hpo
  - optuna
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Find best trials from HPO studies or disk.

This module provides utilities to locate and extract best trial information
from Optuna studies or from saved outputs on disk.

This module has been refactored into focused submodules:
- trial_finder.mlflow_queries: MLflow query logic
- trial_finder.directory_ops: Directory operations
- trial_finder.champion_selection: Champion selection logic
- trial_finder.discovery: Trial discovery
- trial_finder.hash_utils: Hash computation utilities
- trial_finder.config: Parameter Objects (TypedDicts)

This file maintains backward compatibility by re-exporting all public APIs.
"""

# Re-export constants for backward compatibility
from evaluation.selection.trial_finder.mlflow_queries import (
    DEFAULT_MLFLOW_MAX_RESULTS,
    LARGE_MLFLOW_MAX_RESULTS,
    SAMPLE_MLFLOW_MAX_RESULTS,
    SMALL_MLFLOW_MAX_RESULTS,
)

# Re-export public functions from extracted modules for backward compatibility
from evaluation.selection.trial_finder.champion_selection import (
    select_champion_per_backbone,
    select_champions_for_backbones,
)

from evaluation.selection.trial_finder.discovery import (
    find_best_trial_from_study,
    find_best_trial_in_study_folder,
    find_best_trials_for_backbones,
    find_study_folder_in_backbone_dir,
)

from evaluation.selection.trial_finder.trial_finder import (
    format_trial_identifier,
)

# Re-export directory operations (for backward compatibility with code that might use private functions)
from evaluation.selection.trial_finder.directory_ops import (
    build_trial_result_dict as _build_trial_result_dict,
    extract_hashes_from_trial_dir as _extract_hashes_from_trial_dir,
    find_metrics_file as _find_metrics_file,
    find_trial_dir_by_hash as _find_trial_dir_by_hash,
    find_trial_dir_by_number as _find_trial_dir_by_number,
    read_trial_meta as _read_trial_meta,
)

# Re-export hash utilities (for backward compatibility)
from evaluation.selection.trial_finder.hash_utils import (
    compute_trial_key_hash_from_study as _compute_trial_key_hash_from_study,
)

# Re-export MLflow query functions (for backward compatibility)
from evaluation.selection.trial_finder.mlflow_queries import (
    compute_group_scores as _compute_group_scores,
    partition_runs_by_schema_version as _partition_runs_by_schema_version,
    query_runs_with_fallback as _query_runs_with_fallback,
    select_groups_by_schema_version as _select_groups_by_schema_version,
)

# Re-export champion selection helpers (for backward compatibility)
from evaluation.selection.trial_finder.champion_selection import (
    filter_by_artifact_availability as _filter_by_artifact_availability,
    get_checkpoint_path_from_run as _get_checkpoint_path_from_run,
)

__all__ = [
    # Constants
    "DEFAULT_MLFLOW_MAX_RESULTS",
    "LARGE_MLFLOW_MAX_RESULTS",
    "SMALL_MLFLOW_MAX_RESULTS",
    "SAMPLE_MLFLOW_MAX_RESULTS",
    # Public API functions
    "find_best_trial_from_study",
    "find_best_trial_in_study_folder",
    "find_best_trials_for_backbones",
    "find_study_folder_in_backbone_dir",
    "format_trial_identifier",
    "select_champion_per_backbone",
    "select_champions_for_backbones",
]
