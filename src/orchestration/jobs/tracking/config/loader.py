from __future__ import annotations

"""MLflow configuration loader for systematic naming settings.

**DEPRECATED**: This module is maintained for backward compatibility only.
All functions are re-exported from `infrastructure.naming.mlflow.config` (SSOT).

**Migration**: Update imports to use `infrastructure.naming.mlflow.config` directly:
    - `from infrastructure.naming.mlflow.config import get_naming_config`
    - `from infrastructure.naming.mlflow.config import get_index_config`
    - `from infrastructure.naming.mlflow.config import get_auto_increment_config`
    - `from infrastructure.naming.mlflow.config import get_tracking_config`
    - `from infrastructure.naming.mlflow.config import get_run_finder_config`
    - `from infrastructure.naming.mlflow.config import load_mlflow_config`

This module will be removed in a future version.
"""

import warnings
from pathlib import Path
from typing import Any, Dict, Optional

# Import SSOT functions from infrastructure
from infrastructure.naming.mlflow.config import (
    get_auto_increment_config as _get_auto_increment_config,
    get_index_config as _get_index_config,
    get_naming_config as _get_naming_config,
    get_run_finder_config as _get_run_finder_config,
    get_tracking_config as _get_tracking_config,
    load_mlflow_config as _load_mlflow_config,
)

__all__ = [
    "get_naming_config",
    "get_index_config",
    "get_auto_increment_config",
    "get_tracking_config",
    "get_run_finder_config",
    "load_mlflow_config",
]


def get_naming_config(
    config_dir: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get naming configuration with defaults (deprecated wrapper)."""
    warnings.warn(
        "orchestration.jobs.tracking.config.loader.get_naming_config is deprecated. "
        "Use infrastructure.naming.mlflow.config.get_naming_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_naming_config(config_dir=config_dir, config=config)


def get_index_config(
    config_dir: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get index configuration with defaults (deprecated wrapper)."""
    warnings.warn(
        "orchestration.jobs.tracking.config.loader.get_index_config is deprecated. "
        "Use infrastructure.naming.mlflow.config.get_index_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_index_config(config_dir=config_dir, config=config)


def get_auto_increment_config(
    config_dir: Optional[Path] = None,
    process_type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get auto-increment configuration with defaults (deprecated wrapper)."""
    warnings.warn(
        "orchestration.jobs.tracking.config.loader.get_auto_increment_config is deprecated. "
        "Use infrastructure.naming.mlflow.config.get_auto_increment_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_auto_increment_config(
        config_dir=config_dir, process_type=process_type, config=config
    )


def get_tracking_config(
    config_dir: Optional[Path] = None,
    stage: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get tracking configuration for a specific stage (deprecated wrapper)."""
    warnings.warn(
        "orchestration.jobs.tracking.config.loader.get_tracking_config is deprecated. "
        "Use infrastructure.naming.mlflow.config.get_tracking_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_tracking_config(config_dir=config_dir, stage=stage, config=config)


def get_run_finder_config(
    config_dir: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get run finder configuration with defaults (deprecated wrapper)."""
    warnings.warn(
        "orchestration.jobs.tracking.config.loader.get_run_finder_config is deprecated. "
        "Use infrastructure.naming.mlflow.config.get_run_finder_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_run_finder_config(config_dir=config_dir, config=config)


def load_mlflow_config(config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load MLflow configuration from file (deprecated wrapper)."""
    warnings.warn(
        "orchestration.jobs.tracking.config.loader.load_mlflow_config is deprecated. "
        "Use infrastructure.naming.mlflow.config.load_mlflow_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _load_mlflow_config(config_dir=config_dir)

