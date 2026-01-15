from __future__ import annotations

"""
@meta
name: run_names
type: utility
domain: training
responsibility:
  - Build MLflow run names with fallback logic
  - Handle systematic naming and policy-like fallback formats
inputs:
  - Training configuration
  - Naming contexts
  - Process types (final_training, hpo_trial, hpo_trial_fold)
outputs:
  - MLflow run names
tags:
  - utility
  - training
  - mlflow
  - naming
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Run name building utilities for training execution.

This module provides consolidated run name building logic with fallback support.
It handles both systematic naming (via infrastructure.naming) and policy-like
fallback formats for final training and HPO trials.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def build_training_run_name_with_fallback(
    process_type: str,
    config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
    backbone: Optional[str] = None,
    model: Optional[str] = None,
    trial_number: Optional[int] = None,
    fold_idx: Optional[int] = None,
    study_key_hash: Optional[str] = None,
    run_id: Optional[str] = None,
    parent_run_id: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> str:
    """
    Build MLflow run name with fallback logic.

    This function tries systematic naming first (via infrastructure.naming),
    then falls back to policy-like formats if systematic naming fails.

    Args:
        process_type: Process type ("final_training", "hpo_trial", or "hpo_trial_fold").
        config: Optional training configuration dictionary (for extracting fingerprints).
        output_dir: Optional output directory (for inferring config_dir).
        backbone: Optional model backbone name (for final training).
        model: Optional model name (for HPO trials).
        trial_number: Optional trial number (for HPO trials).
        fold_idx: Optional fold index (for k-fold CV).
        study_key_hash: Optional study key hash (for HPO trials).
        run_id: Optional run ID (for final training fallback).
        parent_run_id: Optional parent run ID (for extracting metadata in HPO trials).
        config_dir: Optional config directory (for systematic naming).

    Returns:
        MLflow run name string.

    Examples:
        # Final training:
        run_name = build_training_run_name_with_fallback(
            process_type="final_training",
            config=config,
            output_dir=output_dir,
            backbone="distilbert"
        )

        # HPO trial:
        run_name = build_training_run_name_with_fallback(
            process_type="hpo_trial",
            model="distilbert",
            trial_number=0,
            study_key_hash="abc123",
            parent_run_id="parent_123"
        )
    """
    # First, check if MLFLOW_RUN_NAME is set (from notebook/environment)
    env_run_name = os.environ.get("MLFLOW_RUN_NAME")
    if env_run_name:
        return env_run_name

    # Try systematic naming first
    run_name = _try_systematic_naming(
        process_type=process_type,
        config=config,
        output_dir=output_dir,
        backbone=backbone,
        model=model,
        trial_number=trial_number,
        fold_idx=fold_idx,
        study_key_hash=study_key_hash,
        parent_run_id=parent_run_id,
        config_dir=config_dir,
    )

    # Fallback to policy-like format if systematic naming didn't work
    if not run_name:
        if process_type == "final_training":
            run_name = _build_final_training_fallback_name(
                backbone=backbone or "unknown",
                run_id=run_id,
            )
        elif process_type in ("hpo_trial", "hpo_trial_fold"):
            run_name = _build_hpo_trial_fallback_name(
                model=model or "unknown",
                trial_number=trial_number or 0,
                fold_idx=fold_idx,
                study_key_hash=study_key_hash,
            )
        else:
            # Unknown process type - use generic fallback
            logger.warning(f"Unknown process_type: {process_type}, using generic fallback")
            run_name = f"training_run_{process_type}"

    return run_name


def _try_systematic_naming(
    process_type: str,
    config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
    backbone: Optional[str] = None,
    model: Optional[str] = None,
    trial_number: Optional[int] = None,
    fold_idx: Optional[int] = None,
    study_key_hash: Optional[str] = None,
    parent_run_id: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Try to build systematic run name using infrastructure.naming.

    Returns None if systematic naming fails (allows fallback).
    """
    try:
        from infrastructure.naming import create_naming_context
        from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
        from common.shared.platform_detection import detect_platform

        # Infer config_dir if not provided
        if config_dir is None and output_dir:
            config_dir = _infer_config_dir_from_output(output_dir)
        elif config_dir is None:
            config_dir = Path(os.environ.get("CONFIG_DIR", Path.cwd() / "config"))

        # Build naming context based on process type
        if process_type == "final_training":
            return _try_final_training_systematic_naming(
                config=config,
                backbone=backbone,
                config_dir=config_dir,
            )
        elif process_type in ("hpo_trial", "hpo_trial_fold"):
            return _try_hpo_trial_systematic_naming(
                model=model,
                trial_number=trial_number,
                fold_idx=fold_idx,
                study_key_hash=study_key_hash,
                parent_run_id=parent_run_id,
                config_dir=config_dir,
            )
    except Exception as e:
        logger.debug(f"Could not build systematic run name: {e}, using fallback")

    return None


