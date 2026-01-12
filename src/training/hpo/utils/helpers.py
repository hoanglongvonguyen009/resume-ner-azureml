"""Helper functions for HPO sweep orchestration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def generate_run_id() -> str:
    """
    Generate unique run ID (timestamp-based) to prevent overwriting on reruns.

    Returns:
        Timestamp string in format YYYYMMDD_HHMMSS.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def setup_checkpoint_storage(
    output_dir: Path,
    checkpoint_config: Optional[Dict[str, Any]],
    backbone: str,
    study_name: Optional[str] = None,
    restore_from_drive: Optional[Callable[[Path], bool]] = None,
) -> Tuple[Optional[Path], Optional[str], bool]:
    """
    Set up checkpoint storage and determine if resuming.

    Args:
        output_dir: Base output directory.
        checkpoint_config: Checkpoint configuration dictionary.
        backbone: Model backbone name.
        study_name: Optional resolved study name (for {study_name} placeholder).
        restore_from_drive: Optional function to restore checkpoint from Drive if missing.
                          Function should take a Path and return bool (True if restored).

    Returns:
        Tuple of (storage_path, storage_uri, should_resume).
    """
    # Lazy import to avoid circular dependency
    from training.hpo.checkpoint.storage import get_storage_uri, resolve_storage_path

    checkpoint_config = checkpoint_config or {}
    storage_path = resolve_storage_path(
        output_dir=output_dir,
        checkpoint_config=checkpoint_config,
        backbone=backbone,
        study_name=study_name,
    )
    storage_uri = get_storage_uri(storage_path)

    # If local checkpoint missing and restore_from_drive provided, attempt restore
    if storage_path is not None and not storage_path.exists() and restore_from_drive is not None:
        try:
            restored = restore_from_drive(storage_path)
            if restored:
                logger.info(
                    f"Restored HPO checkpoint from Drive: {storage_path}")
            else:
                logger.debug(
                    f"Drive backup not found for checkpoint: {storage_path}")
        except Exception as e:
            logger.warning(f"Failed to restore checkpoint from Drive: {e}")

    # Determine if we should resume
    auto_resume = (
        checkpoint_config.get("auto_resume", True)
        if checkpoint_config.get("enabled", False)
        else False
    )
    should_resume = (
        auto_resume
        and storage_path is not None
        and storage_path.exists()
    )

    return storage_path, storage_uri, should_resume


def create_study_name(
    backbone: str,
    run_id: str,
    should_resume: bool,
    checkpoint_config: Optional[Dict[str, Any]] = None,
    hpo_config: Optional[Dict[str, Any]] = None,
    run_mode: Optional[str] = None,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> str:
    """
    Create Optuna study name with variant support (like final training).
    
    When run_mode == "force_new", computes next variant number (v1, v2, v3...).
    When run_mode == "reuse_if_exists", uses base name for resumability.
    
    Uses shared variants.py module (DRY).

    Args:
        backbone: Model backbone name.
        run_id: Unique run ID.
        should_resume: Whether resuming from checkpoint.
        checkpoint_config: Optional checkpoint configuration dictionary.
        hpo_config: Optional HPO configuration dictionary.
        run_mode: Optional run mode (if None, extracted from configs).
        root_dir: Optional project root directory (required for variant computation).
        config_dir: Optional config directory (required for variant computation).

    Returns:
        Study name string (with variant suffix if force_new and variant > 1).
    """
    checkpoint_config = checkpoint_config or {}
    hpo_config = hpo_config or {}
    checkpoint_enabled = checkpoint_config.get("enabled", False)
    
    # Get run_mode from config if not provided
    if run_mode is None:
        from infrastructure.config.run_mode import get_run_mode
        combined_config = {**hpo_config, **checkpoint_config}
        run_mode = get_run_mode(combined_config)
    
    # Check for custom study_name in checkpoint config first, then HPO config
    study_name_template = checkpoint_config.get("study_name") or hpo_config.get("study_name")
    
    if study_name_template:
        study_name = study_name_template.replace("{backbone}", backbone)
        # If force_new and we have root_dir/config_dir, compute variant
        if run_mode == "force_new" and root_dir and config_dir:
            from infrastructure.config.variants import compute_next_variant
            variant = compute_next_variant(
                root_dir=root_dir,
                config_dir=config_dir,
                process_type="hpo",
                model=backbone,
                base_name=study_name,
            )
            return f"{study_name}_v{variant}" if variant > 1 else study_name
        # If reuse_if_exists, use base name
        return study_name
    
    # Default behavior when no custom study_name is provided
    base_name = f"hpo_{backbone}"
    
    if run_mode == "force_new":
        # Compute next variant when force_new
        if root_dir and config_dir:
            from infrastructure.config.variants import compute_next_variant
            variant = compute_next_variant(
                root_dir=root_dir,
                config_dir=config_dir,
                process_type="hpo",
                model=backbone,
                base_name=base_name,
            )
            return f"{base_name}_v{variant}" if variant > 1 else base_name
        else:
            # Fallback: use run_id if root_dir/config_dir not available
            return f"{base_name}_{run_id}"
    elif checkpoint_enabled or should_resume:
        # Use consistent name for resumability (no variant suffix)
        return base_name
    else:
        # Use unique name for fresh start (only when checkpointing is disabled)
        return f"{base_name}_{run_id}"


def find_study_variants(
    output_dir: Path,
    backbone: str,
) -> list[str]:
    """
    Find all study variants for a given backbone.
    
    Uses shared variants.py module (DRY).
    
    Scans output directory for study folders matching pattern:
    - hpo_{backbone} (variant 1, implicit)
    - hpo_{backbone}_v1, hpo_{backbone}_v2, etc.
    
    Args:
        output_dir: HPO output directory (backbone-level directory).
        backbone: Model backbone name.
    
    Returns:
        List of variant names (study folder names).
    """
    base_name = f"hpo_{backbone}"
    variants = []
    
    if not output_dir.exists():
        return variants
    
    for item in output_dir.iterdir():
        if not item.is_dir():
            continue
        
        folder_name = item.name
        if folder_name == base_name:
            variants.append(base_name)
        elif folder_name.startswith(f"{base_name}_v"):
            variants.append(folder_name)
    
    return sorted(variants)


def create_mlflow_run_name(
    backbone: str,
    run_id: str,
    study_name: Optional[str] = None,
    should_resume: bool = False,
    checkpoint_enabled: bool = False,
) -> str:
    """
    Create MLflow run name for HPO sweep.

    Args:
        backbone: Model backbone name.
        run_id: Unique run ID.
        study_name: Optional study name (used when checkpointing is enabled).
        should_resume: Whether resuming from checkpoint.
        checkpoint_enabled: Whether checkpointing is enabled.

    Returns:
        MLflow run name string.
    """
    # When checkpointing is enabled, always use study_name (for both new and resumed runs)
    if checkpoint_enabled and study_name:
        return study_name
    elif should_resume and study_name:
        # When resuming without checkpointing, use study_name
        return study_name
    else:
        # For new runs without checkpointing, use unique name with run_id
        return f"hpo_{backbone}_{run_id}"
