"""
@meta
name: artifact_acquisition
type: utility
domain: selection
responsibility:
  - Checkpoint acquisition for best model selection
  - Local-first artifact loading with MLflow fallback
  - Checkpoint validation and extraction
inputs:
  - Best model selection results
  - MLflow run information
  - Local disk paths
outputs:
  - Checkpoint directories
  - Extracted model artifacts
tags:
  - utility
  - selection
  - artifacts
  - mlflow
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""
Artifact acquisition utilities for best model selection.

This module is a backward compatibility wrapper around the unified artifact
acquisition system. It maintains the original API for existing callers while
delegating all functionality to `artifact_unified.compat`.

**Consolidation Note**: This module no longer contains duplicate implementations
of validation, extraction, or discovery logic. All such functionality has been
consolidated into the `artifact_unified` modules:
- Validation: `artifact_unified.validation` (SSOT)
- Extraction: `artifact_unified.acquisition` (SSOT)
- Discovery: `artifact_unified.discovery` (SSOT)

The API remains the same for backward compatibility.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import os

# Import unified acquisition system
from evaluation.selection.artifact_unified.compat import acquire_best_model_checkpoint as _acquire_best_model_checkpoint_unified



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
