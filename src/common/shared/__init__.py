"""Shared utilities used across orchestration and training runtime."""

from .file_utils import verify_output_file, get_file_mtime
from .dict_utils import deep_merge
from .logging_utils import get_logger, get_script_logger
from .argument_parsing import (
    add_config_dir_argument,
    add_backbone_argument,
    add_training_hyperparameter_arguments,
    add_training_data_arguments,
    add_cross_validation_arguments,
    add_api_server_arguments,
    validate_config_dir,
)
from .tokenization_utils import (
    prepare_onnx_inputs,
    get_offset_mapping,
    prepare_onnx_inputs_with_offsets,
)
from .platform_detection import detect_platform, resolve_platform_checkpoint_path
from .mlflow_setup import (
    setup_mlflow_cross_platform,
    setup_mlflow_from_config,
    create_ml_client_from_config,
)
from .hash_utils import (
    compute_hash_64,
    compute_hash_16,
    compute_json_hash,
    compute_selection_cache_key,
)

__all__ = [
    "verify_output_file",
    "get_file_mtime",
    "deep_merge",
    "get_logger",
    "get_script_logger",
    "add_config_dir_argument",
    "add_backbone_argument",
    "add_training_hyperparameter_arguments",
    "add_training_data_arguments",
    "add_cross_validation_arguments",
    "add_api_server_arguments",
    "validate_config_dir",
    "prepare_onnx_inputs",
    "get_offset_mapping",
    "prepare_onnx_inputs_with_offsets",
    "detect_platform",
    "resolve_platform_checkpoint_path",
    "setup_mlflow_cross_platform",
    "setup_mlflow_from_config",
    "create_ml_client_from_config",
    "compute_hash_64",
    "compute_hash_16",
    "compute_json_hash",
    "compute_selection_cache_key",
]

