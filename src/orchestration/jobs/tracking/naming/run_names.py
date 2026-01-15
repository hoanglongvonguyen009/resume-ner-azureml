"""
@meta
name: naming_mlflow_run_names_reexport
type: utility
domain: naming
responsibility:
  - Re-export build_mlflow_run_name from infrastructure module
  - Maintain backward compatibility for orchestration imports
inputs:
  - None (re-export only)
outputs:
  - Re-exported function
tags:
  - utility
  - naming
  - mlflow
  - compatibility
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: legacy
"""

"""Re-export build_mlflow_run_name from infrastructure module for backward compatibility.

DEPRECATED: This module is deprecated and will be removed in a future release.
Please import directly from infrastructure.naming.mlflow.run_names instead:

    from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
"""

import warnings
from infrastructure.naming.mlflow.run_names import (
    build_mlflow_run_name,
)

# Issue deprecation warning when module is imported
warnings.warn(
    "orchestration.jobs.tracking.naming.run_names is deprecated. "
    "Please import from infrastructure.naming.mlflow.run_names instead. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "build_mlflow_run_name",
]
