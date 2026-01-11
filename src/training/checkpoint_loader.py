"""Compatibility shim for training.checkpoint_loader.

DEPRECATED: This module has been moved to training.core.checkpoint_loader.
This shim will be removed in a future release.
Please update your imports to use training.core.checkpoint_loader instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.checkpoint_loader' is deprecated. "
    "Please use 'training.core.checkpoint_loader' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.core.checkpoint_loader import *  # noqa: F403, F401

