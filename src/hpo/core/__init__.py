"""Compatibility shim for hpo.core module.

DEPRECATED: This module has been moved to training.hpo.core.
This shim will be removed in a future release.
Please update your imports to use training.hpo.core instead.
"""

import warnings

warnings.warn(
    "Importing from 'hpo.core' is deprecated. "
    "Please use 'training.hpo.core' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.hpo.core import *  # noqa: F403, F401
