"""
Artifact acquisition utilities for best model selection.

This module provides robust checkpoint acquisition with local-first priority,
checkpoint validation, and graceful handling of Azure ML compatibility issues.

NOTE: This module now uses the unified artifact acquisition system under the hood.
The API remains the same for backward compatibility.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import os
import tarfile
import mlflow
import json
import shutil

# Import unified acquisition system
from evaluation.selection.artifact_unified.compat import acquire_best_model_checkpoint as _acquire_best_model_checkpoint_unified


def _extract_tar_gz(tar_path: Path, extract_to: Optional[Path] = None) -> Path:
    """
    Extract a tar.gz file and return the path to the extracted directory.
    
    NOTE: This function is kept for backward compatibility.
    The unified artifact acquisition system has its own implementation.

    Args:
        tar_path: Path to the tar.gz file
        extract_to: Directory to extract to (defaults to same directory as tar file)

    Returns:
        Path to the extracted directory containing checkpoint files
    """
    if extract_to is None:
        extract_to = tar_path.parent

    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)

    with tarfile.open(tar_path, 'r:gz') as tar:
        members = tar.getmembers()
        if members:
            tar.extractall(path=extract_to)

            # If archive has a single root directory, return that
            root_names = {Path(m.name).parts[0] for m in members if m.name}
            if len(root_names) == 1:
                root_name = list(root_names)[0]
                extracted_path = extract_to / root_name
                if extracted_path.exists():
                    return extracted_path

            return extract_to

    return extract_to


def _validate_checkpoint(checkpoint_path: Path) -> bool:
    """
    Validate checkpoint integrity by checking for essential files.
    
    NOTE: This function is kept for backward compatibility.
    The unified artifact acquisition system uses artifact-kind-specific validation.

    Args:
        checkpoint_path: Path to checkpoint directory

    Returns:
        True if checkpoint appears valid, False otherwise
    """
    if not checkpoint_path.exists() or not checkpoint_path.is_dir():
        return False

    # Check for common checkpoint files (PyTorch/HuggingFace)
    essential_files = [
        "pytorch_model.bin",
        "model.safetensors",
        "model.bin",
        "pytorch_model.bin.index.json",
    ]

    has_model_file = any((checkpoint_path / fname).exists()
                         for fname in essential_files)
    has_config = (checkpoint_path / "config.json").exists()

    return has_model_file or has_config


def _find_checkpoint_in_directory(directory: Path) -> Optional[Path]:
    """
    Search for a valid checkpoint directory within the given directory.

    Args:
        directory: Directory to search in

    Returns:
        Path to valid checkpoint directory, or None if not found
    """
    if not directory.is_dir():
        return None

    # Check if directory itself contains checkpoint files
    if _validate_checkpoint(directory):
        return directory

    # Check for checkpoint subdirectory
    checkpoint_subdir = directory / "checkpoint"
    if checkpoint_subdir.exists() and checkpoint_subdir.is_dir() and _validate_checkpoint(checkpoint_subdir):
        return checkpoint_subdir

    # Search recursively for any directory with checkpoint files
    for item in directory.rglob("*"):
        if item.is_dir() and _validate_checkpoint(item):
            return item

    return None


def _build_checkpoint_dir(
    root_dir: Path,
    config_dir: Path,
    environment: str,
    backbone: str,
    artifact_run_id: str,
    study_key_hash: Optional[str] = None,
    trial_key_hash: Optional[str] = None,
) -> Path:
    """
    Build systematic checkpoint directory path using centralized paths config.

    Uses stable naming based on (study_key_hash, trial_key_hash) when available,
    falling back to run_id for backward compatibility.

    Path structure:
      - Preferred: outputs/best_model_selection/{environment}/{backbone}/sel_{study_hash[:8]}_{trial_hash[:8]}/
      - Fallback: outputs/best_model_selection/{environment}/{backbone}/run_{run_id[:8]}/

    Args:
        root_dir: Project root directory
        config_dir: Config directory
        environment: Execution environment (local, colab, kaggle)
        backbone: Model backbone name
        artifact_run_id: MLflow run ID (for fallback)
        study_key_hash: Study key hash (preferred for stable naming)
        trial_key_hash: Trial key hash (preferred for stable naming)

    Returns:
        Path to checkpoint directory
    """
    from infrastructure.paths import resolve_output_path

    base_dir = resolve_output_path(
        root_dir, config_dir, "best_model_selection") / environment / backbone

    if study_key_hash and trial_key_hash:
        # Extract 8-char hashes for path construction (consistent with token expansion)
        study8 = study_key_hash[:8] if len(study_key_hash) >= 8 else study_key_hash
        trial8 = trial_key_hash[:8] if len(trial_key_hash) >= 8 else trial_key_hash
        return base_dir / f"sel_{study8}_{trial8}"

    return base_dir / f"run_{artifact_run_id[:8]}"


def _find_checkpoint_in_drive_by_hash(
    drive_hpo_dir: Path,
    study_key_hash: str,
    trial_key_hash: str,
) -> Optional[Path]:
    """
    Find checkpoint in Drive by scanning Drive directory structure directly.
    This avoids restoring the entire HPO directory structure.

    Args:
        drive_hpo_dir: Drive path to HPO backbone directory
        study_key_hash: Target study key hash
        trial_key_hash: Target trial key hash

    Returns:
        Path to checkpoint directory in Drive, or None if not found
    """
    if not drive_hpo_dir.exists():
        return None

    # Scan study folders in Drive
    for study_folder in drive_hpo_dir.iterdir():
        if not study_folder.is_dir() or study_folder.name.startswith("trial_"):
            continue

        # Scan trial folders
        for trial_dir in study_folder.iterdir():
            if not trial_dir.is_dir() or not trial_dir.name.startswith("trial_"):
                continue

            # Read trial metadata from Drive
            trial_meta_path = trial_dir / "trial_meta.json"
            if not trial_meta_path.exists():
                continue

            try:
                with open(trial_meta_path, "r") as f:
                    meta = json.load(f)

                # Match by hashes
                if (meta.get("study_key_hash") == study_key_hash and
                        meta.get("trial_key_hash") == trial_key_hash):
                    # Found match! Get checkpoint path (prefer refit, else best CV fold)
                    refit_checkpoint = trial_dir / "refit" / "checkpoint"
                    if refit_checkpoint.exists():
                        return refit_checkpoint

                    # Check CV folds
                    cv_dir = trial_dir / "cv"
                    if cv_dir.exists():
                        fold_dirs = [d for d in cv_dir.iterdir()
                                     if d.is_dir() and d.name.startswith("fold")]
                        if fold_dirs:
                            # Return first fold checkpoint (or implement best fold selection)
                            for fold_dir in sorted(fold_dirs):
                                fold_checkpoint = fold_dir / "checkpoint"
                                if fold_checkpoint.exists():
                                    return fold_checkpoint

                    # Fallback
                    checkpoint = trial_dir / "checkpoint"
                    if checkpoint.exists():
                        return checkpoint
            except Exception:
                continue

    return None


def _get_azure_ml_info(config_dir: Path, root_dir: Path, tracking_uri: str) -> tuple[str, str]:
    """
    Extract Azure ML workspace name and resource group from config files.

    Returns:
        Tuple of (workspace_name, resource_group)
    """
    workspace_name = "<workspace-name>"
    resource_group = "<resource-group>"

    try:
        from common.shared.yaml_utils import load_yaml
        from common.shared.mlflow_setup import _load_env_file
        import re

        # config_dir is already typed as Path, so no conversion needed
        config_dir_path = config_dir

        # Get workspace name from config
        try:
            mlflow_config_path = config_dir_path / "mlflow.yaml"
            if mlflow_config_path.exists():
                mlflow_config = load_yaml(mlflow_config_path)
                workspace_name = mlflow_config.get("azure_ml", {}).get(
                    "workspace_name", "<workspace-name>")
        except Exception:
            pass

        # Get resource group - try multiple sources
        resource_group = os.getenv("AZURE_RESOURCE_GROUP") or ""
        if not resource_group:
            # Try loading from config.env file
            possible_paths = [
                root_dir / "config.env",
                config_dir_path / "config.env",
                config_dir_path.parent / "config.env",
                Path.cwd() / "config.env",
            ]
            for config_env_path in possible_paths:
                if config_env_path.exists():
                    env_vars = _load_env_file(config_env_path)
                    resource_group = env_vars.get("AZURE_RESOURCE_GROUP", "")
                    if resource_group:
                        resource_group = resource_group.strip('"\'')
                        break

        # Try extracting from tracking URI
        if not resource_group and tracking_uri and "azureml://" in tracking_uri:
            patterns = [
                r'/resourceGroups/([^/]+)/',
                r'resourceGroups/([^/]+)',
                r'resourceGroup=([^&]+)',
            ]
            for pattern in patterns:
                rg_match = re.search(pattern, tracking_uri)
                if rg_match:
                    resource_group = rg_match.group(1)
                    break

        # Try config files
        if not resource_group:
            try:
                infra_config_path = config_dir_path / "infrastructure.yaml"
                if infra_config_path.exists():
                    infra_config = load_yaml(infra_config_path)
                    rg_config = infra_config.get(
                        "azure", {}).get("resource_group", "")
                    if rg_config.startswith("${") and rg_config.endswith("}"):
                        env_var = rg_config[2:-1]
                        resource_group = os.getenv(env_var, "")
                    else:
                        resource_group = rg_config or ""
            except Exception:
                pass

        if not resource_group:
            resource_group = "<resource-group>"
        if not workspace_name or workspace_name == "":
            workspace_name = "<workspace-name>"

    except Exception:
        pass

    return workspace_name, resource_group


def acquire_best_model_checkpoint(
    best_run_info: Dict[str, Any],
    root_dir: Path,
    config_dir: Path,
    acquisition_config: Dict[str, Any],
    selection_config: Dict[str, Any],
    platform: str,
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    drive_store: Optional[Any] = None,
    in_colab: bool = False,
) -> Path:
    """
    Acquire checkpoint using unified acquisition system (backward compatibility wrapper).

    This function now uses the unified artifact acquisition system under the hood.
    The API remains the same for backward compatibility.

    Priority order (from config):
    1. Local disk (by config + backbone) - PREFERRED to avoid Azure ML issues
    2. Drive restore (Colab only) - scans Drive metadata, restores only checkpoint
    3. MLflow download

    Args:
        best_run_info: Dictionary with best run information (must include study_key_hash, trial_key_hash, run_id, backbone)
        root_dir: Project root directory
        config_dir: Config directory
        acquisition_config: Artifact acquisition configuration
        selection_config: Best model selection configuration
        platform: Platform name (local, colab, kaggle)
        restore_from_drive: Optional function to restore from Drive backup
        drive_store: Optional DriveBackupStore instance for direct Drive access
        in_colab: Whether running in Google Colab

    Returns:
        Path to validated checkpoint directory

    Raises:
        ValueError: If all fallback strategies fail
    """
    # Use unified acquisition system
    return _acquire_best_model_checkpoint_unified(
        best_run_info=best_run_info,
        root_dir=root_dir,
        config_dir=config_dir,
        acquisition_config=acquisition_config,
        selection_config=selection_config,
        platform=platform,
        restore_from_drive=restore_from_drive,
        drive_store=drive_store,
        in_colab=in_colab,
    )
