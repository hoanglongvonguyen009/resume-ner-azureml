from __future__ import annotations

"""
@meta
name: tracking_mlflow_artifacts_stage_helpers
type: utility
domain: tracking
responsibility:
  - Stage-specific helper functions for common artifact upload patterns
  - Convenience wrappers around ArtifactUploader
inputs:
  - Stage-specific artifact paths
  - Optional run IDs and config directories
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

"""Stage-specific helper functions for artifact uploads."""
from pathlib import Path
from typing import Dict, Optional

from common.shared.logging_utils import get_logger

from infrastructure.tracking.mlflow.artifacts.uploader import ArtifactUploader

logger = get_logger(__name__)


def upload_training_artifacts(
    checkpoint_dir: Path,
    metrics_json_path: Optional[Path] = None,
    run_id: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Dict[str, bool]:
    """
    Upload training artifacts (checkpoint and metrics.json).
    
    The checkpoint is automatically archived as a compressed tar.gz file with
    manifest metadata. This provides compression benefits and consistent
    artifact structure across all stages.
    
    Args:
        checkpoint_dir: Path to checkpoint directory.
        metrics_json_path: Optional path to metrics.json file.
        run_id: Optional MLflow run ID. If None, will be detected automatically.
        config_dir: Optional path to config directory for tracking config.
    
    Returns:
        Dictionary with upload results: {"checkpoint": bool, "metrics_json": bool}
    """
    uploader = ArtifactUploader(
        run_id=run_id,
        stage="training",
        config_dir=config_dir,
    )
    
    results: Dict[str, bool] = {}
    
    # Upload checkpoint (automatically creates archive)
    results["checkpoint"] = uploader.upload_checkpoint(
        checkpoint_dir=checkpoint_dir,
        artifact_path="checkpoint.tar.gz",
    )
    
    # Upload metrics.json if provided
    if metrics_json_path:
        results["metrics_json"] = uploader.upload_file(
            file_path=metrics_json_path,
            artifact_path="metrics.json",
        )
    else:
        results["metrics_json"] = False
    
    return results


def upload_conversion_artifacts(
    onnx_path: Path,
    run_id: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> bool:
    """
    Upload conversion artifacts (ONNX model).
    
    Args:
        onnx_path: Path to ONNX model file.
        run_id: Optional MLflow run ID. If None, will be detected automatically.
        config_dir: Optional path to config directory for tracking config.
    
    Returns:
        True if upload succeeded, False otherwise.
    """
    uploader = ArtifactUploader(
        run_id=run_id,
        stage="conversion",
        config_dir=config_dir,
    )
    
    # Check stage-specific config
    config = uploader.get_tracking_config()
    if not config.get("log_onnx_model", True):
        logger.debug(
            "[Conversion] ONNX model logging disabled "
            "(tracking.conversion.log_onnx_model=false)"
        )
        return False
    
    return uploader.upload_file(
        file_path=onnx_path,
        artifact_path="onnx_model",
    )


def upload_benchmark_artifacts(
    benchmark_json_path: Optional[Path] = None,
    run_id: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Dict[str, bool]:
    """
    Upload benchmarking artifacts (benchmark results JSON).
    
    Args:
        benchmark_json_path: Optional path to benchmark results JSON file.
        run_id: Optional MLflow run ID. If None, will be detected automatically.
        config_dir: Optional path to config directory for tracking config.
    
    Returns:
        Dictionary with upload results: {"benchmark_json": bool}
    """
    uploader = ArtifactUploader(
        run_id=run_id,
        stage="benchmark",
        config_dir=config_dir,
    )
    
    results: Dict[str, bool] = {}
    
    # Check stage-specific config
    config = uploader.get_tracking_config()
    if not config.get("log_artifacts", True):
        logger.debug(
            "[Benchmark] Artifact logging disabled "
            "(tracking.benchmark.log_artifacts=false)"
        )
        results["benchmark_json"] = False
        return results
    
    # Upload benchmark JSON if provided
    if benchmark_json_path:
        results["benchmark_json"] = uploader.upload_file(
            file_path=benchmark_json_path,
            artifact_path="benchmark_results.json",
        )
    else:
        results["benchmark_json"] = False
    
    return results


def upload_hpo_artifacts(
    checkpoint_dir: Path,
    trial_number: int,
    run_id: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> bool:
    """
    Upload HPO artifacts (checkpoint archive and manifest).
    
    This function creates a checkpoint archive automatically and uploads it
    with manifest metadata. The archive is created from the checkpoint directory
    and includes trial number information.
    
    Args:
        checkpoint_dir: Path to checkpoint directory.
        trial_number: Trial number for manifest metadata.
        run_id: Optional MLflow run ID. If None, will be detected automatically.
        config_dir: Optional path to config directory for tracking config.
    
    Returns:
        True if upload succeeded, False otherwise.
    """
    uploader = ArtifactUploader(
        run_id=run_id,
        stage=None,  # HPO doesn't have a specific stage config
        config_dir=config_dir,
    )
    
    return uploader.upload_checkpoint(
        checkpoint_dir=checkpoint_dir,
        artifact_path="best_trial_checkpoint.tar.gz",
        trial_number=trial_number,
    )

