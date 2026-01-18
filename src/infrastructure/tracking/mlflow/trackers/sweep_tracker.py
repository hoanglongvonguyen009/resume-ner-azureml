"""
@meta
name: tracking_mlflow_sweep_tracker
type: utility
domain: tracking
responsibility:
  - Track MLflow runs for HPO sweep stage
  - Manage sweep and trial run lifecycle
inputs:
  - Sweep configurations
  - Run names and contexts
outputs:
  - MLflow run handles
tags:
  - utility
  - tracking
  - mlflow
  - tracker
  - hpo
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow tracker for sweep stage.

This module has been refactored into focused submodules:
- sweep_tracker.config: Parameter Objects (TypedDicts)
- sweep_tracker.run_creation: Run creation logic
- sweep_tracker.tagging: Tagging logic
- sweep_tracker.metrics: Metric logging logic
- sweep_tracker.checkpoint_logger: Checkpoint logging
- sweep_tracker.trial_finder: Trial finding utilities

This file maintains backward compatibility by re-exporting all public APIs.
"""

# Re-export from refactored module for backward compatibility
from infrastructure.tracking.mlflow.trackers.sweep_tracker.sweep_tracker import (
    MLflowSweepTracker,
)

__all__ = [
    "MLflowSweepTracker",
]
