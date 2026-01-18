"""Path resolution utilities for benchmarking."""

from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.logging_utils import get_logger
from infrastructure.naming import create_naming_context
from infrastructure.paths import (
    build_output_path,
    resolve_output_path_for_colab,
    validate_path_before_mkdir,
)

logger = get_logger(__name__)

# Constants
DEFAULT_BENCHMARK_FILENAME = "benchmark.json"


def extract_trial_id(trial_info: Dict[str, Any]) -> str:
    """
    Extract trial ID from trial_info.
    
    Args:
        trial_info: Trial info dictionary
        
    Returns:
        Trial ID string
    """
    # Try multiple fields for trial_id
    trial_id = (
        trial_info.get("trial_id") or
        trial_info.get("trial_name") or
        trial_info.get("trial_number") or
        "unknown"
    )
    return str(trial_id)


def build_benchmark_output_path(
    trial_info: Dict[str, Any],
    backbone: str,
    root_dir: Path,
    environment: str,
    benchmark_config: Optional[Dict[str, Any]],
    data_config: Optional[Dict[str, Any]],
    hpo_config: Optional[Dict[str, Any]],
) -> Path:
    """
    Build benchmark output path for a trial.
    
    Args:
        trial_info: Trial info dictionary
        backbone: Backbone name
        root_dir: Root directory of the project
        environment: Platform environment
        benchmark_config: Optional benchmark configuration
        data_config: Optional data configuration
        hpo_config: Optional HPO configuration
        
    Returns:
        Path to benchmark output file
    """
    from infrastructure.naming.utils import extract_short_backbone_name
    
    backbone_name = extract_short_backbone_name(backbone)
    trial_id = extract_trial_id(trial_info)
    study_key_hash = trial_info.get("study_key_hash")
    trial_key_hash = trial_info.get("trial_key_hash")
    
    # Compute benchmark_config_hash if benchmark_config is available
    benchmark_config_hash = None
    if benchmark_config:
        try:
            from common.shared.hash_utils import compute_json_hash
            benchmark_config_hash = compute_json_hash(benchmark_config, length=64)
        except Exception as e:
            logger.debug(f"Could not compute benchmark_config_hash: {e}")
    
    # Build benchmarking output path with hashes
    benchmarking_context = create_naming_context(
        process_type="benchmarking",
        model=backbone_name,
        trial_id=trial_id,
        environment=environment,
        study_key_hash=study_key_hash,
        trial_key_hash=trial_key_hash,
        benchmark_config_hash=benchmark_config_hash,
    )
    benchmarking_path = build_output_path(root_dir, benchmarking_context)
    # Redirect to Drive on Colab for persistence (similar to checkpoints)
    benchmarking_path = resolve_output_path_for_colab(benchmarking_path)
    # Validate path before creating directory
    benchmarking_path = validate_path_before_mkdir(
        benchmarking_path, context="benchmarking directory"
    )
    benchmarking_path.mkdir(parents=True, exist_ok=True)
    
    # Get output filename from config, with fallback to default
    output_filename = DEFAULT_BENCHMARK_FILENAME
    if benchmark_config and "output" in benchmark_config:
        output_filename = benchmark_config["output"].get("filename", DEFAULT_BENCHMARK_FILENAME)
    
    return benchmarking_path / output_filename

