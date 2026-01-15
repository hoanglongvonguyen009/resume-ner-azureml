"""
@meta
name: naming_policy_reexport
type: utility
domain: naming
responsibility:
  - Re-export naming policy functions from infrastructure module
  - Maintain backward compatibility for orchestration imports
inputs:
  - None (re-export only)
outputs:
  - Re-exported functions
tags:
  - utility
  - naming
  - policy
  - compatibility
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: legacy
"""

"""Re-export naming policy functions from infrastructure module for backward compatibility.

DEPRECATED: This module is deprecated and will be removed in a future release.
Please import directly from infrastructure.naming.display_policy instead:

    from infrastructure.naming.display_policy import (
        format_run_name,
        load_naming_policy,
        parse_parent_training_id,
        sanitize_semantic_suffix,
        validate_naming_policy,
        validate_run_name,
    )
"""

import warnings
from infrastructure.naming.display_policy import (
    format_run_name,
    load_naming_policy,
    parse_parent_training_id,
    sanitize_semantic_suffix,
    validate_naming_policy,
    validate_run_name,
)

# Issue deprecation warning when module is imported
warnings.warn(
    "orchestration.jobs.tracking.naming.policy is deprecated. "
    "Please import from infrastructure.naming.display_policy instead. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "format_run_name",
    "load_naming_policy",
    "parse_parent_training_id",
    "sanitize_semantic_suffix",
    "validate_naming_policy",
    "validate_run_name",
]
