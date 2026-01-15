"""
@meta
name: hpo_checkpoint_cleanup
type: utility
domain: hpo
responsibility:
  - Checkpoint cleanup utilities for HPO trials
  - Manage checkpoint lifecycle: tracking, best trial detection, cleanup
inputs:
  - HPO output directories
  - HPO configuration
  - Trial information
outputs:
  - Cleaned checkpoint directories
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

"""Checkpoint cleanup utilities for HPO trials.

This module is a thin re-export wrapper for backward compatibility.
All classes are imported from the SSOT: training.hpo.checkpoint.cleanup
"""

from training.hpo.checkpoint.cleanup import CheckpointCleanupManager

__all__ = ["CheckpointCleanupManager"]
