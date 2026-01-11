"""Compatibility shim for training_exec module.

DEPRECATED: This module has been moved to training.execution.
This shim will be removed in a future release.
Please update your imports to use training.execution instead.
"""

import warnings

warnings.warn(
    "Importing from 'training_exec' is deprecated. "
    "Please use 'training.execution' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.execution import *  # noqa: F403, F401
