"""Compatibility shim for training.evaluator.

DEPRECATED: This module has been moved to training.core.evaluator.
This shim will be removed in a future release.
Please update your imports to use training.core.evaluator instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.evaluator' is deprecated. "
    "Please use 'training.core.evaluator' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.core.evaluator import *  # noqa: F403, F401

