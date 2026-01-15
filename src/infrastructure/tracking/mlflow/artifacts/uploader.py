from __future__ import annotations

"""
@meta
name: tracking_mlflow_artifacts_uploader
type: utility
domain: tracking
responsibility:
  - Unified artifact upload interface for all stages
  - Stage-aware config checking
  - Consistent run_id handling
inputs:
  - Run IDs, stages, config directories
  - Artifact paths (files, directories, archives)
outputs:
  - Upload success status
tags:
  - utility
  - tracking
  - mlflow
  - artifacts
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Unified artifact uploader for all MLflow artifact operations."""
from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.logging_utils import get_logger

# Import directly from parent artifacts.py to avoid circular import with __init__.py
# Use importlib to load the parent artifacts.py file directly
import importlib.util

_artifacts_file_path = Path(__file__).parent.parent / "artifacts.py"
if _artifacts_file_path.exists():
    _spec = importlib.util.spec_from_file_location(
        "infrastructure.tracking.mlflow._artifacts_file", 
        _artifacts_file_path
    )
    if _spec and _spec.loader:
        _artifacts_module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_artifacts_module)
        log_artifact_safe = _artifacts_module.log_artifact_safe
        log_artifacts_safe = _artifacts_module.log_artifacts_safe
        upload_checkpoint_archive = _artifacts_module.upload_checkpoint_archive
    else:
        raise ImportError("Could not load artifacts.py module")
else:
    raise ImportError(f"artifacts.py not found at {_artifacts_file_path}")
from orchestration.jobs.tracking.config.loader import get_tracking_config
from infrastructure.tracking.mlflow.utils import get_mlflow_run_id
from infrastructure.tracking.mlflow.artifacts.manager import create_checkpoint_archive

logger = get_logger(__name__)


