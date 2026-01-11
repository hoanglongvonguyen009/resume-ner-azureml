"""Compatibility shim for hpo.utils module.

DEPRECATED: This module has been moved to training.hpo.utils.
This shim will be removed in a future release.
Please update your imports to use training.hpo.utils instead.
"""

import warnings

warnings.warn(
    "Importing from 'hpo.utils' is deprecated. "
    "Please use 'training.hpo.utils' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.hpo.utils import *  # noqa: F403, F401

