"""Directory operations for trial finding."""

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)

# UUID pattern for validating run IDs
_UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


def find_metrics_file(trial_dir: Path) -> Optional[Path]:
    """Find metrics.json file in trial directory.
    
    Checks multiple locations:
    1. Trial root: trial_dir/metrics.json
    2. CV folds: trial_dir/cv/fold0/metrics.json (for CV trials)
    
    Args:
        trial_dir: Path to trial directory
        
    Returns:
        Path to metrics.json if found, else None
    """
    # Try trial root first
    root_metrics = trial_dir / "metrics.json"
    if root_metrics.exists():
        return root_metrics
    
    # Try CV folds
    cv_dir = trial_dir / "cv"
    if cv_dir.exists():
        for fold_dir in cv_dir.iterdir():
            if fold_dir.is_dir() and fold_dir.name.startswith("fold"):
                fold_metrics = fold_dir / "metrics.json"
                if fold_metrics.exists():
                    return fold_metrics
    
    return None


def read_trial_meta(trial_dir: Path) -> Optional[Dict[str, Any]]:
    """Read trial_meta.json from trial directory.
    
    Args:
        trial_dir: Path to trial directory
        
    Returns:
        Dictionary with trial metadata, or None if file doesn't exist or can't be read
    """
    trial_meta_path = trial_dir / "trial_meta.json"
    if not trial_meta_path.exists():
        return None
    
    try:
        with open(trial_meta_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.debug(f"Could not read {trial_meta_path}: {e}")
        return None


def extract_hashes_from_trial_dir(trial_dir: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract hashes and run_id from trial directory.
    
    Uses centralized hash utilities (SSOT) when run_id is available, falls back to file metadata.
    
    Args:
        trial_dir: Path to trial directory
        
    Returns:
        Tuple of (study_key_hash, trial_key_hash, trial_run_id)
    """
    meta = read_trial_meta(trial_dir)
    if not meta:
        return None, None, None
    
    trial_run_id = None
    run_id_from_meta = meta.get("run_id")
    if run_id_from_meta and _UUID_PATTERN.match(run_id_from_meta):
        trial_run_id = run_id_from_meta
    
    # Priority 1: Use centralized utilities to get hashes from MLflow tags (SSOT)
    if trial_run_id:
        try:
            from infrastructure.tracking.mlflow.hash_utils import (
                get_study_key_hash_from_run,
                get_trial_key_hash_from_run,
            )
            from mlflow.tracking import MlflowClient
            
            client = MlflowClient()
            # Try to get config_dir from trial_dir for tag registry
            config_dir = None
            try:
                from infrastructure.paths.utils import resolve_project_paths_with_fallback
                _, config_dir = resolve_project_paths_with_fallback(output_dir=trial_dir, config_dir=None)
            except Exception:
                pass
            
            study_key_hash = get_study_key_hash_from_run(trial_run_id, client, config_dir)
            trial_key_hash = get_trial_key_hash_from_run(trial_run_id, client, config_dir)
            
            # If we got hashes from MLflow tags, use them (SSOT)
            if study_key_hash or trial_key_hash:
                return study_key_hash, trial_key_hash, trial_run_id
        except Exception as e:
            logger.debug(f"Could not retrieve hashes from MLflow tags for run {trial_run_id[:12] if trial_run_id else 'unknown'}...: {e}")
    
    # Priority 2: Fall back to file metadata
    study_key_hash = meta.get("study_key_hash")
    trial_key_hash = meta.get("trial_key_hash")
    
    return study_key_hash, trial_key_hash, trial_run_id


def find_trial_dir_by_hash(
    study_folder: Path,
    trial_key_hash: str,
    study_key_hash: Optional[str],
    backbone_name: str,
    hpo_backbone_dir: Path,
) -> Optional[Path]:
    """Find trial directory by trial_key_hash.
    
    Args:
        study_folder: Path to study folder
        trial_key_hash: Trial key hash to match
        study_key_hash: Study key hash (for v2 path lookup)
        backbone_name: Model backbone name
        hpo_backbone_dir: HPO backbone output directory
        
    Returns:
        Path to trial directory if found, else None
    """
    # Try v2 path lookup first if we have study_key_hash
    if study_key_hash:
        try:
            from infrastructure.paths.parse import find_trial_by_hash
            from infrastructure.paths.utils import resolve_project_paths_with_fallback
            
            project_root, resolved_config_dir = resolve_project_paths_with_fallback(
                output_dir=hpo_backbone_dir,
                config_dir=None,
            )
            if project_root and resolved_config_dir:
                v2_trial_dir = find_trial_by_hash(
                    root_dir=project_root,
                    config_dir=resolved_config_dir,
                    model=backbone_name,
                    study_key_hash=study_key_hash,
                    trial_key_hash=trial_key_hash,
                )
                if v2_trial_dir and v2_trial_dir.exists():
                    return v2_trial_dir
        except Exception:
            pass
    
    # Fallback: iterate through study_folder looking for v2 trials
    for trial_dir in study_folder.iterdir():
        if not trial_dir.is_dir():
            continue
        if not (trial_dir.name.startswith("trial-") and len(trial_dir.name) > 7):
            continue
        
        meta = read_trial_meta(trial_dir)
        if meta and meta.get("trial_key_hash") == trial_key_hash:
            return trial_dir
    
    return None


def find_trial_dir_by_number(
    study_folder: Path,
    trial_number: int,
) -> Optional[Path]:
    """Find trial directory by trial number.
    
    Args:
        study_folder: Path to study folder
        trial_number: Trial number to match
        
    Returns:
        Path to trial directory if found, else None
    """
    for trial_dir in study_folder.iterdir():
        if not trial_dir.is_dir():
            continue
        if not (trial_dir.name.startswith("trial-") and len(trial_dir.name) > 7):
            continue
        
        meta = read_trial_meta(trial_dir)
        if meta and meta.get("trial_number") == trial_number:
            return trial_dir
    
    return None


def build_trial_result_dict(
    trial_dir: Path,
    best_trial_config: Dict[str, Any],
    study_key_hash: Optional[str] = None,
    trial_key_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Build trial result dictionary from trial directory and config.
    
    Args:
        trial_dir: Path to trial directory
        best_trial_config: Best trial configuration from study
        study_key_hash: Optional study key hash
        trial_key_hash: Optional trial key hash
        
    Returns:
        Dictionary with trial information
    """
    # Extract hashes from trial_meta.json if not provided
    if not study_key_hash or not trial_key_hash:
        meta_study_hash, meta_trial_hash, _ = extract_hashes_from_trial_dir(trial_dir)
        study_key_hash = study_key_hash or meta_study_hash
        trial_key_hash = trial_key_hash or meta_trial_hash
    
    return {
        "trial_name": trial_dir.name,
        "trial_dir": str(trial_dir),
        "checkpoint_dir": None,  # Will be determined later
        "checkpoint_type": "unknown",
        "accuracy": best_trial_config.get("selection_criteria", {}).get("best_value"),
        "metrics": best_trial_config.get("metrics", {}),
        "hyperparameters": best_trial_config.get("hyperparameters", {}),
        "study_key_hash": study_key_hash,
        "trial_key_hash": trial_key_hash,
    }

