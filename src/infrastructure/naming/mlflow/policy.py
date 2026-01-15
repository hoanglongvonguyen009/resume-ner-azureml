from __future__ import annotations

"""
@meta
name: naming_mlflow_policy_compat
type: utility
domain: naming
responsibility:
  - Provide backward-compatible re-exports for naming policy helpers
  - Bridge legacy orchestration naming.policy module to infrastructure.naming
  - Does NOT introduce new business logic (delegates to display_policy)
inputs:
  - None (module-level compatibility only)
outputs:
  - Re-exported naming policy functions
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

"""Naming policy loader and formatter for run names.

This module provides backward compatibility by re-exporting from display_policy.
"""

from typing import Any, Dict, Optional

from core.normalize import normalize_for_name

# Re-export all the functions directly from display_policy (no circular dependency)
from ..display_policy import (
    extract_component,
    format_run_name,
    load_naming_policy,
    parse_parent_training_id,
    sanitize_semantic_suffix,
    validate_naming_policy,
    validate_run_name,
)

def normalize_value(value: str, rules: Optional[Dict[str, Any]] = None) -> str:
    """Apply normalization rules to a value (backward-compatible wrapper)."""
    return normalize_for_name(value, rules, return_warnings=False)

__all__ = [
    "load_naming_policy",
    "format_run_name",
    "validate_run_name",
    "parse_parent_training_id",
    "validate_naming_policy",
    "normalize_value",
    "sanitize_semantic_suffix",
    "extract_component",
]
