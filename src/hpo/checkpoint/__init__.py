"""Compatibility shim for hpo.checkpoint module.

DEPRECATED: This module has been moved to training.hpo.checkpoint.
This shim will be removed in a future release.
Please update your imports to use training.hpo.checkpoint instead.
"""

import warnings

warnings.warn(
    "Importing from 'hpo.checkpoint' is deprecated. "
    "Please use 'training.hpo.checkpoint' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.hpo.checkpoint import *  # noqa: F403, F401
