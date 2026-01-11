"""Compatibility shim for training_exec.jobs.

DEPRECATED: This module has been moved to training.execution.jobs.
This shim will be removed in a future release.
Please update your imports to use training.execution.jobs instead.
"""

import warnings

warnings.warn(
    "Importing from 'training_exec.jobs' is deprecated. "
    "Please use 'training.execution.jobs' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.execution.jobs import *  # noqa: F403, F401

