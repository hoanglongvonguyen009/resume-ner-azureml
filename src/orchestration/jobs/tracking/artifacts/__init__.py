from __future__ import annotations

"""MLflow artifact management utilities.

This module re-exports artifact functions from infrastructure (SSOT) for backward compatibility.
New code should import directly from infrastructure.tracking.mlflow.artifacts.manager.*
"""

# Re-export all artifact functions from infrastructure (SSOT) for backward compatibility
from infrastructure.tracking.mlflow.artifacts.manager import (
    create_checkpoint_archive,
    should_skip_file,
)

__all__ = [
    "create_checkpoint_archive",
    "should_skip_file",
]