def _try_final_training_systematic_naming(
    config: Optional[Dict[str, Any]],
    backbone: Optional[str],
    config_dir: Path,
) -> Optional[str]:
    """Try systematic naming for final training."""
    if not config or not backbone:
        return None

    from infrastructure.naming import create_naming_context
    from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
    from common.shared.platform_detection import detect_platform

    # Extract fingerprints from config
    spec_fp = config.get("fingerprints", {}).get("spec_fp")
    exec_fp = config.get("fingerprints", {}).get("exec_fp")
    variant = config.get("fingerprints", {}).get("variant", 1)

    # Build NamingContext if we have required fields
    if spec_fp and exec_fp:
        training_context = create_naming_context(
            process_type="final_training",
            model=backbone,
            spec_fp=spec_fp,
            exec_fp=exec_fp,
            environment=detect_platform(),
            variant=variant,
        )
        return build_mlflow_run_name(training_context, config_dir)

    return None


def _try_hpo_trial_systematic_naming(
    model: Optional[str],
    trial_number: Optional[int],
    fold_idx: Optional[int],
    study_key_hash: Optional[str],
    parent_run_id: Optional[str],
    config_dir: Path,
) -> Optional[str]:
    """Try systematic naming for HPO trial."""
    from infrastructure.naming import create_naming_context
    from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
    from common.shared.platform_detection import detect_platform

    # Try to get study_key_hash and model from parent run if not provided
    if parent_run_id and (not study_key_hash or not model):
        try:
            from mlflow.tracking import MlflowClient

            client = MlflowClient()
            parent_run = client.get_run(parent_run_id)
            if not study_key_hash:
                study_key_hash = parent_run.data.tags.get("code.study_key_hash")
            if not model:
                model = parent_run.data.tags.get("code.model")
        except Exception:
            pass

    # Create context if we have minimum required info
    if model or study_key_hash:
        fold_context = create_naming_context(
            process_type="hpo",
            model=model or "unknown",
            environment=detect_platform(),
            trial_id=f"trial_{trial_number}" if trial_number is not None else "trial_0",
            trial_number=trial_number,
            fold_idx=fold_idx,
            study_key_hash=study_key_hash,
        )
        return build_mlflow_run_name(fold_context, config_dir=config_dir)

    return None


def _build_final_training_fallback_name(
    backbone: str,
    run_id: Optional[str] = None,
) -> str:
    """
    Build fallback run name for final training.

    Format: {env}_{backbone}_training_{run_id}

    Args:
        backbone: Model backbone name.
        run_id: Optional run ID (from config if available).

    Returns:
        Policy-like run name string.
    """
    from common.shared.platform_detection import detect_platform

    environment = detect_platform()
    run_id_value = run_id or "unknown"

    # Shorten run_id if it's long (take first 8 chars)
    run_id_short = run_id_value[:8] if len(run_id_value) > 8 else run_id_value

    # Sanitize: replace problematic characters
    backbone_safe = backbone.replace("/", "_").replace("\\", "_").replace(":", "_")
    run_id_safe = run_id_short.replace("/", "_").replace("\\", "_").replace(":", "_")

    # Use policy-like format: {env}_{backbone}_training_{run_id}
    return f"{environment}_{backbone_safe}_training_{run_id_safe}"


def _build_hpo_trial_fallback_name(
    model: str,
    trial_number: int,
    fold_idx: Optional[int] = None,
    study_key_hash: Optional[str] = None,
) -> str:
    """
    Build fallback run name for HPO trial.

    Format: {env}_{model}_hpo_trial_study-{hash}_{trial}[_fold{idx}]

    Args:
        model: Model name.
        trial_number: Trial number.
        fold_idx: Optional fold index (for k-fold CV).
        study_key_hash: Optional study key hash.

    Returns:
        Policy-like run name string.
    """
    from common.shared.platform_detection import detect_platform

    env = detect_platform()
    model_name = model or "unknown"

    # Try to get study_hash short version
    study_hash_short = "unknown"
    if study_key_hash:
        study_hash_short = study_key_hash[:8]

    # Build policy-like name
    trial_num_str = f"t{str(trial_number).zfill(2)}"

    if fold_idx is not None:
        # Use hpo_trial_fold pattern
        return f"{env}_{model_name}_hpo_trial_study-{study_hash_short}_{trial_num_str}_fold{fold_idx}"
    else:
        # Use hpo_trial pattern
        return f"{env}_{model_name}_hpo_trial_study-{study_hash_short}_{trial_num_str}"


def _infer_config_dir_from_output(output_dir: Path) -> Optional[Path]:
    """
    Infer config directory from output directory.

    Looks for config/ directory by going up from outputs/ to root.

    Args:
        output_dir: Output directory path.

    Returns:
        Config directory path if found, None otherwise.
    """
    current = output_dir
    for _ in range(5):  # Limit search depth
        if current.name == "outputs" and (current.parent / "config").exists():
            return current.parent / "config"
        current = current.parent
        if not current or current == current.parent:  # Reached root
            break
    return None

