"""Utility functions for selection workflows."""

from pathlib import Path
from typing import Optional, Dict, Any
import json

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def resolve_test_data_path(
    benchmark_config: Dict[str, Any],
    data_config: Dict[str, Any],
    config_dir: Path,
) -> Optional[Path]:
    """
    Resolve test data path from configs with fallbacks.
    
    Priority:
    1. benchmark_config["benchmarking"]["test_data"] (explicit)
    2. data_config["local_path"] / "test.json" or "validation.json"
    3. config_dir / "dataset" / "test.json" or "validation.json"
    
    Args:
        benchmark_config: Benchmark configuration dict
        data_config: Data configuration dict
        config_dir: Config directory path
        
    Returns:
        Path to test data file if found, None otherwise
    """
    # Priority 1: Explicit test_data in benchmark config
    if benchmark_config.get("benchmarking", {}).get("test_data"):
        test_data_path = Path(benchmark_config["benchmarking"]["test_data"])
        if not test_data_path.is_absolute():
            test_data_path = config_dir / test_data_path
        if test_data_path.exists():
            logger.debug(f"Found test data at explicit path: {test_data_path}")
            return test_data_path
    
    # Priority 2: data_config local_path
    if data_config.get("local_path"):
        local_path_str = data_config.get("local_path", "../dataset")
        dataset_path = (config_dir / local_path_str).resolve()
        
        # Handle seed subdirectory for dataset_tiny
        seed = data_config.get("seed")
        if seed is not None and "dataset_tiny" in str(dataset_path):
            dataset_path = dataset_path / f"seed{seed}"
        
        # Try test.json or validation.json
        for candidate in ["test.json", "validation.json"]:
            candidate_path = dataset_path / candidate
            if candidate_path.exists():
                logger.debug(f"Found test data at data config path: {candidate_path}")
                return candidate_path
    
    # Priority 3: Common locations relative to config
    for candidate in ["test.json", "validation.json"]:
        candidate_path = config_dir / "dataset" / candidate
        if candidate_path.exists():
            logger.debug(f"Found test data at common path: {candidate_path}")
            return candidate_path
    
    logger.warning("Test data not found in any expected location")
    return None


def validate_checkpoint_for_reuse(
    checkpoint_path: Path,
    expected_refit_run_id: Optional[str] = None,
) -> bool:
    """
    Validate checkpoint integrity before reuse.
    
    Args:
        checkpoint_path: Path to checkpoint directory
        expected_refit_run_id: Optional refit run_id to verify against metadata
        
    Returns:
        True if checkpoint is valid for reuse
    """
    if not checkpoint_path.exists():
        logger.debug(f"Checkpoint path does not exist: {checkpoint_path}")
        return False
    
    # Check for essential checkpoint files
    has_model = any(
        (checkpoint_path / f).exists()
        for f in ["pytorch_model.bin", "model.safetensors", "model.bin"]
    )
    has_config = (checkpoint_path / "config.json").exists()
    
    if not (has_model and has_config):
        logger.debug(f"Checkpoint missing essential files: {checkpoint_path}")
        return False
    
    # Optional: Verify refit_run_id in metadata if available
    if expected_refit_run_id:
        metadata_file = checkpoint_path / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                metadata_refit_id = metadata.get("refit_run_id")
                if metadata_refit_id and metadata_refit_id != expected_refit_run_id:
                    logger.debug(
                        f"Checkpoint metadata refit_run_id mismatch: "
                        f"expected={expected_refit_run_id[:12]}..., "
                        f"found={metadata_refit_id[:12]}..."
                    )
                    return False
            except Exception as e:
                # If metadata parsing fails, still allow reuse if files exist
                logger.debug(f"Could not parse checkpoint metadata: {e}")
    
    return True


