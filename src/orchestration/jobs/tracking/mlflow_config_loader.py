from __future__ import annotations

"""MLflow configuration loader for systematic naming settings.

**DEPRECATED**: This module is maintained for backward compatibility only.
All functions are re-exported from `infrastructure.naming.mlflow.config` (SSOT).

**Migration**: Update imports to use `infrastructure.naming.mlflow.config` directly:
    - `from infrastructure.naming.mlflow.config import get_naming_config`
    - `from infrastructure.naming.mlflow.config import get_index_config`
    - `from infrastructure.naming.mlflow.config import get_auto_increment_config`
    - `from infrastructure.naming.mlflow.config import load_mlflow_config`

This module will be removed in a future version.
"""

import warnings

# Import all functions from SSOT (infrastructure)
from infrastructure.naming.mlflow.config import (
    get_auto_increment_config,
    get_index_config,
    get_naming_config,
    load_mlflow_config,
)

__all__ = [
    "load_mlflow_config",
    "get_naming_config",
    "get_index_config",
    "get_run_finder_config",
    "get_auto_increment_config",
]

# Re-export get_run_finder_config for backward compatibility
# (not in original exports but may be used)
from infrastructure.naming.mlflow.config import get_run_finder_config

# Issue deprecation warning when module is imported
warnings.warn(
    "orchestration.jobs.tracking.mlflow_config_loader is deprecated. "
    "Use infrastructure.naming.mlflow.config instead.",
    DeprecationWarning,
    stacklevel=2,
)
