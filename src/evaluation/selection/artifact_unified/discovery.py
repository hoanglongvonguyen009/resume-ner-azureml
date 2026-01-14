"""
@meta
name: artifact_unified_discovery
type: utility
domain: selection
responsibility:
  - Artifact discovery for local/drive/mlflow sources
  - Check artifact availability without downloading
  - Prioritize sources (local > drive > mlflow)
inputs:
  - Artifact requests
  - Root and config directories
outputs:
  - Artifact locations with availability status
tags:
  - utility
  - selection
  - artifacts
  - discovery
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Artifact discovery for local/drive/mlflow sources.

This module provides discovery functions that check for artifact availability
in different sources (local disk, Google Drive, MLflow) without downloading.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from mlflow.tracking import MlflowClient

from common.shared.logging_utils import get_logger
from common.shared.platform_detection import detect_platform
from evaluation.selection.artifact_unified.types import (
    ArtifactKind,
    ArtifactLocation,
    ArtifactRequest,
    ArtifactSource,
    AvailabilityStatus,
    RunSelectorResult,
)
from evaluation.selection.artifact_unified.validation import validate_artifact
from infrastructure.paths import build_output_path, resolve_output_path

logger = get_logger(__name__)


def _check_checkpoint_files(path: Path) -> bool:
    """Check if a directory contains essential checkpoint files."""
    if not path.exists() or not path.is_dir():
        return False
    has_model = any(
        (path / f).exists() 
        for f in ["pytorch_model.bin", "model.safetensors", "model.bin"]
    )
    has_config = (path / "config.json").exists()
    return has_model and has_config


def discover_artifact_local(
    request: ArtifactRequest,
    root_dir: Path,
    config_dir: Path,
    validate: bool = True,
) -> Optional[ArtifactLocation]:
    """
    Discover artifact on local disk.
    
    Discovery priority:
    1. Refit-run-id-based cache (if refit_run_id/artifact_run_id available)
    2. Hash-based paths in configurable search roots
    3. HPO output directory (original checkpoints from training)
    
    Args:
        request: Artifact request
        root_dir: Project root directory
        config_dir: Config directory
        validate: If True, validate artifact integrity
        
    Returns:
        ArtifactLocation if found, None otherwise
    """
    if request.artifact_kind != ArtifactKind.CHECKPOINT:
        # Only checkpoints are supported for local discovery currently
        return None
    
    if not request.study_key_hash or not request.trial_key_hash:
        logger.debug("Missing hashes for local discovery")
        return None
    
    environment = detect_platform()
    backbone_name = request.backbone.split("-")[0] if "-" in request.backbone else request.backbone
    
    # Priority 1: Refit-run-id-based discovery (most reliable)
    # This is the primary key for refit checkpoints
    artifact_run_id = request.metadata.get("artifact_run_id") or request.refit_run_id
    if artifact_run_id:
        location = _discover_by_run_id(
            artifact_run_id=artifact_run_id,
            request=request,
            root_dir=root_dir,
            config_dir=config_dir,
            environment=environment,
            backbone_name=backbone_name,
            validate=validate,
        )
        if location:
            return location
    
    # Priority 2: Hash-based discovery in configurable search roots
    location = _discover_by_hash_in_roots(
        request=request,
        root_dir=root_dir,
        config_dir=config_dir,
        environment=environment,
        backbone_name=backbone_name,
        validate=validate,
    )
    if location:
        return location
    
    # Priority 3: HPO output directory (original checkpoints)
    return _discover_in_hpo_output(
        request=request,
        root_dir=root_dir,
        config_dir=config_dir,
        environment=environment,
        backbone_name=backbone_name,
        validate=validate,
    )


def _discover_by_run_id(
    artifact_run_id: str,
    request: ArtifactRequest,
    root_dir: Path,
    config_dir: Path,
    environment: str,
    backbone_name: str,
    validate: bool,
) -> Optional[ArtifactLocation]:
    """Discover artifact by run_id in configurable cache roots."""
    # Get search roots from config (defaults to common locations)
    search_roots = request.metadata.get("search_roots", ["artifacts", "best_model_selection"])
    
    logger.debug(
        f"Searching for artifact by run_id in search_roots: {search_roots} "
        f"(from config: {'yes' if 'search_roots' in request.metadata else 'no, using defaults'})"
    )
    
    for root_name in search_roots:
        try:
            base_dir = resolve_output_path(root_dir, config_dir, root_name) / environment / backbone_name
            # Use run_id as cache key (first 12 chars for readability)
            cache_key = f"{request.artifact_kind.value}_{artifact_run_id[:12]}"
            cache_path = base_dir / cache_key
            
            checkpoint_path = _find_checkpoint_in_path(cache_path)
            if checkpoint_path:
                if validate:
                    is_valid, error = validate_artifact(
                        request.artifact_kind,
                        checkpoint_path,
                        strict=True,
                    )
                    if not is_valid:
                        logger.debug(f"Cache entry invalid in {root_name}: {error}")
                        continue
                
                logger.info(f"Found artifact by run_id in {root_name}/: {checkpoint_path}")
                return ArtifactLocation(
                    source=ArtifactSource.LOCAL,
                    path=checkpoint_path,
                    status=AvailabilityStatus.VERIFIED,
                    metadata={
                        "discovery_method": "run_id_cache",
                        "cache_root": root_name,
                        "validated": validate,
                    },
                )
        except Exception as e:
            logger.debug(f"Run-id discovery in {root_name} failed: {type(e).__name__}: {e}")
    
    return None


def _discover_by_hash_in_roots(
    request: ArtifactRequest,
    root_dir: Path,
    config_dir: Path,
    environment: str,
    backbone_name: str,
    validate: bool,
) -> Optional[ArtifactLocation]:
    """Discover artifact by hash in configurable search roots."""
    if not request.study_key_hash or not request.trial_key_hash:
        return None
    study8 = request.study_key_hash[:8] if len(request.study_key_hash) >= 8 else request.study_key_hash
    trial8 = request.trial_key_hash[:8] if len(request.trial_key_hash) >= 8 else request.trial_key_hash
    artifact_dir_name = f"{request.artifact_kind.value}_{study8}_{trial8}"
    
    # Get search roots from config (defaults to common locations)
    search_roots = request.metadata.get("search_roots", ["artifacts", "best_model_selection"])
    
    logger.debug(
        f"Searching for artifact by hash in search_roots: {search_roots} "
        f"(from config: {'yes' if 'search_roots' in request.metadata else 'no, using defaults'})"
    )
    
    for root_name in search_roots:
        try:
            base_dir = resolve_output_path(root_dir, config_dir, root_name) / environment / backbone_name
            destination_path = base_dir / artifact_dir_name
            
            checkpoint_path = _find_checkpoint_in_path(destination_path)
            if checkpoint_path:
                if validate:
                    is_valid, error = validate_artifact(
                        request.artifact_kind,
                        checkpoint_path,
                        strict=True,
                    )
                    if not is_valid:
                        logger.debug(f"Hash-based artifact invalid in {root_name}: {error}")
                        continue
                
                logger.info(f"Found artifact by hash in {root_name}/: {checkpoint_path}")
                return ArtifactLocation(
                    source=ArtifactSource.LOCAL,
                    path=checkpoint_path,
                    status=AvailabilityStatus.VERIFIED,
                    metadata={
                        "discovery_method": "hash_based",
                        "cache_root": root_name,
                        "validated": validate,
                    },
                )
        except Exception as e:
            logger.debug(f"Hash discovery in {root_name} failed: {type(e).__name__}: {e}")
    
    return None


def _find_checkpoint_in_path(path: Path) -> Optional[Path]:
    """
    Find checkpoint files in a given path.
    
    Supports:
    - Direct checkpoint directory (contains model files + config.json)
    - Extracted tar.gz directories (best_trial_checkpoint/, checkpoint/, etc.)
    - Tar.gz files (detected but not extracted - would need extraction)
    
    Args:
        path: Path to search for checkpoint
        
    Returns:
        Path to checkpoint directory if found, None otherwise
    """
    if not path.exists():
        return None
    
    # Check if path itself is a checkpoint directory
    if path.is_dir() and _check_checkpoint_files(path):
        return path
    
    # Check for extracted tar.gz directories first (before checking for tar.gz files)
    # This handles the case where tar.gz was already extracted in a previous run
    if path.is_dir():
        # Look for common extracted structures
        for subdir_name in ["best_trial_checkpoint", "checkpoint"]:
            subdir = path / subdir_name
            if subdir.exists() and subdir.is_dir() and _check_checkpoint_files(subdir):
                return subdir
        
        # Check for directories that look like extracted tar.gz (name ends with .tar.gz)
        for item in path.iterdir():
            if item.is_dir() and item.name.endswith(".tar.gz"):
                # Check inside the extracted directory
                checkpoint_subdir = item / "checkpoint"
                if checkpoint_subdir.exists() and checkpoint_subdir.is_dir() and _check_checkpoint_files(checkpoint_subdir):
                    return checkpoint_subdir
                
                best_trial_dir = item / "best_trial_checkpoint"
                if best_trial_dir.exists() and best_trial_dir.is_dir() and _check_checkpoint_files(best_trial_dir):
                    return best_trial_dir
                
                # Or the extracted directory itself might contain checkpoint files
                if _check_checkpoint_files(item):
                    return item
    
    # Check for tar.gz files (not extracted yet) - only if no extracted checkpoint found
    if path.is_dir():
        tar_gz_files = list(path.glob("*.tar.gz"))
        if tar_gz_files:
            # For now, return None for tar.gz files - let acquisition handle extraction
            # In future, could extract to temp and return extracted path
            logger.debug(f"Found tar.gz file in {path} (extraction not implemented in discovery)")
            # TODO: Extract and validate, or return None to trigger download
            # For now, don't return tar.gz files - let acquisition handle extraction
            return None
    
    return None


def _discover_in_hpo_output(
    request: ArtifactRequest,
    root_dir: Path,
    config_dir: Path,
    environment: str,
    backbone_name: str,
    validate: bool,
) -> Optional[ArtifactLocation]:
    """Discover artifact in HPO output directory (original checkpoints)."""
    try:
        from evaluation.selection.local_selection_v2 import find_trial_checkpoint_by_hash
        
        # Build HPO output directory path manually (outputs/hpo/{environment}/{backbone_name})
        hpo_output_dir = root_dir / "outputs" / "hpo" / environment / backbone_name
        
        if request.study_key_hash is None or request.trial_key_hash is None:
            return None

        found_path = find_trial_checkpoint_by_hash(
            hpo_backbone_dir=hpo_output_dir,
            study_key_hash=request.study_key_hash,
            trial_key_hash=request.trial_key_hash,
        )
        
        if found_path:
            found_path = Path(found_path)
            if found_path.exists():
                status = AvailabilityStatus.VERIFIED
                if validate:
                    is_valid, error = validate_artifact(
                        request.artifact_kind,
                        found_path,
                        strict=True,
                    )
                    if not is_valid:
                        status = AvailabilityStatus.INVALID
                        logger.warning(f"HPO artifact found but invalid: {error}")
                
                logger.debug(f"Found artifact in HPO directory: {found_path}")
                return ArtifactLocation(
                    source=ArtifactSource.LOCAL,
                    path=found_path,
                    status=status,
                    metadata={
                        "discovery_method": "hpo_hash_lookup",
                        "validated": validate,
                    },
                )
    except Exception as e:
        logger.debug(f"HPO directory discovery failed: {type(e).__name__}: {e}")
    
    return None


def discover_artifact_drive(
    request: ArtifactRequest,
    root_dir: Path,
    config_dir: Path,
    drive_store: Optional[Any] = None,
    validate: bool = True,
) -> Optional[ArtifactLocation]:
    """
    Discover artifact on Google Drive.
    
    Args:
        request: Artifact request
        root_dir: Project root directory
        config_dir: Config directory
        drive_store: DriveBackupStore instance for Drive access
        validate: If True, validate artifact integrity
        
    Returns:
        ArtifactLocation if found, None otherwise
    """
    if request.artifact_kind != ArtifactKind.CHECKPOINT:
        # Only checkpoints are supported for Drive discovery currently
        return None
    
    if not drive_store:
        return None
    
    if not request.study_key_hash or not request.trial_key_hash:
        logger.debug("Missing hashes for Drive discovery")
        return None
    
    try:
        environment = detect_platform()
        backbone_name = request.backbone.split("-")[0] if "-" in request.backbone else request.backbone
        
        hpo_output_dir = root_dir / "outputs" / "hpo" / environment / backbone_name
        
        # Compute Drive path
        try:
            drive_hpo_dir = drive_store.drive_path_for(hpo_output_dir)
        except ValueError:
            return None
        
        if not drive_hpo_dir or not drive_hpo_dir.exists():
            return None
        
        # Scan Drive directory structure
        found_path = _find_checkpoint_in_drive_by_hash(
            drive_hpo_dir,
            request.study_key_hash,
            request.trial_key_hash,
        )
        
        if found_path and found_path.exists():
            status = AvailabilityStatus.VERIFIED
            if validate:
                is_valid, error = validate_artifact(
                    request.artifact_kind,
                    found_path,
                    strict=True,
                )
                if not is_valid:
                    status = AvailabilityStatus.INVALID
                    logger.warning(f"Drive artifact found but invalid: {error}")
            
            return ArtifactLocation(
                source=ArtifactSource.DRIVE,
                path=found_path,
                status=status,
                metadata={
                    "discovery_method": "hash_scan",
                    "validated": validate,
                },
            )
    except Exception as e:
        logger.debug(f"Drive discovery failed: {e}")
    
    return None


def discover_artifact_mlflow(
    request: ArtifactRequest,
    mlflow_client: MlflowClient,
    experiment_id: str,
    run_selector_result: RunSelectorResult,
    validate: bool = False,  # MLflow discovery doesn't validate (just checks tag)
) -> Optional[ArtifactLocation]:
    """
    Discover artifact in MLflow (check availability tag, don't download).
    
    Args:
        request: Artifact request
        mlflow_client: MLflow client instance
        experiment_id: MLflow experiment ID
        run_selector_result: Result from run selector (contains artifact_run_id)
        validate: If True, check artifact actually exists (requires download - expensive)
        
    Returns:
        ArtifactLocation if available, None otherwise
    """
    artifact_run_id = run_selector_result.artifact_run_id
    
    if not artifact_run_id:
        return None
    
    try:
        run = mlflow_client.get_run(artifact_run_id)
        
        # Check artifact availability tag (declared availability)
        from infrastructure.naming.mlflow.tags_registry import load_tags_registry
        tags_registry = load_tags_registry(request.metadata.get("config_dir"))
        artifact_tag = tags_registry.key("artifact", "available")
        
        artifact_available = run.data.tags.get(artifact_tag, "false").lower()
        is_declared = artifact_available in ("true", "1", "yes")
        
        if not is_declared:
            return None
        
        # If validate=True, actually check artifact exists (expensive - lists artifacts)
        status = AvailabilityStatus.DECLARED
        if validate:
            try:
                artifacts = mlflow_client.list_artifacts(run_id=artifact_run_id)
                artifact_paths = [a.path for a in artifacts]
                
                # Check for checkpoint artifacts
                if request.artifact_kind == ArtifactKind.CHECKPOINT:
                    has_checkpoint = any(
                        "checkpoint" in p.lower() or "best_trial" in p.lower()
                        for p in artifact_paths
                    )
                    if has_checkpoint:
                        status = AvailabilityStatus.VERIFIED
                    else:
                        status = AvailabilityStatus.MISSING
            except Exception as e:
                logger.debug(f"Could not verify MLflow artifact: {e}")
                status = AvailabilityStatus.DECLARED  # Fallback to declared
        
        # Return location (path is MLflow run_id, not filesystem path)
        return ArtifactLocation(
            source=ArtifactSource.MLFLOW,
            path=Path(artifact_run_id),  # Placeholder - actual path after download
            status=status,
            metadata={
                "run_id": artifact_run_id,
                "experiment_id": experiment_id,
                "declared": is_declared,
                "validated": validate,
            },
        )
    except Exception as e:
        logger.debug(f"MLflow discovery failed: {e}")
        return None


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
                            # Return first fold checkpoint
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

