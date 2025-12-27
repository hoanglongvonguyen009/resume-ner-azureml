"""Final cleanup of notebook - remove deprecated code and unused variables."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

cells_modified = 0

# Clean up cells
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    
    source = cell['source']
    if isinstance(source, str):
        source = source.split('\n')
    
    original_source = source.copy()
    new_source = []
    skip_next = False
    
    for j, line in enumerate(source):
        # Skip lines that are part of a multi-line comment block
        if skip_next:
            skip_next = False
            continue
        
        # Remove deprecated variable definitions that are no longer used
        # Keep BEST_CONFIG_CACHE_FILE and FINAL_TRAINING_CACHE_FILE for backward compatibility
        # But we can remove them if they're only used in legacy fallback code
        
        # Remove empty comment-only lines
        if line.strip() == "#" or line.strip().startswith("# ") and len(line.strip()) < 5:
            continue
        
        new_source.append(line)
    
    # Only update if changed
    if new_source != original_source:
        cell['source'] = new_source
        cells_modified += 1
        print(f"  Cleaned cell {i}")

# Remove any cells that are entirely empty or just whitespace
empty_cells = []
for i, cell in enumerate(notebook['cells']):
    source_text = "".join(cell['source'])
    if not source_text.strip():
        empty_cells.append(i)

if empty_cells:
    for i in sorted(empty_cells, reverse=True):
        print(f"  Removing empty cell {i}")
        del notebook['cells'][i]

if cells_modified > 0 or empty_cells:
    # Create backup
    backup_path = notebook_path.with_suffix('.ipynb.backup_final')
    print(f"Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    # Write updated notebook
    print(f"Writing cleaned notebook: {notebook_path}")
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"\n[OK] Modified {cells_modified} cell(s)")
    if empty_cells:
        print(f"[OK] Removed {len(empty_cells)} empty cell(s)")
else:
    print("No cleanup needed")

print(f"\nFinal cell count: {len(notebook['cells'])}")

