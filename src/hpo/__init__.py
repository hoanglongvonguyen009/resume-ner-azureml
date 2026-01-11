"""Compatibility shim for hpo module.

DEPRECATED: This module has been moved to training.hpo.
This shim will be removed in a future release.
Please update your imports to use training.hpo instead.
"""

import warnings

warnings.warn(
    "Importing from 'hpo' is deprecated. "
    "Please use 'training.hpo' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.hpo import *  # noqa: F403, F401
