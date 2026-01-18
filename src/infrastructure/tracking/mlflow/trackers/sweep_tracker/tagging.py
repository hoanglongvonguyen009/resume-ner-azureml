"""Tagging utilities for sweep tracker."""

from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.logging_utils import get_logger
from infrastructure.naming.mlflow.run_keys import build_mlflow_run_key, build_mlflow_run_key_hash
from infrastructure.naming.mlflow.tags import build_mlflow_tags
from infrastructure.paths.utils import infer_config_dir

logger = get_logger(__name__)


def compute_grouping_hashes(
    hpo_config: Dict[str, Any],
    data_config: Optional[Dict[str, Any]],
    train_config: Optional[Dict[str, Any]],
    context: Optional[Any],  # NamingContext
    config_dir: Path,
) -> tuple[Optional[str], Optional[str]]:
    """
    Compute study_key_hash and study_family_hash for grouping.
    
    Returns:
        Tuple of (study_key_hash, study_family_hash)
    """
    study_key_hash = None
    study_family_hash = None
    
    # Compute v2 hash using fingerprints (requires data_config, hpo_config, train_config)
    if hpo_config and data_config and train_config and context and context.model:
        from infrastructure.tracking.mlflow.hash_utils import (
            compute_study_key_hash_v2,
        )
        study_key_hash = compute_study_key_hash_v2(
            data_config, hpo_config, train_config, context.model, config_dir
        )
        if study_key_hash:
            logger.info(
                f"[START_SWEEP_RUN] Computed v2 grouping hashes: "
                f"study_key_hash={study_key_hash[:16]}..."
            )
    
    # Always compute family hash (v1, doesn't depend on train_config)
    if not study_family_hash and hpo_config and data_config:
        try:
            from infrastructure.naming.mlflow.hpo_keys import (
                build_hpo_study_family_key,
                build_hpo_study_family_hash,
            )
            benchmark_config = None  # Could be passed as parameter if needed
            study_family_key = build_hpo_study_family_key(
                data_config, hpo_config, benchmark_config
            )
            study_family_hash = build_hpo_study_family_hash(
                study_family_key)
            if study_key_hash:
                logger.info(
                    f"[START_SWEEP_RUN] Computed grouping hashes: "
                    f"study_key_hash={study_key_hash[:16]}..., "
                    f"study_family_hash={study_family_hash[:16]}..."
                )
        except Exception as e:
            logger.warning(
                f"[START_SWEEP_RUN] Could not compute study_family_hash: {e}",
                exc_info=True
            )
    
    return study_key_hash, study_family_hash


def build_sweep_tags(
    context: Optional[Any],  # NamingContext
    output_dir: Optional[Path],
    group_id: Optional[str],
    config_dir: Path,
    study_key_hash: Optional[str],
    study_family_hash: Optional[str],
) -> Dict[str, str]:
    """
    Build MLflow tags for sweep run.
    
    Returns:
        Dictionary of tags to set
    """
    # Build RunHandle (compute run_key_hash before building tags)
    run_key = build_mlflow_run_key(context) if context else None
    run_key_hash = build_mlflow_run_key_hash(
        run_key) if run_key else None

    # Build and set tags atomically
    tags = build_mlflow_tags(
        context=context,
        output_dir=output_dir,
        group_id=group_id,
        config_dir=config_dir,
        study_key_hash=study_key_hash,
        study_family_hash=study_family_hash,
        trial_key_hash=None,  # Trial key hash is computed in trial runs
        run_key_hash=run_key_hash,  # Pass run_key_hash for cleanup matching
    )
    
    return tags

