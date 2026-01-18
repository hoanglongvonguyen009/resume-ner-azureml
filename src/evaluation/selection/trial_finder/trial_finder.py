"""Main trial finder module - refactored to use extracted modules."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from common.shared.logging_utils import get_logger

from evaluation.selection.trial_finder.champion_selection import (
    select_champion_per_backbone,
    select_champions_for_backbones,
)
from evaluation.selection.trial_finder.directory_ops import (
    build_trial_result_dict,
    extract_hashes_from_trial_dir,
    find_metrics_file,
    find_trial_dir_by_hash,
    find_trial_dir_by_number,
    read_trial_meta,
)
from evaluation.selection.trial_finder.discovery import (
    find_best_trial_from_study,
    find_best_trial_in_study_folder,
    find_best_trials_for_backbones,
    find_study_folder_in_backbone_dir,
)

logger = get_logger(__name__)

# Re-export constants for backward compatibility
from evaluation.selection.trial_finder.mlflow_queries import (
    DEFAULT_MLFLOW_MAX_RESULTS,
    LARGE_MLFLOW_MAX_RESULTS,
    SAMPLE_MLFLOW_MAX_RESULTS,
    SMALL_MLFLOW_MAX_RESULTS,
)


def format_trial_identifier(trial_dir: Path, trial_number: Optional[int] = None) -> str:
    """Format trial identifier using hash-based naming if available, else fallback to directory name.

    Args:
        trial_dir: Path to trial directory
        trial_number: Optional trial number to include in identifier

    Returns:
        Formatted identifier string (e.g., "study-350a79aa, trial-9d4153fb, t1" or "trial_1_20260106_173735")
    """
    meta = read_trial_meta(trial_dir)
    if meta:
        study_key_hash = meta.get("study_key_hash")
        trial_key_hash = meta.get("trial_key_hash")
        meta_trial_number = meta.get("trial_number")

        # Use trial_number from meta if available, else use provided trial_number
        display_trial_number = meta_trial_number if meta_trial_number is not None else trial_number

        if study_key_hash and trial_key_hash:
            if display_trial_number is not None:
                return f"study-{study_key_hash[:8]}, trial-{trial_key_hash[:8]}, t{display_trial_number}"
            else:
                return f"study-{study_key_hash[:8]}, trial-{trial_key_hash[:8]}"
        elif display_trial_number is not None:
            return f"t{display_trial_number}"

    # Fallback to directory name or trial number
    if trial_number is not None:
        return f"t{trial_number}"
    return trial_dir.name

