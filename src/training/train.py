"""Compatibility shim for training.train.

DEPRECATED: This module has been moved to training.cli.train.
This shim will be removed in a future release.
Please update your imports to use training.cli.train instead.
"""

import warnings

warnings.warn(
    "Importing from 'training.train' is deprecated. "
    "Please use 'training.cli.train' instead. "
    "This shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from training.cli.train import *  # noqa: F403, F401

# Support running as module: python -m training.train
if __name__ == "__main__":
    from training.cli.train import main
    main()

