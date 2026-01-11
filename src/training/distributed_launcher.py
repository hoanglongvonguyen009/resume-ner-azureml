"""Compatibility shim for training.distributed_launcher.

DEPRECATED: This module has been moved to training.execution.distributed_launcher.
This shim will be removed in a future release.
Please update your imports to use training.execution.distributed_launcher instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.distributed_launcher' is deprecated. "
    "Please use 'training.execution.distributed_launcher' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.execution.distributed_launcher import *  # noqa: F403, F401

