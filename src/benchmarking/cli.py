#!/usr/bin/env python
"""Compatibility wrapper for benchmarking CLI.

This script redirects to the new evaluation.benchmarking.cli module.
It's kept for backward compatibility when the CLI is called directly.
"""

import sys
from pathlib import Path

# Add src to path if not already there
_script_dir = Path(__file__).parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

# Import and run the actual CLI from the new location
if __name__ == "__main__":
    from evaluation.benchmarking.cli import main
    main()

