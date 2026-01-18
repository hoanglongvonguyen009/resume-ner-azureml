"""Checkpoint resolution utilities for benchmarking."""

from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def extract_trial_id(trial_info: Dict[str, Any]) -> str:
    """
    Extract and normalize trial_id from trial_info.
    
    Handles both old format (trial_1_20251231_161745) and new format (trial-25d03eeb).
    
    Args:
        trial_info: Trial info dictionary
        
    Returns:
        Normalized trial_id string
    """
    trial_id_raw = trial_info.get("trial_id") or trial_info.get("trial_name", "unknown")
    
    if trial_id_raw.startswith("trial_"):
        return trial_id_raw[6:]  # Remove "trial_" prefix
    elif trial_id_raw.startswith("trial-"):
        return trial_id_raw  # Keep full "trial-25d03eeb" format
    else:
        return trial_id_raw


def validate_trial_info(trial_info: Dict[str, Any], backbone: str) -> Optional[Path]:
    """
    Validate trial_info and extract checkpoint_dir.
    
    Args:
        trial_info: Trial info dictionary
        backbone: Backbone name for logging
        
    Returns:
        Checkpoint directory Path if valid, None otherwise
    """
    checkpoint_dir: Optional[Path] = None
    if "checkpoint_dir" in trial_info and trial_info["checkpoint_dir"]:
        checkpoint_dir = Path(trial_info["checkpoint_dir"])
    else:
        logger.warning(
            f"Skipping {backbone}: missing 'checkpoint_dir' in trial_info. "
            f"Legacy format (trial_dir) is no longer supported. "
            f"Please use champion format from Phase 2."
        )
        return None
    
    study_key_hash = trial_info.get("study_key_hash")
    trial_key_hash = trial_info.get("trial_key_hash")
    
    if not study_key_hash or not trial_key_hash:
        logger.warning(
            f"Skipping {backbone}: missing 'study_key_hash' or 'trial_key_hash' in trial_info. "
            f"Legacy format is no longer supported. "
            f"Please use champion format from Phase 2."
        )
        return None
    
    return checkpoint_dir

