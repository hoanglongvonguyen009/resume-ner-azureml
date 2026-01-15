from __future__ import annotations

"""MLflow run finder with priority-based retrieval and strict mode.

This module re-exports finder functions from infrastructure (SSOT) for backward compatibility.
New code should import directly from infrastructure.tracking.mlflow.finder.*
"""

# Re-export for backward compatibility (from infrastructure SSOT)
from infrastructure.tracking.mlflow.finder import (
    find_mlflow_run,
    find_run_by_trial_id,
)

__all__ = [
    "find_mlflow_run",
    "find_run_by_trial_id",
]
