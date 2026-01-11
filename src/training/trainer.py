"""Compatibility shim for training.trainer.

DEPRECATED: This module has been moved to training.core.trainer.
This shim will be removed in a future release.
Please update your imports to use training.core.trainer instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.trainer' is deprecated. "
    "Please use 'training.core.trainer' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.core.trainer import *  # noqa: F403, F401

