"""Compatibility shim for training.distributed.

DEPRECATED: This module has been moved to training.execution.distributed.
This shim will be removed in a future release.
Please update your imports to use training.execution.distributed instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.distributed' is deprecated. "
    "Please use 'training.execution.distributed' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.execution.distributed import *  # noqa: F403, F401

