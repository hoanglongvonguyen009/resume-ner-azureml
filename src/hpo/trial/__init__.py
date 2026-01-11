"""Compatibility shim for hpo.trial module.

DEPRECATED: This module has been moved to training.hpo.trial.
This shim will be removed in a future release.
Please update your imports to use training.hpo.trial instead.
"""

import warnings

warnings.warn(
    "Importing from 'hpo.trial' is deprecated. "
    "Please use 'training.hpo.trial' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.hpo.trial import *  # noqa: F403, F401
