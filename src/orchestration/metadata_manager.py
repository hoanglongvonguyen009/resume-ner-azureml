"""Manage persistent metadata for training and conversion stages."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from orchestration.paths import resolve_output_path
from shared.json_cache import load_json, save_json


def get_metadata_file_path(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> Path:
    """
    Get path to metadata file for a training name.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory (root_dir / "config").
        training_name: Stable training name (e.g., "distilbert_trial_0").
    
    Returns:
        Path to metadata file.
    """
    cache_dir = resolve_output_path(
        root_dir, config_dir, "cache", subcategory="final_training"
    )
    return cache_dir / f"{training_name}_metadata.json"


def load_training_metadata(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> Optional[Dict[str, Any]]:
    """
    Load metadata for a training name.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
    
    Returns:
        Metadata dictionary or None if not found.
    """
    metadata_file = get_metadata_file_path(root_dir, config_dir, training_name)
    return load_json(metadata_file, default=None)


def save_training_metadata(
    root_dir: Path,
    config_dir: Path,
    training_name: str,
    backbone: str,
    trial_name: str,
    trial_id: str,
    best_config_timestamp: str,
    status_updates: Dict[str, Any]
) -> Path:
    """
    Save or update training metadata.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
        backbone: Model backbone name.
        trial_name: Trial name from best configuration.
        trial_id: Trial ID from best configuration.
        best_config_timestamp: Timestamp when best config was selected.
        status_updates: Dictionary of status updates by stage:
            {
                "training": {"completed": True, "checkpoint_path": "...", ...},
                "benchmarking": {"completed": True, ...},
                "conversion": {"completed": True, "onnx_model_path": "...", ...}
            }
    
    Returns:
        Path to saved metadata file.
    """
    metadata_file = get_metadata_file_path(root_dir, config_dir, training_name)
    
    # Load existing metadata or create new
    metadata = load_json(metadata_file, default={})
    
    # Update base info
    metadata.update({
        "training_name": training_name,
        "backbone": backbone,
        "trial_name": trial_name,
        "trial_id": trial_id,
        "best_config_timestamp": best_config_timestamp,
        "last_updated": datetime.now().isoformat(),
    })
    
    # Update status
    if "status" not in metadata:
        metadata["status"] = {}
    
    for stage, updates in status_updates.items():
        if stage not in metadata["status"]:
            metadata["status"][stage] = {}
        metadata["status"][stage].update(updates)
        
        # Add timestamps for completion and artifact upload
        if "completed" in updates and updates["completed"]:
            metadata["status"][stage]["completed_at"] = datetime.now().isoformat()
        if "artifacts_uploaded" in updates and updates.get("artifacts_uploaded"):
            metadata["status"][stage]["artifacts_uploaded_at"] = datetime.now().isoformat()
    
    save_json(metadata_file, metadata)
    return metadata_file


def is_training_complete(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> bool:
    """
    Check if training has been completed.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
    
    Returns:
        True if training is marked as complete, False otherwise.
    """
    metadata = load_training_metadata(root_dir, config_dir, training_name)
    if not metadata:
        return False
    return metadata.get("status", {}).get("training", {}).get("completed", False)


def are_training_artifacts_uploaded(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> bool:
    """
    Check if training artifacts have been uploaded.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
    
    Returns:
        True if artifacts are marked as uploaded, False otherwise.
    """
    metadata = load_training_metadata(root_dir, config_dir, training_name)
    if not metadata:
        return False
    return metadata.get("status", {}).get("training", {}).get("artifacts_uploaded", False)


def is_benchmarking_complete(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> bool:
    """
    Check if benchmarking has been completed.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
    
    Returns:
        True if benchmarking is marked as complete, False otherwise.
    """
    metadata = load_training_metadata(root_dir, config_dir, training_name)
    if not metadata:
        return False
    return metadata.get("status", {}).get("benchmarking", {}).get("completed", False)


def is_conversion_complete(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> bool:
    """
    Check if model conversion has been completed.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
    
    Returns:
        True if conversion is marked as complete, False otherwise.
    """
    metadata = load_training_metadata(root_dir, config_dir, training_name)
    if not metadata:
        return False
    return metadata.get("status", {}).get("conversion", {}).get("completed", False)


def are_conversion_artifacts_uploaded(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> bool:
    """
    Check if conversion artifacts have been uploaded.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
    
    Returns:
        True if artifacts are marked as uploaded, False otherwise.
    """
    metadata = load_training_metadata(root_dir, config_dir, training_name)
    if not metadata:
        return False
    return metadata.get("status", {}).get("conversion", {}).get("artifacts_uploaded", False)


def get_training_checkpoint_path(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> Optional[Path]:
    """
    Get checkpoint path from metadata.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
    
    Returns:
        Path to checkpoint directory or None if not found.
    """
    metadata = load_training_metadata(root_dir, config_dir, training_name)
    if not metadata:
        return None
    
    checkpoint_path_str = metadata.get("status", {}).get("training", {}).get("checkpoint_path")
    if checkpoint_path_str:
        return Path(checkpoint_path_str)
    return None


def get_conversion_onnx_path(
    root_dir: Path,
    config_dir: Path,
    training_name: str
) -> Optional[Path]:
    """
    Get ONNX model path from metadata.
    
    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        training_name: Stable training name.
    
    Returns:
        Path to ONNX model file or None if not found.
    """
    metadata = load_training_metadata(root_dir, config_dir, training_name)
    if not metadata:
        return None
    
    onnx_path_str = metadata.get("status", {}).get("conversion", {}).get("onnx_model_path")
    if onnx_path_str:
        return Path(onnx_path_str)
    return None

