from __future__ import annotations

"""
@meta
name: artifact_unified_validation
type: utility
domain: selection
responsibility:
  - Artifact-kind-specific validation
  - Validate checkpoints, metadata, configs, logs, and metrics
  - Check essential files for each artifact kind
inputs:
  - Artifact kind
  - Artifact paths
outputs:
  - Validation results (is_valid, error_message)
tags:
  - utility
  - selection
  - artifacts
  - validation
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Artifact-kind-specific validation.

This module provides validation functions for different artifact kinds.
Each artifact kind has its own validation requirements.
"""
from pathlib import Path
from typing import List, Optional

from common.shared.logging_utils import get_logger
from evaluation.selection.artifact_unified.types import ArtifactKind, AvailabilityStatus

logger = get_logger(__name__)


def validate_artifact(
    artifact_kind: ArtifactKind,
    path: Path,
    strict: bool = True,
) -> tuple[bool, Optional[str]]:
    """
    Validate artifact based on its kind.
    
    Args:
        artifact_kind: Type of artifact to validate
        path: Path to artifact
        strict: If True, require all essential files. If False, be lenient.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if artifact_kind == ArtifactKind.CHECKPOINT:
        return _validate_checkpoint(path, strict)
    elif artifact_kind == ArtifactKind.METADATA:
        return _validate_metadata(path, strict)
    elif artifact_kind == ArtifactKind.CONFIG:
        return _validate_config(path, strict)
    elif artifact_kind == ArtifactKind.LOGS:
        return _validate_logs(path, strict)
    elif artifact_kind == ArtifactKind.METRICS:
        return _validate_metrics(path, strict)
    else:
        # All enum values are covered above, but mypy needs explicit else for exhaustiveness
        return False, f"Unknown artifact kind: {artifact_kind}"  # type: ignore[unreachable]


def _validate_checkpoint(path: Path, strict: bool) -> tuple[bool, Optional[str]]:
    """
    Validate checkpoint integrity by checking for essential files.
    
    Required files (strict mode):
    - config.json (always required)
    - At least one model file: pytorch_model.bin, model.safetensors, model.bin, or pytorch_model.bin.index.json
    
    Lenient mode:
    - Only requires config.json
    
    Args:
        path: Path to checkpoint directory
        strict: If True, require model files. If False, only require config.json.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"Checkpoint path does not exist: {path}"
    
    if not path.is_dir():
        return False, f"Checkpoint path is not a directory: {path}"
    
    # Check for config.json (always required)
    config_file = path / "config.json"
    if not config_file.exists():
        return False, f"Checkpoint missing config.json: {path}"
    
    if not strict:
        return True, None
    
    # Strict mode: require at least one model file
    model_files = [
        "pytorch_model.bin",
        "model.safetensors",
        "model.bin",
        "pytorch_model.bin.index.json",
    ]
    
    has_model_file = any((path / fname).exists() for fname in model_files)
    
    if not has_model_file:
        return False, (
            f"Checkpoint missing model files (strict mode). "
            f"Expected one of: {', '.join(model_files)}"
        )
    
    return True, None


def _validate_metadata(path: Path, strict: bool) -> tuple[bool, Optional[str]]:
    """
    Validate metadata file (JSON).
    
    Args:
        path: Path to metadata file or directory
        strict: If True, require valid JSON. If False, only check existence.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"Metadata path does not exist: {path}"
    
    # If directory, look for common metadata file names
    if path.is_dir():
        metadata_files = [
            path / "trial_meta.json",
            path / "metadata.json",
            path / "run_metadata.json",
        ]
        metadata_file = next((f for f in metadata_files if f.exists()), None)
        if not metadata_file:
            return False, f"Metadata directory has no metadata file: {path}"
        path = metadata_file
    
    if not path.is_file():
        return False, f"Metadata path is not a file: {path}"
    
    if strict:
        # Validate JSON structure
        try:
            import json
            with open(path, "r") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Metadata file is not valid JSON: {e}"
        except Exception as e:
            return False, f"Error reading metadata file: {e}"
    
    return True, None


def _validate_config(path: Path, strict: bool) -> tuple[bool, Optional[str]]:
    """
    Validate config file (JSON or YAML).
    
    Args:
        path: Path to config file
        strict: If True, require valid JSON/YAML. If False, only check existence.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"Config path does not exist: {path}"
    
    if not path.is_file():
        return False, f"Config path is not a file: {path}"
    
    if strict:
        # Validate JSON or YAML structure
        try:
            if path.suffix in [".json", ".jsonl"]:
                import json
                with open(path, "r") as f:
                    json.load(f)
            elif path.suffix in [".yaml", ".yml"]:
                from common.shared.yaml_utils import load_yaml
                load_yaml(path)
            else:
                # Unknown format - assume valid if file exists
                pass
        except Exception as e:
            return False, f"Config file is not valid: {e}"
    
    return True, None


def _validate_logs(path: Path, strict: bool) -> tuple[bool, Optional[str]]:
    """
    Validate logs (directory or file).
    
    Args:
        path: Path to logs directory or file
        strict: If True, require non-empty. If False, only check existence.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"Logs path does not exist: {path}"
    
    if strict:
        if path.is_dir():
            # Check if directory has any files
            if not any(path.iterdir()):
                return False, f"Logs directory is empty: {path}"
        elif path.is_file():
            # Check if file is non-empty
            if path.stat().st_size == 0:
                return False, f"Logs file is empty: {path}"
    
    return True, None


def _validate_metrics(path: Path, strict: bool) -> tuple[bool, Optional[str]]:
    """
    Validate metrics file (JSON).
    
    Args:
        path: Path to metrics file
        strict: If True, require valid JSON with metrics. If False, only check existence.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"Metrics path does not exist: {path}"
    
    if not path.is_file():
        return False, f"Metrics path is not a file: {path}"
    
    if strict:
        # Validate JSON structure
        try:
            import json
            with open(path, "r") as f:
                data = json.load(f)
            # Check if it looks like metrics (has numeric values)
            if not isinstance(data, dict):
                return False, "Metrics file is not a JSON object"
        except json.JSONDecodeError as e:
            return False, f"Metrics file is not valid JSON: {e}"
        except Exception as e:
            return False, f"Error reading metrics file: {e}"
    
    return True, None


def get_required_files(artifact_kind: ArtifactKind) -> List[str]:
    """
    Get list of required files for an artifact kind.
    
    Args:
        artifact_kind: Type of artifact
        
    Returns:
        List of required file names (relative paths)
    """
    if artifact_kind == ArtifactKind.CHECKPOINT:
        return ["config.json", "pytorch_model.bin"]  # At least one model file
    elif artifact_kind == ArtifactKind.METADATA:
        return ["trial_meta.json"]  # Or metadata.json, run_metadata.json
    elif artifact_kind == ArtifactKind.CONFIG:
        return ["config.json"]  # Or config.yaml
    elif artifact_kind == ArtifactKind.LOGS:
        return []  # Any files
    elif artifact_kind == ArtifactKind.METRICS:
        return ["metrics.json"]  # Or similar
    else:
        # All enum values are covered above, but mypy needs explicit else for exhaustiveness
        return []  # type: ignore[unreachable]

