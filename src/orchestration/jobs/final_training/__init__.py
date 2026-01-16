from __future__ import annotations

"""Final training job modules - backward compatibility facade.

This module re-exports from training.execution module for backward compatibility.
"""

import warnings

# Re-export from new location
from training.execution.executor import execute_final_training
from training.execution.lineage import extract_lineage_from_best_model
from training.execution.tags import apply_lineage_tags

# Issue deprecation warning
warnings.warn(
    "Importing from 'orchestration.jobs.final_training' is deprecated. "
    "Please import from 'training.execution' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "extract_lineage_from_best_model",
    "apply_lineage_tags",
    "execute_final_training",
]

