#!/usr/bin/env python3
"""Script to validate notebook hpo_studies dictionary storage.

This script checks that the notebook correctly stores all backbone studies
in the hpo_studies dictionary, preventing the indentation bug.

Usage:
    python tests/scripts/validate_notebook_hpo_studies.py
    python tests/scripts/validate_notebook_hpo_studies.py --notebook notebooks/01_orchestrate_training_colab.ipynb
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from tests.shared.validate_hpo_studies import check_notebook_indentation


def main():
    parser = argparse.ArgumentParser(
        description="Validate notebook hpo_studies dictionary storage"
    )
    parser.add_argument(
        "--notebook",
        type=Path,
        default=ROOT_DIR / "notebooks" / "01_orchestrate_training_colab.ipynb",
        help="Path to notebook file (default: notebooks/01_orchestrate_training_colab.ipynb)",
    )
    
    args = parser.parse_args()
    
    notebook_path = args.notebook
    if not notebook_path.exists():
        print(f"Error: Notebook not found at {notebook_path}", file=sys.stderr)
        sys.exit(1)
    
    is_correct, error_message = check_notebook_indentation(notebook_path)
    
    if is_correct:
        print(f"OK: Notebook indentation is correct: {notebook_path}")
        sys.exit(0)
    else:
        print(f"ERROR: {error_message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

