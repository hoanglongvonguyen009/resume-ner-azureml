"""Helper functions for HPO sweep orchestration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from shared.logging_utils import get_logger

from .checkpoint_manager import get_storage_uri, resolve_storage_path

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
) -> Tuple[Optional[Path], Optional[str], bool]:
    """
    Set up checkpoint storage and determine if resuming.

    Args:
        output_dir: Base output directory.
        checkpoint_config: Checkpoint configuration dictionary.
        backbone: Model backbone name.

    Returns:
        Tuple of (storage_path, storage_uri, should_resume).
    """
    checkpoint_config = checkpoint_config or {}
    storage_path = resolve_storage_path(
        output_dir=output_dir,
        checkpoint_config=checkpoint_config,
        backbone=backbone,
    )
    storage_uri = get_storage_uri(storage_path)

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


def create_study_name(backbone: str, run_id: str, should_resume: bool) -> str:
    """
    Create Optuna study name.

    Args:
        backbone: Model backbone name.
        run_id: Unique run ID.
        should_resume: Whether resuming from checkpoint.

    Returns:
        Study name string.
    """
    if should_resume:
        # Use base name to resume existing study
        return f"hpo_{backbone}"
    else:
        # Use unique name for fresh start
        return f"hpo_{backbone}_{run_id}"


def create_mlflow_run_name(backbone: str, run_id: str) -> str:
    """
    Create MLflow run name for HPO sweep.

    Args:
        backbone: Model backbone name.
        run_id: Unique run ID.

    Returns:
        MLflow run name string.
    """
    return f"hpo_{backbone}_{run_id}"

