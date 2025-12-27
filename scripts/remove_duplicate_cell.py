"""Remove duplicate/corrupted cell from notebook."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find and remove corrupted cells
cells_to_remove = []
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        # Check for corrupted pattern (duplicate load_cache_file calls)
        if source_text.count("from orchestration.paths import load_cache_file") > 1:
            # Check if it's the corrupted one (has malformed code)
            if "if previous_training is None:\n    ROOT_DIR" in source_text:
                cells_to_remove.append(i)
                print(f"  Found corrupted cell at index {i}")

# Remove cells in reverse order to maintain indices
for i in reversed(cells_to_remove):
    print(f"  Removing cell {i}")
    del notebook['cells'][i]

if cells_to_remove:
    # Create backup
    backup_path = notebook_path.with_suffix('.ipynb.backup3')
    print(f"Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    # Write updated notebook
    print(f"Writing updated notebook: {notebook_path}")
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"[OK] Removed {len(cells_to_remove)} corrupted cell(s)")
else:
    print("No corrupted cells found")

