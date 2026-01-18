"""Hash computation utilities for trial finding."""

from typing import Any, Dict, Optional, Tuple

logger = None  # Will be initialized lazily


def compute_trial_key_hash_from_study(
    study: Any,
    backbone_name: str,
    hpo_config: Optional[Dict[str, Any]],
    data_config: Optional[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[str]]:
    """Compute trial_key_hash and study_key_hash from Optuna study.
    
    Args:
        study: Optuna study object
        backbone_name: Model backbone name
        hpo_config: HPO configuration
        data_config: Data configuration
        
    Returns:
        Tuple of (trial_key_hash, study_key_hash) or (None, None) if computation fails
    """
    if not hpo_config or not data_config or not study.best_trial:
        return None, None
    
    try:
        from infrastructure.tracking.mlflow.hash_utils import (
            compute_trial_key_hash_from_configs,
        )
        from infrastructure.naming.mlflow.hpo_keys import (
            build_hpo_study_key,  # v1 - used here because train_config not available
            build_hpo_study_key_hash,
        )
        
        # Build study key hash using v1 (train_config not available in this context)
        # TODO: Migrate to v2 when train_config becomes available
        study_key = build_hpo_study_key(
            data_config=data_config,
            hpo_config=hpo_config,
            model=backbone_name,
        )
        study_key_hash = build_hpo_study_key_hash(study_key)
        
        if not study_key_hash:
            return None, None
        
        # Extract hyperparameters (excluding metadata fields)
        hyperparameters = {
            k: v
            for k, v in study.best_trial.params.items()
            if k not in ("backbone", "trial_number")
        }
        
        # Compute trial_key_hash
        trial_key_hash = compute_trial_key_hash_from_configs(
            study_key_hash, hyperparameters, None
        )
        
        return trial_key_hash, study_key_hash
    except Exception:
        return None, None

