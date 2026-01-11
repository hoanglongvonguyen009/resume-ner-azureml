"""Compatibility shim for training.metrics.

DEPRECATED: This module has been moved to training.core.metrics.
This shim will be removed in a future release.
Please update your imports to use training.core.metrics instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.metrics' is deprecated. "
    "Please use 'training.core.metrics' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.core.metrics import *  # noqa: F403, F401

