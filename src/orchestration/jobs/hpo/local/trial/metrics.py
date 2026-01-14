from __future__ import annotations

"""Trial metrics utilities for local HPO.

This module provides backward compatibility by re-exporting from the new location.
"""

# Use lazy imports to avoid circular import issues
# Import the module first, then assign attributes
import training.hpo.trial.metrics as _metrics_module

# Re-export functions
read_trial_metrics = _metrics_module.read_trial_metrics
store_metrics_in_trial_attributes = _metrics_module.store_metrics_in_trial_attributes
parse_metrics_file = getattr(_metrics_module, 'parse_metrics_file', None)

__all__ = [
    "read_trial_metrics",
    "store_metrics_in_trial_attributes",
    "parse_metrics_file",
]

