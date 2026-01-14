from __future__ import annotations

"""MLflow run setup for local HPO.

This module provides backward compatibility by re-exporting from the new location.
"""

# Import from new location
from training.hpo.tracking.setup import (
    setup_hpo_mlflow_run,
    commit_run_name_version,
)

__all__ = [
    "setup_hpo_mlflow_run",
    "commit_run_name_version",
]






