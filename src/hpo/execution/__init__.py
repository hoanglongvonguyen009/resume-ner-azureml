"""Compatibility shim for hpo.execution module.

DEPRECATED: This module has been moved to training.hpo.execution.
This shim will be removed in a future release.
Please update your imports to use training.hpo.execution instead.
"""

import warnings

warnings.warn(
    "Importing from 'hpo.execution' is deprecated. "
    "Please use 'training.hpo.execution' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.hpo.execution import *  # noqa: F403, F401
