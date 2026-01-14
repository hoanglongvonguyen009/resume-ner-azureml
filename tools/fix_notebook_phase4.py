#!/usr/bin/env python3
"""
Fix notebook cells to use extracted Phase 4 functions.

This script updates notebooks to use the extracted notebook_setup functions
instead of inline environment detection and path setup logic.
"""

import json
from pathlib import Path


def fix_cell_11(notebook_path: Path) -> None:
    """Fix cell 11 (environment detection) in 01_orchestrate_training_colab.ipynb."""
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Find cell 11 (index 11, which is the 12th cell, 0-indexed)
    # Looking for the cell with environment detection code
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            # Check if this is the duplicate environment detection cell
            if "# Environment detection and platform configuration" in source:
                if "IN_COLAB = \"COLAB_GPU\"" in source:
                    # Replace with extracted function
                    new_source = """# Environment detection and platform configuration
# This cell can be run independently to re-detect environment
# Useful if environment variables change during notebook execution

from common.shared.notebook_setup import detect_notebook_environment

# Re-detect environment (useful if env vars change)
env = detect_notebook_environment()
PLATFORM = env.platform
IN_COLAB = env.is_colab
IN_KAGGLE = env.is_kaggle
IS_LOCAL = env.is_local
BASE_DIR = env.base_dir
BACKUP_ENABLED = env.backup_enabled

print(f"✓ Detected environment: {PLATFORM.upper()}")
print(f"Platform: {PLATFORM}")
"""
                    nb["cells"][i]["source"] = new_source.splitlines(keepends=True)
                    print(f"✓ Fixed cell {i} (environment detection)")
                    break

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)


def fix_cell_12(notebook_path: Path) -> None:
    """Fix cell 12 (path setup) in 01_orchestrate_training_colab.ipynb."""
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Find cell 12 with path setup code
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            # Check if this is the duplicate path setup cell
            if "# Setup paths (ROOT_DIR should be set in Cell 2)" in source:
                if "if 'ROOT_DIR' not in globals():" in source:
                    # Replace with extracted function
                    new_source = """# Setup paths (ROOT_DIR should be set in Cell 6)
# This cell can be run independently to re-setup paths
# Useful if paths need to be refreshed

from common.shared.notebook_setup import setup_notebook_paths

# Re-setup paths (useful if paths need to be refreshed)
if not IS_LOCAL and BASE_DIR:
    ROOT_DIR = BASE_DIR / "resume-ner-azureml"
    paths = setup_notebook_paths(root_dir=ROOT_DIR, add_src_to_path=True)
else:
    paths = setup_notebook_paths(add_src_to_path=True)

ROOT_DIR = paths.root_dir
CONFIG_DIR = paths.config_dir
SRC_DIR = paths.src_dir
NOTEBOOK_DIR = ROOT_DIR / "notebooks"

print("Notebook directory:", NOTEBOOK_DIR)
print("Project root:", ROOT_DIR)
print("Source directory:", SRC_DIR)
print("Config directory:", CONFIG_DIR)
print("Platform:", PLATFORM)
print("In Colab:", IN_COLAB)
print("In Kaggle:", IN_KAGGLE)
"""
                    nb["cells"][i]["source"] = new_source.splitlines(keepends=True)
                    print(f"✓ Fixed cell {i} (path setup)")
                    break

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)


def main() -> None:
    """Fix all notebooks for Phase 4."""
    repo_root = Path(__file__).parent.parent
    notebook_path = repo_root / "notebooks" / "01_orchestrate_training_colab.ipynb"

    if not notebook_path.exists():
        print(f"Error: Notebook not found at {notebook_path}")
        return

    print(f"Fixing {notebook_path.name}...")
    fix_cell_11(notebook_path)
    fix_cell_12(notebook_path)
    print("✓ All fixes applied")


if __name__ == "__main__":
    main()

