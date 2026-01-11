"""Compatibility shim for training_exec.tags.

DEPRECATED: This module has been moved to training.execution.tags.
This shim will be removed in a future release.
Please update your imports to use training.execution.tags instead.
"""

import warnings

warnings.warn(
    "Importing from 'training_exec.tags' is deprecated. "
    "Please use 'training.execution.tags' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.execution.tags import *  # noqa: F403, F401
