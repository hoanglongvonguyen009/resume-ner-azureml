"""Training module for Resume NER model.

This module provides a unified interface for training operations, including:
- Core training logic (training.core.*)
- Hyperparameter optimization (training.hpo.*)
- Training execution infrastructure (training.execution.*)
- Command-line interfaces (training.cli.*)

For new code, prefer importing directly from submodules:
    from training.core import train_model
    from training.hpo import run_local_hpo_sweep
    from training.execution import run_final_training_workflow

The top-level imports are maintained for backward compatibility.
"""

from .config import build_training_config, resolve_distributed_config
# Import build_label_list separately since it doesn't require torch
from data.loaders import build_label_list

# Import from logging module (doesn't require torch)
from .logging import log_metrics

# Core training functions require torch, so they are imported lazily
# Lazy imports for functions that require torch or optional dependencies
# These will be imported on-demand to avoid requiring dependencies at module level

__all__ = [
    # Configuration
    "build_training_config",
    "resolve_distributed_config",
    # Data utilities (lazy)
    "load_dataset",
    "build_label_list",
    "ResumeNERDataset",
    "split_train_test",
    "save_split_files",
    # Core training
    "create_model_and_tokenizer",
    "train_model",
    "evaluate_model",
    "compute_metrics",
    "set_seed",
    "resolve_training_checkpoint_path",
    "validate_checkpoint",
    # Logging
    "log_metrics",
    # HPO (lazy)
    "run_local_hpo_sweep",
    "extract_best_config_from_study",
    "create_search_space",
    # Execution (lazy)
    "run_final_training_workflow",
    "execute_final_training",  # Backward compatibility alias
    "extract_lineage_from_best_model",
]


def __getattr__(name: str):
    """Lazy import for training functions that require torch or optional dependencies."""
    # Core training functions (require torch)
    if name == "train_model":
        from .core import train_model
        return train_model
    elif name == "create_model_and_tokenizer":
        from .core import create_model_and_tokenizer
        return create_model_and_tokenizer
    elif name == "evaluate_model":
        from .core import evaluate_model
        return evaluate_model
    elif name == "compute_metrics":
        from .core import compute_metrics
        return compute_metrics
    elif name == "set_seed":
        from .core import set_seed
        return set_seed
    elif name == "resolve_training_checkpoint_path":
        from .core import resolve_training_checkpoint_path
        return resolve_training_checkpoint_path
    elif name == "validate_checkpoint":
        from .core import validate_checkpoint
        return validate_checkpoint
    # Data utilities
    elif name == "load_dataset":
        from data.loaders import load_dataset
        return load_dataset
    elif name == "ResumeNERDataset":
        from data.loaders import ResumeNERDataset
        return ResumeNERDataset
    elif name == "split_train_test":
        from data.loaders import split_train_test
        return split_train_test
    elif name == "save_split_files":
        from data.loaders import save_split_files
        return save_split_files
    # HPO utilities (require optuna)
    elif name == "run_local_hpo_sweep":
        from .hpo import run_local_hpo_sweep
        return run_local_hpo_sweep
    elif name == "extract_best_config_from_study":
        from .hpo import extract_best_config_from_study
        return extract_best_config_from_study
    elif name == "create_search_space":
        from .hpo import create_search_space
        return create_search_space
    # Execution utilities
    elif name == "run_final_training_workflow":
        from .execution import run_final_training_workflow
        return run_final_training_workflow
    elif name == "execute_final_training":
        # Backward compatibility alias
        from .execution import run_final_training_workflow
        return run_final_training_workflow
    elif name == "extract_lineage_from_best_model":
        from .execution import extract_lineage_from_best_model
        return extract_lineage_from_best_model
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

