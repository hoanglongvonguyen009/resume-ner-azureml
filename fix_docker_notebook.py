#!/usr/bin/env python3
"""
Script to clean up unused imports and variables from docker_testing.ipynb.

Removes:
- Unused imports: json, subprocess, pandas, IPython.display, ContainerError
- Unused model_finder imports: find_latest_onnx_model, find_matching_checkpoint, list_available_models
- Unused server_launcher imports: all of them
- Unused variables: SRC_DIR, CONFIG_DIR
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/docker_testing.ipynb")


def fix_cell_3_imports(source: str) -> str:
    """Remove unused imports from Cell 3."""
    lines = source.split("\n")
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Remove unused standard library imports
        if stripped == "import json":
            i += 1
            continue
        if stripped == "import subprocess":
            i += 1
            continue
        if stripped == "from IPython.display import display, Markdown, JSON":
            i += 1
            continue
        if stripped == "import pandas as pd":
            i += 1
            continue
        
        # Remove ContainerError from docker.errors import
        if stripped.startswith("from docker.errors import"):
            # Replace with version without ContainerError
            new_lines.append("from docker.errors import DockerException, ImageNotFound")
            i += 1
            continue
        
        # Fix model_finder imports - keep only find_model_pair
        if "from src.deployment.api.tools.model_finder import" in stripped:
            new_lines.append(line)  # Keep the import line
            i += 1
            # Process the multi-line import, keeping only find_model_pair
            while i < len(lines):
                current_line = lines[i]
                current_stripped = current_line.strip()
                if current_stripped == ")":
                    new_lines.append(current_line)  # Keep closing paren
                    i += 1
                    break
                elif "find_model_pair" in current_line:
                    new_lines.append(current_line)  # Keep find_model_pair
                i += 1
            continue
        
        # Remove entire server_launcher import block
        if "from src.deployment.api.tools.server_launcher import" in stripped:
            # Skip this entire import block
            i += 1
            while i < len(lines):
                if lines[i].strip() == ")":
                    i += 1  # Skip closing paren
                    break
                i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    return "\n".join(new_lines)


def fix_cell_4_variables(source: str) -> str:
    """Remove unused variables from Cell 4."""
    lines = source.split("\n")
    new_lines = []
    
    for line in lines:
        # Remove SRC_DIR and CONFIG_DIR definitions
        if "SRC_DIR = project_root / \"src\"" in line:
            continue
        if "CONFIG_DIR = project_root / \"config\"" in line:
            continue
        
        new_lines.append(line)
    
    return "\n".join(new_lines)


def main():
    """Main function to fix the notebook."""
    print(f"Loading notebook: {NOTEBOOK_PATH}")
    
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        notebook = json.load(f)
    
    # Cell 3 is at index 3 (0-indexed: 0=markdown, 1=markdown, 2=pip install, 3=imports)
    cell_3 = notebook["cells"][3]
    if cell_3["cell_type"] == "code":
        print("Fixing Cell 3 imports...")
        source = "".join(cell_3["source"])
        fixed_source = fix_cell_3_imports(source)
        cell_3["source"] = list(fixed_source.split("\n"))
        # Add newline back to each line except the last
        for i in range(len(cell_3["source"]) - 1):
            cell_3["source"][i] += "\n"
        print("✓ Cell 3 fixed")
    else:
        print(f"⚠ Cell 3 is not a code cell (type: {cell_3['cell_type']})")
    
    # Cell 4 is at index 4 (0-indexed)
    cell_4 = notebook["cells"][4]
    if cell_4["cell_type"] == "code":
        print("Fixing Cell 4 variables...")
        source = "".join(cell_4["source"])
        fixed_source = fix_cell_4_variables(source)
        cell_4["source"] = list(fixed_source.split("\n"))
        # Add newline back to each line except the last
        for i in range(len(cell_4["source"]) - 1):
            cell_4["source"][i] += "\n"
        print("✓ Cell 4 fixed")
    else:
        print(f"⚠ Cell 4 is not a code cell (type: {cell_4['cell_type']})")
    
    # Save the notebook
    print(f"Saving notebook: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print("✓ Notebook fixed successfully!")


if __name__ == "__main__":
    main()

