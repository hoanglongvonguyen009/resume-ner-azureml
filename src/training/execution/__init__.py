"""Training execution infrastructure.

This module provides utilities for executing training as subprocesses.
"""

from .mlflow_setup import (
    create_training_mlflow_run,
    setup_mlflow_tracking_env,
)
from .subprocess_runner import (
    FoldConfig,
    MLflowConfig,
    TrialConfig,
    TrainingOptions,
    build_training_command,
    execute_training_subprocess,
    setup_training_environment,
    verify_training_environment,
)
# Import non-optional dependencies
from .lineage import extract_lineage_from_best_model
from .tags import apply_lineage_tags

# Jobs and distributed imports require optional dependencies (azure, torch)
# These will be imported lazily via __getattr__

__all__ = [
    "build_training_command",
    "setup_training_environment",
    "execute_training_subprocess",
    "verify_training_environment",
    "create_training_mlflow_run",
    "setup_mlflow_tracking_env",
    "TrainingOptions",
    "MLflowConfig",
    "FoldConfig",
    "TrialConfig",
    "RunContext",
    "create_run_context",
    "detect_hardware",
    "should_use_ddp",
    "init_process_group_if_needed",
    "execute_final_training",
    "extract_lineage_from_best_model",
    "apply_lineage_tags",
]


def __getattr__(name: str):
    """Lazy import for executor, distributed, and jobs modules to avoid circular dependency and optional dependency requirements."""
    if name == "execute_final_training":
        from .executor import execute_final_training
        return execute_final_training
    # Distributed imports require torch
    elif name == "RunContext":
        from .distributed import RunContext
        return RunContext
    elif name == "create_run_context":
        from .distributed import create_run_context
        return create_run_context
    elif name == "detect_hardware":
        from .distributed import detect_hardware
        return detect_hardware
    elif name == "should_use_ddp":
        from .distributed import should_use_ddp
        return should_use_ddp
    elif name == "init_process_group_if_needed":
        from .distributed import init_process_group_if_needed
        return init_process_group_if_needed
    # Jobs imports require azure
    elif name == "build_final_training_config":
        from .jobs import build_final_training_config
        return build_final_training_config
    elif name == "validate_final_training_job":
        from .jobs import validate_final_training_job
        return validate_final_training_job
    elif name == "create_final_training_job":
        from .jobs import create_final_training_job
        return create_final_training_job
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

