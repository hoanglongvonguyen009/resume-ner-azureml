"""Core training logic module.

This module contains the core training logic including:
- Model training (trainer.py)
- Model definitions (model.py)
- Metrics computation (metrics.py)
- Model evaluation (evaluator.py)
- Checkpoint loading (checkpoint_loader.py)
- Cross-validation utilities (cv_utils.py)
- Training utilities (utils.py)
"""

from typing import Any

# Import non-torch dependencies first (can be imported eagerly)
from .cv_utils import create_kfold_splits, load_fold_splits, get_fold_data

# Torch-dependent modules are imported lazily via __getattr__
# This allows importing core module without requiring torch

__all__ = [
    "train_model",
    "create_model_and_tokenizer",
    "compute_metrics",
    "evaluate_model",
    "validate_checkpoint",
    "resolve_training_checkpoint_path",
    "create_kfold_splits",
    "load_fold_splits",
    "get_fold_data",
    "set_seed",
]


def __getattr__(name: str) -> Any:
    """Lazy import for torch-dependent modules."""
    if name == "train_model":
        from .trainer import train_model
        return train_model
    elif name == "create_model_and_tokenizer":
        from .model import create_model_and_tokenizer
        return create_model_and_tokenizer
    elif name == "compute_metrics":
        from .metrics import compute_metrics
        return compute_metrics
    elif name == "evaluate_model":
        from .evaluator import evaluate_model
        return evaluate_model
    elif name == "validate_checkpoint":
        from .checkpoint_loader import validate_checkpoint
        return validate_checkpoint
    elif name == "resolve_training_checkpoint_path":
        from .checkpoint_loader import resolve_training_checkpoint_path
        return resolve_training_checkpoint_path
    elif name == "set_seed":
        from .utils import set_seed
        return set_seed
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

