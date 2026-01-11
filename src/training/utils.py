"""Compatibility shim for training.utils.

DEPRECATED: This module has been moved to training.core.utils.
This shim will be removed in a future release.
Please update your imports to use training.core.utils instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.utils' is deprecated. "
    "Please use 'training.core.utils' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.core.utils import *  # noqa: F403, F401

