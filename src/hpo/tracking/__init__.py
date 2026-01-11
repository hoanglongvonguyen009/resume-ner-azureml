"""Compatibility shim for hpo.tracking module.

DEPRECATED: This module has been moved to training.hpo.tracking.
This shim will be removed in a future release.
Please update your imports to use training.hpo.tracking instead.
"""

import warnings

warnings.warn(
    "Importing from 'hpo.tracking' is deprecated. "
    "Please use 'training.hpo.tracking' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.hpo.tracking import *  # noqa: F403, F401
