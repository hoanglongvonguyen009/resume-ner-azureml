from __future__ import annotations

"""
@meta
name: artifact_unified_acquisition
type: utility
domain: selection
responsibility:
  - Unified artifact acquisition orchestration
  - Coordinate discovery, validation, and download from multiple sources
  - Support local, drive, and MLflow sources
inputs:
  - Artifact requests
  - MLflow client
  - Root and config directories
outputs:
  - Artifact results with validated paths
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

"""Main artifact acquisition orchestration.

This module provides the unified API for artifact acquisition across all stages.
It orchestrates discovery, validation, and download from multiple sources.

**Single Source of Truth (SSOT)**: This module is the SSOT for tar.gz extraction
logic. All tar.gz extraction functionality should use `_extract_tar_gz()` from
this module to avoid duplication.
"""
import shutil
import tarfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import mlflow
# MlflowClient import removed - use create_mlflow_client() from infrastructure.tracking.mlflow.client instead

from common.shared.logging_utils import get_logger
from common.shared.platform_detection import detect_platform
from evaluation.selection.artifact_unified.discovery import (
    discover_artifact_drive,
    discover_artifact_local,
    discover_artifact_mlflow,
)
from evaluation.selection.artifact_unified.selectors import select_artifact_run_from_request
from evaluation.selection.artifact_unified.types import (
    ArtifactKind,
    ArtifactRequest,
    ArtifactResult,
    ArtifactSource,
    AvailabilityStatus,
    ArtifactLocation,
    RunSelectorResult,
)
from evaluation.selection.artifact_unified.validation import validate_artifact
from infrastructure.paths import resolve_output_path

logger = get_logger(__name__)


def acquire_artifact(
    request: ArtifactRequest,
    root_dir: Path,
    config_dir: Path,
    acquisition_config: Dict[str, Any],
    mlflow_client: Optional[MlflowClient] = None,
    experiment_id: Optional[str] = None,
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    backup_to_drive: Optional[Any] = None,
    in_colab: bool = False,
) -> ArtifactResult:
    """
    Acquire artifact using unified acquisition system.
    
    This is the main entry point for artifact acquisition. It:
    1. Selects the appropriate run (trial→refit mapping)
    2. Discovers artifact in priority order (from config)
    3. Validates artifact integrity
    4. Downloads/copies artifact to local destination
    
    Args:
        request: Artifact request
        root_dir: Project root directory
        config_dir: Config directory
        acquisition_config: Acquisition configuration (priority, validation, etc.)
        mlflow_client: Optional MLflow client (created if not provided)
        experiment_id: Optional MLflow experiment ID
        restore_from_drive: Optional function to restore from Drive backup
        backup_to_drive: Optional DriveBackupStore instance
        in_colab: Whether running in Google Colab
        
    Returns:
        ArtifactResult with success status and path
    """
    logger.info(
        f"Starting artifact acquisition: "
        f"artifact_kind={request.artifact_kind.value}, "
        f"backbone={request.backbone}, "
        f"run_id={request.run_id[:12] if request.run_id else 'N/A'}..., "
        f"study_key_hash={request.study_key_hash[:8] if request.study_key_hash else 'N/A'}..., "
        f"trial_key_hash={request.trial_key_hash[:8] if request.trial_key_hash else 'N/A'}..."
    )
    logger.debug(f"Acquisition config: {acquisition_config}")
    
    if mlflow_client is None:
        from infrastructure.tracking.mlflow.client import create_mlflow_client
        mlflow_client = create_mlflow_client()
    
    # Step 1: Select artifact run (trial→refit mapping, SSOT)
    if experiment_id is None:
        # Try to get experiment ID from request or MLflow
        try:
            if request.experiment_name:
                experiment = mlflow_client.get_experiment_by_name(request.experiment_name)
                if experiment:
                    experiment_id = experiment.experiment_id
        except Exception:
            pass
    
    if not experiment_id:
        # Fallback: try to get from run
        try:
            run = mlflow_client.get_run(request.run_id)
            experiment_id = run.info.experiment_id
        except Exception as e:
            return ArtifactResult(
                request=request,
                success=False,
                error=f"Could not determine experiment ID: {e}",
            )
    
    try:
        logger.debug(
            f"Selecting artifact run: run_id={request.run_id[:12] if request.run_id else 'N/A'}..., "
            f"experiment_id={experiment_id}, artifact_kind={request.artifact_kind.value}"
        )
        run_selector_result = select_artifact_run_from_request(
            request=request,
            mlflow_client=mlflow_client,
            experiment_id=experiment_id,
            config_dir=config_dir,
        )
        logger.info(
            f"Selected artifact run: artifact_run_id={run_selector_result.artifact_run_id[:12] if run_selector_result.artifact_run_id else 'N/A'}..., "
            f"trial_run_id={run_selector_result.trial_run_id[:12] if run_selector_result.trial_run_id else 'N/A'}..."
        )
    except Exception as e:
        error_msg = f"Run selection failed: {e}"
        logger.error(error_msg, exc_info=True)
        return ArtifactResult(
            request=request,
            success=False,
            error=error_msg,
        )
    
    # Step 2: Discover artifact in priority order (per-artifact-kind if configured)
    # Get priority for this artifact kind, fallback to global priority
    artifact_kinds_config = acquisition_config.get("artifact_kinds", {})
    kind_config = artifact_kinds_config.get(request.artifact_kind.value, {})
    priority = kind_config.get("priority") or acquisition_config.get("priority", ["local", "drive", "mlflow"])
    
    # Log acquisition config for debugging
    logger.info(
        f"Artifact acquisition config for {request.artifact_kind.value}: "
        f"priority={priority}, "
        f"local.enabled={acquisition_config.get('local', {}).get('enabled', True)}, "
        f"local.validate={acquisition_config.get('local', {}).get('validate', True)}, "
        f"drive.enabled={acquisition_config.get('drive', {}).get('enabled', True)}, "
        f"mlflow.enabled={acquisition_config.get('mlflow', {}).get('enabled', True)}"
    )
    
    discovered_location = None
    
    for source_name in priority:
        if source_name == "local":
            location = discover_artifact_local(
                request=request,
                root_dir=root_dir,
                config_dir=config_dir,
                validate=acquisition_config.get("local", {}).get("validate", True),
            )
            if location and location.status == AvailabilityStatus.VERIFIED:
                discovered_location = location
                break
        
        elif source_name == "drive" and in_colab and backup_to_drive:
            if not acquisition_config.get("drive", {}).get("enabled", True):
                continue
            location = discover_artifact_drive(
                request=request,
                root_dir=root_dir,
                config_dir=config_dir,
                backup_to_drive=backup_to_drive,
                validate=acquisition_config.get("drive", {}).get("validate", True),
            )
            if location and location.status == AvailabilityStatus.VERIFIED:
                discovered_location = location
                break
        
        elif source_name == "mlflow":
            if not acquisition_config.get("mlflow", {}).get("enabled", True):
                continue
            location = discover_artifact_mlflow(
                request=request,
                mlflow_client=mlflow_client,
                experiment_id=experiment_id,
                run_selector_result=run_selector_result,
                config_dir=config_dir,  # Pass config_dir explicitly (DRY principle)
                validate=False,  # Don't validate during discovery (expensive)
            )
            if location:
                discovered_location = location
                break
    
    if not discovered_location:
        error_msg = (
            f"Artifact not found in any configured source. "
            f"Checked sources in priority order: {priority}. "
            f"Request: artifact_kind={request.artifact_kind.value}, "
            f"run_id={request.run_id[:12] if request.run_id else 'N/A'}..., "
            f"backbone={request.backbone}"
        )
        logger.error(error_msg)
        return ArtifactResult(
            request=request,
            success=False,
            error=error_msg,
        )
    
    # Step 3: Acquire artifact (copy/download to local destination)
    try:
        logger.info(
            f"Acquiring artifact from {discovered_location.source.value}: "
            f"run_id={run_selector_result.artifact_run_id[:12] if run_selector_result.artifact_run_id else 'N/A'}..., "
            f"artifact_kind={request.artifact_kind.value}, "
            f"backbone={request.backbone}"
        )
        
        acquired_path = _acquire_from_location(
            location=discovered_location,
            request=request,
            root_dir=root_dir,
            config_dir=config_dir,
            run_selector_result=run_selector_result,
            acquisition_config=acquisition_config,
            mlflow_client=mlflow_client,
            restore_from_drive=restore_from_drive,
            backup_to_drive=backup_to_drive,
            in_colab=in_colab,
        )
        
        if not acquired_path:
            error_msg = f"Failed to acquire artifact from {discovered_location.source.value}"
            logger.error(error_msg)
            return ArtifactResult(
                request=request,
                success=False,
                error=error_msg,
            )
        
        # Step 4: Final validation
        validate = acquisition_config.get(discovered_location.source.value, {}).get("validate", True)
        if validate:
            logger.debug(f"Validating acquired artifact: {acquired_path}")
            is_valid, error = validate_artifact(
                request.artifact_kind,
                acquired_path,
                strict=True,
            )
            if not is_valid:
                error_msg = f"Acquired artifact failed validation: {error}, path={acquired_path}"
                logger.error(error_msg)
                return ArtifactResult(
                    request=request,
                    success=False,
                    error=error_msg,
                )
            logger.info(f"Artifact validation passed: {acquired_path}")
        
        return ArtifactResult(
            request=request,
            success=True,
            path=acquired_path,
            source=discovered_location.source,
            status=AvailabilityStatus.VERIFIED,
            metadata={
                "run_selector": run_selector_result.metadata,
                "discovery": discovered_location.metadata,
            },
        )
    
    except Exception as e:
        logger.error(f"Artifact acquisition failed: {e}", exc_info=True)
        return ArtifactResult(
            request=request,
            success=False,
            error=f"Acquisition error: {e}",
        )


def _acquire_from_location(
    location: ArtifactLocation,
    request: ArtifactRequest,
    root_dir: Path,
    config_dir: Path,
    run_selector_result: RunSelectorResult,
    acquisition_config: Dict[str, Any],
    mlflow_client: MlflowClient,
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    backup_to_drive: Optional[Any] = None,
    in_colab: bool = False,
) -> Optional[Path]:
    """
    Acquire artifact from discovered location (copy/download to local destination).
    
    Args:
        location: Discovered artifact location
        request: Artifact request
        root_dir: Project root directory
        config_dir: Config directory
        run_selector_result: Run selector result
        acquisition_config: Acquisition configuration
        mlflow_client: MLflow client
        restore_from_drive: Optional function to restore from Drive
        backup_to_drive: Optional DriveBackupStore
        in_colab: Whether in Colab
        
    Returns:
        Path to acquired artifact, or None if failed
    """
    # Build destination path
    destination = _build_artifact_destination(
        request=request,
        root_dir=root_dir,
        config_dir=config_dir,
        run_selector_result=run_selector_result,
    )
    
    logger.debug(f"Artifact destination path: {destination}")
    
    # Check if destination already exists and is valid (before any acquisition)
    # Also check for nested extracted checkpoints (e.g., destination/best_trial_checkpoint.tar.gz/best_trial_checkpoint)
    if destination.exists():
        # First check destination directly
        is_valid, error = validate_artifact(
            request.artifact_kind,
            destination,
            strict=False,  # Use lenient validation for existence check
        )
        
        # If not valid, check for nested extracted checkpoints
        if not is_valid and destination.is_dir():
            # Look for nested checkpoint directories (common after tar.gz extraction)
            nested_checkpoints = []
            for item in destination.iterdir():
                if item.is_dir():
                    # Check if this directory or a subdirectory is a valid checkpoint
                    is_valid_checkpoint, _ = validate_artifact(
                        ArtifactKind.CHECKPOINT,
                        item,
                        strict=False,  # Lenient mode for quick checks
                    )
                    if is_valid_checkpoint:
                        nested_checkpoints.append(item)
                    # Also check common nested patterns like tar.gz/best_trial_checkpoint
                    for subitem in item.iterdir():
                        if subitem.is_dir():
                            is_valid_subcheckpoint, _ = validate_artifact(
                                ArtifactKind.CHECKPOINT,
                                subitem,
                                strict=False,  # Lenient mode for quick checks
                            )
                            if is_valid_subcheckpoint:
                                nested_checkpoints.append(subitem)
            
            if nested_checkpoints:
                # Use the first valid nested checkpoint
                nested_checkpoint = nested_checkpoints[0]
                logger.info(
                    f"Found valid nested checkpoint at: {nested_checkpoint}. "
                    f"Skipping acquisition from {location.source.value}."
                )
                return nested_checkpoint
        
        if is_valid:
            logger.info(
                f"Artifact already exists at destination and is valid: {destination}. "
                f"Skipping acquisition from {location.source.value}."
            )
            return destination
        else:
            logger.warning(
                f"Artifact exists at {destination} but failed validation: {error}. "
                f"Will re-acquire from {location.source.value}."
            )
    
    if location.source == ArtifactSource.LOCAL:
        # Copy from local disk
        if location.path == destination:
            return destination  # Already in place
        
        # Check if source is inside destination (e.g., nested tar.gz extraction)
        # In this case, we should use the source path directly
        try:
            # Check if source is a subdirectory of destination
            source_str = str(location.path.resolve())
            dest_str = str(destination.resolve())
            if source_str.startswith(dest_str + "/") or source_str == dest_str:
                # Source is inside or equal to destination - use source directly
                logger.info(f"Artifact already in destination location: {location.path}")
                return location.path
        except Exception:
            # If path resolution fails, continue with copy logic
            pass
        
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(location.path, destination)
        logger.info(f"Copied artifact from local: {location.path} -> {destination}")
        return destination
    
    elif location.source == ArtifactSource.DRIVE:
        # Copy from Drive
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(location.path, destination)
        logger.info(f"Copied artifact from Drive: {location.path} -> {destination}")
        return destination
    
    elif location.source == ArtifactSource.MLFLOW:
        # Download from MLflow
        if run_selector_result.artifact_run_id is None:
            logger.error("Cannot download from MLflow: artifact_run_id is None")
            return None
        return _download_from_mlflow(
            run_id=run_selector_result.artifact_run_id,
            request=request,
            destination=destination,
            acquisition_config=acquisition_config,
            mlflow_client=mlflow_client,
        )
    # All ArtifactSource enum values are handled above (LOCAL, DRIVE, MLFLOW)
    # This should never be reached, but kept for defensive programming
    raise ValueError(f"Unsupported artifact source: {location.source}")


def _build_artifact_destination(
    request: ArtifactRequest,
    root_dir: Path,
    config_dir: Path,
    run_selector_result: RunSelectorResult,
) -> Path:
    """
    Build destination path for acquired artifact.
    
    Args:
        request: Artifact request
        root_dir: Project root directory
        config_dir: Config directory
        run_selector_result: Run selector result
        
    Returns:
        Path to destination directory
    """
    environment = detect_platform()
    backbone_name = request.backbone.split("-")[0] if "-" in request.backbone else request.backbone
    
    # Build base directory based on artifact kind and use case
    # Allow override via metadata for different use cases (e.g., benchmarking)
    output_base_dir = request.metadata.get("output_base_dir")
    
    if request.artifact_kind == ArtifactKind.CHECKPOINT:
        # Use provided base dir, or default to "best_model_selection" for backward compatibility
        base_dir_name = output_base_dir or "best_model_selection"
        base_dir = resolve_output_path(
            root_dir, config_dir, base_dir_name
        ) / environment / backbone_name
    else:
        base_dir = resolve_output_path(
            root_dir, config_dir, output_base_dir or "artifacts"
        ) / environment / backbone_name
    
    # Build subdirectory using hashes if available
    if request.study_key_hash and request.trial_key_hash:
        study8 = request.study_key_hash[:8] if len(request.study_key_hash) >= 8 else request.study_key_hash
        trial8 = request.trial_key_hash[:8] if len(request.trial_key_hash) >= 8 else request.trial_key_hash
        return base_dir / f"{request.artifact_kind.value}_{study8}_{trial8}"
    
    # Fallback: use run_id
    run_id = run_selector_result.artifact_run_id
    if not run_id:
        # Last resort: use request.run_id
        run_id = request.run_id
    return base_dir / f"{request.artifact_kind.value}_{run_id[:8]}"


def _download_from_mlflow(
    run_id: str,
    request: ArtifactRequest,
    destination: Path,
    acquisition_config: Dict[str, Any],
    mlflow_client: MlflowClient,
) -> Optional[Path]:
    """
    Download artifact from MLflow.
    
    Args:
        run_id: MLflow run ID
        request: Artifact request
        destination: Destination path
        acquisition_config: Acquisition configuration
        mlflow_client: MLflow client
        
    Returns:
        Path to downloaded artifact, or None if failed
    """
    # Check if destination already exists and is valid
    # Also check for nested extracted checkpoints (e.g., destination/best_trial_checkpoint.tar.gz/best_trial_checkpoint)
    if destination.exists():
        # First check destination directly
        is_valid, error = validate_artifact(
            request.artifact_kind,
            destination,
            strict=False,  # Use lenient validation for existence check
        )
        
        # If not valid, check for nested extracted checkpoints
        if not is_valid and destination.is_dir():
            # Look for nested checkpoint directories (common after tar.gz extraction)
            nested_checkpoints = []
            for item in destination.iterdir():
                if item.is_dir():
                    # Check if this directory or a subdirectory is a valid checkpoint
                    is_valid_checkpoint, _ = validate_artifact(
                        ArtifactKind.CHECKPOINT,
                        item,
                        strict=False,  # Lenient mode for quick checks
                    )
                    if is_valid_checkpoint:
                        nested_checkpoints.append(item)
                    # Also check common nested patterns like tar.gz/best_trial_checkpoint
                    for subitem in item.iterdir():
                        if subitem.is_dir():
                            is_valid_subcheckpoint, _ = validate_artifact(
                                ArtifactKind.CHECKPOINT,
                                subitem,
                                strict=False,  # Lenient mode for quick checks
                            )
                            if is_valid_subcheckpoint:
                                nested_checkpoints.append(subitem)
            
            if nested_checkpoints:
                # Use the first valid nested checkpoint
                nested_checkpoint = nested_checkpoints[0]
                logger.info(
                    f"Found valid nested checkpoint at: {nested_checkpoint}. "
                    f"Skipping download from MLflow."
                )
                return nested_checkpoint
        
        if is_valid:
            logger.info(
                f"Artifact already exists at destination and is valid: {destination}. "
                f"Skipping download from MLflow."
            )
            return destination
        else:
            logger.warning(
                f"Artifact exists at {destination} but failed validation: {error}. "
                f"Will re-download from MLflow."
            )
    
    try:
        logger.info(f"Downloading artifact from MLflow: run_id={run_id[:12]}..., destination={destination}")
        # List artifacts to find the right one
        artifacts = mlflow_client.list_artifacts(run_id=run_id)
        artifact_paths = [a.path for a in artifacts]
        
        # Determine artifact path based on kind
        artifact_path = None
        if request.artifact_kind == ArtifactKind.CHECKPOINT:
            # Look for checkpoint artifacts
            checkpoint_artifacts = [
                p for p in artifact_paths
                if "checkpoint" in p.lower() or "best_trial" in p.lower()
            ]
            if checkpoint_artifacts:
                # Prefer best_trial_checkpoint
                for path in checkpoint_artifacts:
                    if "best_trial_checkpoint" in path.lower():
                        artifact_path = path
                        break
                if not artifact_path:
                    artifact_path = checkpoint_artifacts[0]
            else:
                # Default fallback
                artifact_path = "best_trial_checkpoint.tar.gz"
        
        if not artifact_path:
            logger.warning(f"No artifact path found for {request.artifact_kind} in run {run_id[:12]}...")
            return None
        
        # Download artifact
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            downloaded_path = mlflow_client.download_artifacts(
                run_id=run_id,
                path=artifact_path,
                dst_path=str(destination),
            )
            logger.info(f"Successfully downloaded artifact from MLflow to: {downloaded_path}")
        except Exception as e:
            logger.error(
                f"Failed to download artifact from MLflow: run_id={run_id[:12]}..., "
                f"artifact_path={artifact_path}, destination={destination}, error={e}",
                exc_info=True
            )
            return None
        
        downloaded_path = Path(downloaded_path)
        
        # Extract if tar.gz
        try:
            if downloaded_path.is_file() and downloaded_path.suffixes == ['.tar', '.gz']:
                logger.debug(f"Extracting tar.gz file: {downloaded_path}")
                # Extract to destination directory (not to tar.gz's parent)
                extracted_path = _extract_tar_gz(downloaded_path, extract_to=destination)
                # Clean up tar.gz file after extraction
                try:
                    downloaded_path.unlink()
                    logger.debug(f"Cleaned up tar.gz file: {downloaded_path}")
                except Exception as e:
                    logger.debug(f"Could not clean up tar.gz file: {e}")
                downloaded_path = extracted_path
            elif downloaded_path.is_dir():
                tar_files = list(downloaded_path.glob("*.tar.gz")) + list(downloaded_path.glob("*.tgz"))
                if tar_files:
                    logger.debug(f"Found tar.gz file in directory, extracting: {tar_files[0]}")
                    # Extract to destination directory
                    extracted_path = _extract_tar_gz(tar_files[0], extract_to=destination)
                    # Clean up tar.gz file after extraction
                    try:
                        tar_files[0].unlink()
                        logger.debug(f"Cleaned up tar.gz file: {tar_files[0]}")
                    except Exception as e:
                        logger.debug(f"Could not clean up tar.gz file: {e}")
                    downloaded_path = extracted_path
        except Exception as e:
            logger.error(f"Failed to extract tar.gz file: {e}", exc_info=True)
            return None
        
        # Find checkpoint in extracted directory if needed
        if request.artifact_kind == ArtifactKind.CHECKPOINT and downloaded_path.is_dir():
            # First check for "checkpoint" subdirectory
            checkpoint_subdir = downloaded_path / "checkpoint"
            if checkpoint_subdir.exists() and checkpoint_subdir.is_dir():
                is_valid, _ = validate_artifact(
                    ArtifactKind.CHECKPOINT,
                    checkpoint_subdir,
                    strict=False,  # Lenient mode for quick checks
                )
                if is_valid:
                    logger.info(f"Found checkpoint subdirectory: {checkpoint_subdir}")
                    return checkpoint_subdir
            
            # Check if directory itself is checkpoint
            is_valid, _ = validate_artifact(
                ArtifactKind.CHECKPOINT,
                downloaded_path,
                strict=False,  # Lenient mode for quick checks
            )
            if is_valid:
                logger.info(f"Directory is a valid checkpoint: {downloaded_path}")
                return downloaded_path
            
            # If still not found, search recursively for checkpoint directories
            logger.debug(f"Searching recursively for checkpoint in: {downloaded_path}")
            for item in downloaded_path.rglob("*"):
                if item.is_dir():
                    is_valid, _ = validate_artifact(
                        ArtifactKind.CHECKPOINT,
                        item,
                        strict=False,  # Lenient mode for quick checks
                    )
                    if is_valid:
                        logger.info(f"Found checkpoint in nested directory: {item}")
                        return item
        
        logger.info(f"Artifact acquired successfully: {downloaded_path}")
        return downloaded_path
    
    except Exception as e:
        logger.error(
            f"MLflow download failed: run_id={run_id[:12]}..., "
            f"artifact_kind={request.artifact_kind.value}, error={e}",
            exc_info=True
        )
        return None


def _extract_tar_gz(tar_path: Path, extract_to: Optional[Path] = None) -> Path:
    """
    Extract tar.gz file and return path to extracted directory.
    
    If the archive has a single root directory, moves its contents to extract_to
    to avoid nested directory structures.
    """
    if extract_to is None:
        extract_to = tar_path.parent
    
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    
    with tarfile.open(tar_path, 'r:gz') as tar:
        members = tar.getmembers()
        if members:
            # Extract to a temporary subdirectory first
            temp_extract = extract_to / "_temp_extract"
            temp_extract.mkdir(exist_ok=True)
            tar.extractall(path=temp_extract)
            
            # Check if archive has a single root directory
            root_names = {Path(m.name).parts[0] for m in members if m.name}
            if len(root_names) == 1:
                root_name = list(root_names)[0]
                root_path = temp_extract / root_name
                
                if root_path.exists():
                    # Move contents of root directory to extract_to
                    import shutil
                    for item in root_path.iterdir():
                        dest_item = extract_to / item.name
                        if dest_item.exists():
                            if dest_item.is_dir():
                                shutil.rmtree(dest_item)
                            else:
                                dest_item.unlink()
                        shutil.move(str(item), str(extract_to))
                    
                    # Clean up temp directory
                    try:
                        shutil.rmtree(temp_extract)
                    except Exception as e:
                        logger.debug(f"Could not clean up temp extract directory: {e}")
                    
                    return extract_to
                else:
                    return temp_extract
            else:
                # Multiple root items - move all to extract_to
                import shutil
                for item in temp_extract.iterdir():
                    dest_item = extract_to / item.name
                    if dest_item.exists():
                        if dest_item.is_dir():
                            shutil.rmtree(dest_item)
                        else:
                            dest_item.unlink()
                    shutil.move(str(item), str(extract_to))
                
                # Clean up temp directory
                try:
                    shutil.rmtree(temp_extract)
                except Exception as e:
                    logger.debug(f"Could not clean up temp extract directory: {e}")
                
                return extract_to
    
    return extract_to



