"""Compatibility shim for training.model.

DEPRECATED: This module has been moved to training.core.model.
This shim will be removed in a future release.
Please update your imports to use training.core.model instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.model' is deprecated. "
    "Please use 'training.core.model' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.core.model import *  # noqa: F403, F401

