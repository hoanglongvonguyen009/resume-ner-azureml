"""Compatibility shim for training_exec.lineage.

DEPRECATED: This module has been moved to training.execution.lineage.
This shim will be removed in a future release.
Please update your imports to use training.execution.lineage instead.
"""

import warnings

warnings.warn(
    "Importing from 'training_exec.lineage' is deprecated. "
    "Please use 'training.execution.lineage' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.execution.lineage import *  # noqa: F403, F401

