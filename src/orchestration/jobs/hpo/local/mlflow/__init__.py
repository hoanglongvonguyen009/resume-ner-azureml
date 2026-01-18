from __future__ import annotations

"""MLflow integration for local HPO.

**Note**: This module is deprecated. Import directly from the source modules:
- `training.hpo.tracking.setup` for `setup_hpo_mlflow_run` and `commit_run_name_version`
- `training.hpo.tracking.cleanup` for `cleanup_interrupted_runs`
"""

# Re-export from source modules for backward compatibility
from training.hpo.tracking.setup import setup_hpo_mlflow_run, commit_run_name_version
from training.hpo.tracking.cleanup import cleanup_interrupted_runs

__all__ = [
    "setup_hpo_mlflow_run",
    "commit_run_name_version",
    "cleanup_interrupted_runs",
]
