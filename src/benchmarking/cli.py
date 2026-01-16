#!/usr/bin/env python
"""
@meta
name: benchmarking_cli
type: script
domain: benchmarking
responsibility:
  - Compatibility wrapper for benchmarking CLI
  - Redirects to evaluation.benchmarking.cli
lifecycle:
  status: deprecated
tags:
  - entrypoint
  - compatibility
  - deprecated
"""

"""Compatibility wrapper for benchmarking CLI.

This script redirects to the new evaluation.benchmarking.cli module.
It's kept for backward compatibility when the CLI is called directly.

.. deprecated:: 
    This module is deprecated. Use :mod:`evaluation.benchmarking` instead.
"""

import sys
import warnings
from pathlib import Path

# Emit deprecation warning when module is imported
warnings.warn(
    "src.benchmarking is deprecated. Use src.evaluation.benchmarking instead.",
    DeprecationWarning,
    stacklevel=2
)

# Add src to path if not already there
_script_dir = Path(__file__).parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

# Import and run the actual CLI from the new location
if __name__ == "__main__":
    from evaluation.benchmarking.cli import main
    main()

