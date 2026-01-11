"""Compatibility shim for training.cv_utils.

DEPRECATED: This module has been moved to training.core.cv_utils.
This shim will be removed in a future release.
Please update your imports to use training.core.cv_utils instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.cv_utils' is deprecated. "
    "Please use 'training.core.cv_utils' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.core.cv_utils import *  # noqa: F403, F401