class ArtifactUploader:
    """
    Unified artifact uploader for all stages.
    
    This class provides a single interface for artifact uploads across
    all stages (training, conversion, benchmarking, HPO) with:
    - Stage-aware config checking
    - Consistent run_id handling
    - Built-in retry logic via existing utilities
    - Lazy config loading
    """
    
    def __init__(
        self,
        run_id: Optional[str] = None,
        stage: Optional[str] = None,
        config_dir: Optional[Path] = None,
    ):
        """
        Initialize artifact uploader.
        
        Args:
            run_id: Optional MLflow run ID. If None, will be detected from
                   active run or MLFLOW_RUN_ID environment variable.
            stage: Optional stage name ("training", "conversion", "benchmark").
                  Used for stage-specific config checking.
            config_dir: Optional path to config directory for tracking config.
        """
        self._run_id = run_id
        self._stage = stage
        self._config_dir = config_dir
        self._tracking_config: Optional[Dict[str, Any]] = None
    
    def _get_run_id(self) -> Optional[str]:
        """Get run ID, detecting from active run or env if not provided."""
        if self._run_id is not None:
            return self._run_id
        return get_mlflow_run_id()
    
    def _get_tracking_config(self) -> Dict[str, Any]:
        """
        Get tracking config for the current stage (lazy loading).
        
        Returns:
            Tracking config dictionary with defaults applied.
        """
        if self._tracking_config is None:
            if self._stage:
                self._tracking_config = get_tracking_config(
                    config_dir=self._config_dir,
                    stage=self._stage,
                )
            else:
                # No stage specified, return empty dict with defaults
                self._tracking_config = {"enabled": True}
        return self._tracking_config
    
    def get_tracking_config(self) -> Dict[str, Any]:
        """
        Get tracking config for the current stage.
        
        Returns:
            Tracking config dictionary with defaults applied.
        """
        return self._get_tracking_config()
    
    def _is_upload_enabled(self, skip_if_disabled: bool = True) -> bool:
        """
        Check if artifact uploads are enabled for this stage.
        
        Args:
            skip_if_disabled: If True, return False when disabled.
                             If False, always return True (skip check).
        
        Returns:
            True if uploads are enabled, False otherwise.
        """
        if not skip_if_disabled:
            return True
        
        config = self._get_tracking_config()
        return config.get("enabled", True)
    
    def upload_checkpoint(
        self,
        checkpoint_dir: Path,
        artifact_path: str = "checkpoint.tar.gz",
        trial_number: Optional[int] = None,
        skip_if_disabled: bool = True,
    ) -> bool:
        """
        Upload a checkpoint directory to MLflow as a compressed archive.
        
        This method automatically creates a tar.gz archive from the checkpoint directory,
        includes manifest metadata, and uploads it as a single file. This provides:
        - Compression benefits (smaller upload size)
        - Single file upload (faster, more reliable)
        - Automatic manifest generation with file count, sizes, and trial number
        
        Args:
            checkpoint_dir: Path to checkpoint directory.
            artifact_path: Artifact path within run's artifact directory.
                          Defaults to "checkpoint.tar.gz". If not ending in .tar.gz,
                          the extension will be automatically appended.
            trial_number: Optional trial number for manifest metadata (default: 0).
                         Used primarily for HPO checkpoints.
            skip_if_disabled: If True, skip upload when tracking is disabled.
        
        Returns:
            True if upload succeeded, False otherwise.
        """
        if not self._is_upload_enabled(skip_if_disabled):
            logger.debug(
                f"[ArtifactUploader] Upload disabled for stage={self._stage}, "
                f"skipping checkpoint upload"
            )
            return False
        
        # Check stage-specific config if stage is set
        if self._stage == "training":
            config = self._get_tracking_config()
            if not config.get("log_checkpoint", True):
                logger.debug(
                    "[ArtifactUploader] Checkpoint logging disabled "
                    "(tracking.training.log_checkpoint=false)"
                )
                return False
        
        checkpoint_dir = Path(checkpoint_dir)
        if not checkpoint_dir.exists():
            logger.warning(f"Checkpoint directory does not exist: {checkpoint_dir}")
            return False
        
        # Auto-append .tar.gz if not present
        if not artifact_path.endswith('.tar.gz'):
            artifact_path = f"{artifact_path}.tar.gz"
        
        # Use trial_number=0 as default if not provided
        trial_number = trial_number if trial_number is not None else 0
        
        # Create archive
        archive_path = None
        try:
            logger.info(f"Creating checkpoint archive from {checkpoint_dir}...")
            archive_path, manifest = create_checkpoint_archive(
                checkpoint_dir=checkpoint_dir,
                trial_number=trial_number,
            )
            
            # Upload archive using upload_checkpoint_archive
            run_id = self._get_run_id()
            success = self.upload_checkpoint_archive(
                archive_path=archive_path,
                manifest=manifest,
                artifact_path=artifact_path,
                skip_if_disabled=False,  # Already checked above
            )
            
            if success:
                logger.info(
                    f"Successfully uploaded checkpoint archive: {manifest['file_count']} files "
                    f"({manifest['total_size'] / 1024 / 1024:.1f}MB) for trial {trial_number}"
                )
            
            return success
            
        except Exception as e:
            logger.warning(
                f"Failed to create/upload checkpoint archive: {e}",
                exc_info=True
            )
            return False
        finally:
            # Clean up temp archive file
            if archive_path and archive_path.exists():
                try:
                    archive_path.unlink()
                    logger.debug(f"Cleaned up temporary archive: {archive_path}")
                except Exception as cleanup_error:
                    logger.warning(
                        f"Could not clean up archive file: {cleanup_error}"
        )
    
    def upload_file(
        self,
        file_path: Path,
        artifact_path: Optional[str] = None,
        skip_if_disabled: bool = True,
    ) -> bool:
        """
        Upload a single file to MLflow.
        
        Args:
            file_path: Path to file to upload.
            artifact_path: Optional artifact path within run's artifact directory.
                          If None, uses file name.
            skip_if_disabled: If True, skip upload when tracking is disabled.
        
        Returns:
            True if upload succeeded, False otherwise.
        """
        if not self._is_upload_enabled(skip_if_disabled):
            logger.debug(
                f"[ArtifactUploader] Upload disabled for stage={self._stage}, "
                f"skipping file upload"
            )
            return False
        
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False
        
        if artifact_path is None:
            artifact_path = file_path.name
        
        run_id = self._get_run_id()
        return log_artifact_safe(
            local_path=file_path,
            artifact_path=artifact_path,
            run_id=run_id,
        )
    
    def upload_checkpoint_archive(
        self,
        archive_path: Path,
        manifest: Optional[dict] = None,
        artifact_path: str = "best_trial_checkpoint.tar.gz",
        skip_if_disabled: bool = True,
    ) -> bool:
        """
        Upload a checkpoint archive and optional manifest to MLflow.
        
        .. deprecated:: 
            This method is primarily for internal use. For most cases, use
            `upload_checkpoint()` which automatically creates archives.
            This method is kept for edge cases where archives are pre-created externally.
        
        Args:
            archive_path: Path to checkpoint archive file.
            manifest: Optional manifest dictionary to upload as JSON.
            artifact_path: Artifact path within run's artifact directory.
            skip_if_disabled: If True, skip upload when tracking is disabled.
        
        Returns:
            True if upload succeeded, False otherwise.
        """
        if not self._is_upload_enabled(skip_if_disabled):
            logger.debug(
                f"[ArtifactUploader] Upload disabled for stage={self._stage}, "
                f"skipping checkpoint archive upload"
            )
            return False
        
        archive_path = Path(archive_path)
        if not archive_path.exists():
            logger.warning(f"Checkpoint archive does not exist: {archive_path}")
            return False
        
        run_id = self._get_run_id()
        return upload_checkpoint_archive(
            archive_path=archive_path,
            manifest=manifest,
            artifact_path=artifact_path,
            run_id=run_id,
        )

