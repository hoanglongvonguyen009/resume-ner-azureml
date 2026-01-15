from __future__ import annotations

"""
@meta
name: naming_mlflow_policy_compat
type: utility
domain: naming
responsibility:
  - Provide backward-compatible re-exports for naming policy helpers
  - Bridge legacy orchestration naming.policy module to infrastructure.naming
  - Does NOT introduce new business logic (delegates to orchestration module)
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

This module provides backward compatibility by re-exporting from the old location.
"""

from typing import Any, Dict, Optional

from core.normalize import normalize_for_name

# Lazy import to avoid circular import issues during module initialization
_policy_module = None

def _get_policy_module():
    """Lazy import of the policy module."""
    global _policy_module
    if _policy_module is None:
        import orchestration.jobs.tracking.naming.policy as _policy_module
    return _policy_module

# Re-export all the functions with lazy loading
def load_naming_policy(*args, **kwargs):
    return _get_policy_module().load_naming_policy(*args, **kwargs)

def format_run_name(*args, **kwargs):
    return _get_policy_module().format_run_name(*args, **kwargs)

def validate_run_name(*args, **kwargs):
    return _get_policy_module().validate_run_name(*args, **kwargs)

def parse_parent_training_id(*args, **kwargs):
    return _get_policy_module().parse_parent_training_id(*args, **kwargs)

def validate_naming_policy(*args, **kwargs):
    return _get_policy_module().validate_naming_policy(*args, **kwargs)

def normalize_value(value: str, rules: Optional[Dict[str, Any]] = None) -> str:
    """Apply normalization rules to a value (backward-compatible wrapper)."""
    return normalize_for_name(value, rules, return_warnings=False)

def sanitize_semantic_suffix(*args, **kwargs):
    return _get_policy_module().sanitize_semantic_suffix(*args, **kwargs)

def extract_component(*args, **kwargs):
    return _get_policy_module().extract_component(*args, **kwargs)

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
