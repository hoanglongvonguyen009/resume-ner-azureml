from __future__ import annotations

"""MLflow configuration loader for systematic naming settings.

This module re-exports configuration functions for backward compatibility.
New code should import directly from orchestration.jobs.tracking.config.*
"""

# Import load_mlflow_config from SSOT
from infrastructure.naming.mlflow.config import load_mlflow_config

# Re-export other configuration functions for backward compatibility
from orchestration.jobs.tracking.config.loader import (
    get_naming_config,
    get_index_config,
    get_run_finder_config,
    get_auto_increment_config,
)

__all__ = [
    "load_mlflow_config",
    "get_naming_config",
    "get_index_config",
    "get_run_finder_config",
    "get_auto_increment_config",
]
