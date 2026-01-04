"""
Artifact acquisition utilities for best model selection.

This module provides robust checkpoint acquisition with local-first priority,
checkpoint validation, and graceful handling of Azure ML compatibility issues.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import os
import tarfile
import mlflow


def _extract_tar_gz(tar_path: Path, extract_to: Optional[Path] = None) -> Path:
    """
    Extract a tar.gz file and return the path to the extracted directory.

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
    from orchestration.paths import resolve_output_path
    
    base_dir = resolve_output_path(root_dir, config_dir, "best_model_selection") / environment / backbone
    
    if study_key_hash and trial_key_hash:
        return base_dir / f"sel_{study_key_hash[:8]}_{trial_key_hash[:8]}"
    
    return base_dir / f"run_{artifact_run_id[:8]}"


def _get_azure_ml_info(config_dir: Path, root_dir: Path, tracking_uri: str) -> tuple[str, str]:
    """
    Extract Azure ML workspace name and resource group from config files.

    Returns:
        Tuple of (workspace_name, resource_group)
    """
    workspace_name = "<workspace-name>"
    resource_group = "<resource-group>"

    try:
        from shared.yaml_utils import load_yaml
        from shared.mlflow_setup import _load_env_file
        import re

        config_dir_path = Path(config_dir) if isinstance(
            config_dir, str) else config_dir

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
    in_colab: bool = False,
) -> Path:
    """
    Acquire checkpoint using local-first fallback strategy.

    Priority order (from config):
    1. Local disk (by config + backbone) - PREFERRED to avoid Azure ML issues
    2. Drive restore (Colab only)
    3. MLflow download

    Args:
        best_run_info: Dictionary with best run information (must include study_key_hash, trial_key_hash, run_id, backbone)
        root_dir: Project root directory
        config_dir: Config directory
        acquisition_config: Artifact acquisition configuration
        selection_config: Best model selection configuration
        platform: Platform name (local, colab, kaggle)
        restore_from_drive: Optional function to restore from Drive backup
        in_colab: Whether running in Google Colab

    Returns:
        Path to validated checkpoint directory

    Raises:
        ValueError: If all fallback strategies fail
    """
    run_id = best_run_info["run_id"]
    study_key_hash = best_run_info.get("study_key_hash")
    trial_key_hash = best_run_info.get("trial_key_hash")
    backbone = best_run_info.get("backbone", "unknown")
    experiment_name = best_run_info.get("experiment_name", "unknown")

    print(f"[ACQUIRE] Acquiring checkpoint for run {run_id[:8]}...")
    priority = acquisition_config["priority"]

    # Strategy 1: Local disk selection (using hashes from best_model)
    if "local" in priority:
        try:
            from orchestration.jobs.local_selection_v2 import (
                find_trial_checkpoint_by_hash,
            )

            print(f"\n[Strategy 1] Local disk selection...")

            # Use study_key_hash and trial_key_hash to find exact trial
            if study_key_hash and trial_key_hash:
                hpo_output_dir = root_dir / "outputs" / "hpo" / platform / backbone
                checkpoint_path = find_trial_checkpoint_by_hash(
                    hpo_backbone_dir=hpo_output_dir,
                    study_key_hash=study_key_hash,
                    trial_key_hash=trial_key_hash,
                )

                if checkpoint_path:
                    checkpoint_path = Path(checkpoint_path)
                    if acquisition_config["local"].get("validate", True):
                        if _validate_checkpoint(checkpoint_path):
                            print(
                                f"   [OK] Checkpoint validated: \"{checkpoint_path}\"")
                            return checkpoint_path
                    else:
                        if checkpoint_path.exists():
                            print(
                                f"   [OK] Found checkpoint: \"{checkpoint_path}\"")
                            return checkpoint_path
                else:
                    print(f"   [INFO] Trial not found locally by hash (study_key_hash={study_key_hash[:8]}..., trial_key_hash={trial_key_hash[:8]}...)")
            else:
                print(f"   [INFO] Missing hashes (study_key_hash={study_key_hash is not None}, trial_key_hash={trial_key_hash is not None})")
        except Exception as e:
            import traceback
            print(f"   [WARN] Strategy 1 failed: {type(e).__name__}: {e}")
            # Don't print full traceback in normal flow, but keep for debugging
            # traceback.print_exc()

    # Strategy 2: Drive restore (Colab only)
    if "drive" in priority and restore_from_drive and in_colab and acquisition_config["drive"]["enabled"]:
        try:
            print(f"\n[Strategy 2] Drive restore...")
            checkpoint_name = f"checkpoint_{run_id[:8]}"
            drive_folder = acquisition_config["drive"]["folder_path"]
            drive_checkpoint_path = Path(
                "/content/drive/MyDrive") / drive_folder / "checkpoints" / checkpoint_name

            if restore_from_drive(drive_checkpoint_path, is_directory=True):
                if acquisition_config["drive"].get("validate", True):
                    if _validate_checkpoint(drive_checkpoint_path):
                        print(
                            f"   [OK] Restored and validated checkpoint from Drive: \"{drive_checkpoint_path}\"")
                        return drive_checkpoint_path
                else:
                    print(
                        f"   [OK] Restored checkpoint from Drive: \"{drive_checkpoint_path}\"")
                    return drive_checkpoint_path
        except Exception:
            pass

    # Strategy 3: MLflow download
    if "mlflow" in priority and acquisition_config["mlflow"]["enabled"]:
        try:
            print(f"\n[Strategy 3] MLflow download...")
            checkpoint_dir = _build_checkpoint_dir(
                root_dir, config_dir, platform, backbone, run_id,
                study_key_hash=study_key_hash, trial_key_hash=trial_key_hash
            )
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            import mlflow as mlflow_func
            from mlflow.tracking import MlflowClient

            tracking_uri = mlflow_func.get_tracking_uri()
            is_azure_ml = tracking_uri and "azureml://" in tracking_uri

            # List artifacts to find checkpoint
            client = MlflowClient()
            checkpoint_artifact_path = None

            try:
                artifacts = client.list_artifacts(run_id=run_id)
                artifact_paths = [artifact.path for artifact in artifacts]

                # Look for checkpoint in artifact paths
                for path in artifact_paths:
                    if "checkpoint" in path.lower():
                        if path == "checkpoint" or path == "checkpoint/":
                            checkpoint_artifact_path = path
                            break
                        elif checkpoint_artifact_path is None:
                            checkpoint_artifact_path = path

                if checkpoint_artifact_path is None:
                    checkpoint_artifact_path = "checkpoint"
            except Exception:
                checkpoint_artifact_path = "checkpoint"

            # Download artifacts
            local_path = client.download_artifacts(
                run_id=run_id,
                path=checkpoint_artifact_path,
                dst_path=str(checkpoint_dir)
            )

            checkpoint_path = Path(local_path)

            # Check for and extract tar.gz files
            if checkpoint_path.is_file() and checkpoint_path.suffixes == ['.tar', '.gz']:
                checkpoint_path = _extract_tar_gz(checkpoint_path)
            elif checkpoint_path.is_dir():
                tar_files = list(checkpoint_path.glob("*.tar.gz")) + \
                    list(checkpoint_path.glob("*.tgz"))
                if tar_files:
                    checkpoint_path = _extract_tar_gz(
                        tar_files[0], extract_to=checkpoint_path)

            # Find checkpoint in downloaded/extracted directory
            if checkpoint_path.is_dir():
                found_checkpoint = _find_checkpoint_in_directory(
                    checkpoint_path)
                if found_checkpoint:
                    checkpoint_path = found_checkpoint
                else:
                    # Validate the directory itself
                    if not _validate_checkpoint(checkpoint_path):
                        raise ValueError(
                            "Downloaded checkpoint failed validation - no valid checkpoint files found")

            # Final validation
            if acquisition_config["mlflow"].get("validate", True):
                if not _validate_checkpoint(checkpoint_path):
                    raise ValueError("Downloaded checkpoint failed validation")

            print(
                f"   [OK] Downloaded checkpoint from MLflow: \"{checkpoint_path}\"")
            return checkpoint_path

        except Exception as e:
            print(f"\n   [WARN] MLflow download failed: {type(e).__name__}")

    # All strategies failed - check for manually placed checkpoint
    checkpoint_dir = _build_checkpoint_dir(
        root_dir, config_dir, platform, backbone, run_id,
        study_key_hash=study_key_hash, trial_key_hash=trial_key_hash
    )
    manual_checkpoint_path = checkpoint_dir / "checkpoint"

    if manual_checkpoint_path.exists() and any(manual_checkpoint_path.iterdir()):
        if _validate_checkpoint(manual_checkpoint_path):
            print(
                f"[OK] Found manually placed checkpoint: \"{manual_checkpoint_path}\"")
            return manual_checkpoint_path

    # Generate error message
    tracking_uri = mlflow.get_tracking_uri() or ""
    is_azure_ml = "azureml://" in tracking_uri

    error_msg = (
        f"\n[ERROR] Could not acquire checkpoint for run {run_id[:8]}...\n"
        f"   Experiment: {experiment_name}\n"
        f"   Backbone: {backbone}\n"
        f"\n[TRIED] Strategies attempted:\n"
        f"   1. Local disk selection (by config + backbone)\n"
        f"   2. Drive restore (Colab only)\n"
        f"   3. MLflow download\n"
        f"\n[SOLUTIONS] In order of preference:\n"
        f"\n1. **Use Local Disk** (if checkpoint exists locally):\n"
        f"   - Ensure checkpoint is at: \"{root_dir / 'outputs' / 'hpo' / platform / backbone}\"\n"
        f"   - Verify 'local' is first in artifact_acquisition.yaml priority\n"
        f"   - Re-run this cell\n"
    )

    if is_azure_ml:
        error_msg += (
            f"\n2. **Manual download from Azure ML Studio**:\n"
            f"   - Go to: https://ml.azure.com\n"
            f"   - Navigate to: Experiments → {experiment_name} → Run {run_id[:8]}...\n"
            f"   - Download the 'best_trial_checkpoint' artifact (or 'checkpoint' if available)\n"
            f"   - Extract if it's a .tar.gz file\n"
            f"   - Place the checkpoint folder at: \"{manual_checkpoint_path}\"\n"
            f"   - Re-run this cell\n"
        )
    else:
        error_msg += (
            f"\n2. **Manual download from MLflow UI**:\n"
            f"   - Go to MLflow tracking UI (check tracking URI: {tracking_uri})\n"
            f"   - Navigate to: Experiment '{experiment_name}' → Run {run_id[:8]}...\n"
            f"   - Download the 'best_trial_checkpoint' artifact (or 'checkpoint' if available)\n"
            f"   - Extract if it's a .tar.gz file\n"
            f"   - Place the checkpoint folder at: \"{manual_checkpoint_path}\"\n"
            f"   - Re-run this cell\n"
        )

    raise ValueError(error_msg)
