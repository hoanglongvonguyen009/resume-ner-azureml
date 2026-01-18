"""
@meta
name: model_finder
type: utility
domain: deployment
responsibility:
  - Find ONNX models in outputs directory
  - Find matching checkpoints for ONNX models
  - List available models and checkpoints
inputs:
  - outputs directory path
outputs:
  - Paths to ONNX models and checkpoints
tags:
  - utility
  - api
  - model-discovery
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Utilities for finding ONNX models and checkpoints in outputs directory."""

import re
from pathlib import Path
from typing import Optional

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)

# Pattern for spec hash: spec-{8 hex chars}_exec-{8 hex chars}
SPEC_HASH_PATTERN = re.compile(r"spec-([a-f0-9]{8})_exec-([a-f0-9]{8})")


def extract_spec_hash(path: Path) -> Optional[str]:
    """
    Extract spec hash from path.
    
    Args:
        path: Path containing spec hash (e.g., .../spec-1e6acb58_exec-02136b6b/...)
    
    Returns:
        Spec hash string (e.g., "spec-1e6acb58_exec-02136b6b") or None if not found
    """
    path_str = str(path)
    match = SPEC_HASH_PATTERN.search(path_str)
    if match:
        return f"spec-{match.group(1)}_exec-{match.group(2)}"
    return None


def find_latest_onnx_model(outputs_dir: Path) -> Optional[Path]:
    """
    Find the latest ONNX model in outputs/conversion directory.
    
    Args:
        outputs_dir: Root outputs directory (e.g., Path("outputs"))
    
    Returns:
        Path to latest ONNX model file, or None if not found
    """
    conversion_dir = outputs_dir / "conversion"
    if not conversion_dir.exists():
        logger.warning(f"Conversion directory does not exist: {conversion_dir}")
        return None
    
    # Find all ONNX model files
    onnx_files = list(conversion_dir.rglob("model.onnx"))
    if not onnx_files:
        logger.warning(f"No ONNX models found in {conversion_dir}")
        return None
    
    # Sort by modification time (newest first)
    onnx_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    latest_model = onnx_files[0]
    logger.info(f"Found latest ONNX model: {latest_model}")
    return latest_model


def find_matching_checkpoint(onnx_path: Path, outputs_dir: Path) -> Optional[Path]:
    """
    Find checkpoint matching ONNX model's spec hash.
    
    Args:
        onnx_path: Path to ONNX model file
        outputs_dir: Root outputs directory (e.g., Path("outputs"))
    
    Returns:
        Path to matching checkpoint directory, or None if not found
    """
    spec_hash = extract_spec_hash(onnx_path)
    if not spec_hash:
        logger.warning(f"Could not extract spec hash from ONNX path: {onnx_path}")
        return None
    
    # Search for checkpoint with matching spec hash
    final_training_dir = outputs_dir / "final_training"
    if not final_training_dir.exists():
        logger.warning(f"Final training directory does not exist: {final_training_dir}")
        return None
    
    # Find all checkpoint directories
    checkpoint_dirs = list(final_training_dir.rglob("checkpoint"))
    if not checkpoint_dirs:
        logger.warning(f"No checkpoints found in {final_training_dir}")
        return None
    
    # Find checkpoint with matching spec hash
    for checkpoint_dir in checkpoint_dirs:
        checkpoint_path_str = str(checkpoint_dir)
        if spec_hash in checkpoint_path_str:
            logger.info(f"Found matching checkpoint: {checkpoint_dir}")
            return checkpoint_dir
    
    logger.warning(f"No checkpoint found matching spec hash: {spec_hash}")
    return None


def find_model_pair(outputs_dir: Path) -> tuple[Optional[Path], Optional[Path]]:
    """
    Find matching ONNX and checkpoint pair.
    
    Args:
        outputs_dir: Root outputs directory (e.g., Path("outputs"))
    
    Returns:
        Tuple of (onnx_path, checkpoint_path), either may be None if not found
    """
    onnx_path = find_latest_onnx_model(outputs_dir)
    if not onnx_path:
        return None, None
    
    checkpoint_path = find_matching_checkpoint(onnx_path, outputs_dir)
    return onnx_path, checkpoint_path


def list_available_models(outputs_dir: Path) -> dict[str, list[Path]]:
    """
    List all available models and checkpoints.
    
    Args:
        outputs_dir: Root outputs directory (e.g., Path("outputs"))
    
    Returns:
        Dictionary with keys "onnx_models" and "checkpoints", each containing list of Paths
    """
    result: dict[str, list[Path]] = {
        "onnx_models": [],
        "checkpoints": [],
    }
    
    # Find all ONNX models
    conversion_dir = outputs_dir / "conversion"
    if conversion_dir.exists():
        onnx_files = list(conversion_dir.rglob("model.onnx"))
        result["onnx_models"] = sorted(onnx_files, key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Find all checkpoints
    final_training_dir = outputs_dir / "final_training"
    if final_training_dir.exists():
        checkpoint_dirs = list(final_training_dir.rglob("checkpoint"))
        result["checkpoints"] = sorted(checkpoint_dirs, key=lambda p: p.stat().st_mtime, reverse=True)
    
    return result

