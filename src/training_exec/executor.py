"""Compatibility shim for training_exec.executor.

DEPRECATED: This module has been moved to training.execution.executor.
This shim will be removed in a future release.
Please update your imports to use training.execution.executor instead.
"""

import warnings

warnings.warn(
    "Importing from 'training_exec.executor' is deprecated. "
    "Please use 'training.execution.executor' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.execution.executor import *  # noqa: F403, F401

