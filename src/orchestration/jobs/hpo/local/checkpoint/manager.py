"""
@meta
name: hpo_checkpoint_manager
type: utility
domain: hpo
responsibility:
  - Manage checkpoint storage paths for HPO studies
  - Resolve platform-specific checkpoint paths
inputs:
  - Checkpoint configuration
  - Output directories
outputs:
  - Resolved storage paths
tags:
  - utility
  - hpo
  - checkpoint
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Checkpoint manager for HPO study persistence.

This module is a thin re-export wrapper for backward compatibility.
All functions are imported from the SSOT: training.hpo.checkpoint.storage
"""

from training.hpo.checkpoint.storage import get_storage_uri, resolve_storage_path

__all__ = ["get_storage_uri", "resolve_storage_path"]
