"""Clean up notebook by removing duplicate, corrupted, and deprecated cells."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

cells_to_remove = []
cells_to_fix = []

# Analyze all cells
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    
    source_text = "".join(cell['source'])
    
    # Check for corrupted cells (malformed code)
    if "if previous_training is None:\n    ROOT_DIR, CONFIG_DIR" in source_text:
        print(f"  Found corrupted cell at index {i}")
        cells_to_remove.append(i)
        continue
    
    # Check for duplicate continued training cells
    if "CONTINUED_EXPERIMENT_ENABLED" in source_text:
        # Count how many times this pattern appears
        count = source_text.count("if CONTINUED_EXPERIMENT_ENABLED:")
        if count > 1:
            print(f"  Found duplicate CONTINUED_EXPERIMENT_ENABLED in cell {i}")
            # Keep the first one, mark others for removal
            # We'll keep the one that's properly formatted
            if "previous_training = load_cache_file(" in source_text and source_text.count("from orchestration.paths import load_cache_file") == 1:
                # This is the good one, keep it
                pass
            else:
                cells_to_remove.append(i)
    
    # Check for cells that are entirely commented out (deprecated)
    lines = cell['source']
    if isinstance(lines, str):
        lines = lines.split('\n')
    
    non_comment_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    if len(non_comment_lines) == 0 and len(lines) > 5:
        # Entirely commented out cell with substantial content - likely deprecated
        print(f"  Found deprecated commented-out cell at index {i} ({len(lines)} lines)")
        cells_to_remove.append(i)
    
    # Check for cells with duplicate imports/code
    if source_text.count("from orchestration.paths import load_cache_file") > 1:
        # Check if it's the corrupted one
        if "if previous_training is None:\n    ROOT_DIR" in source_text:
            print(f"  Found cell with duplicate imports and corrupted code at index {i}")
            cells_to_remove.append(i)

# Remove cells in reverse order to maintain indices
for i in sorted(set(cells_to_remove), reverse=True):
    print(f"  Removing cell {i}")
    del notebook['cells'][i]

# Fix any remaining issues in continued training cells
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    
    source_text = "".join(cell['source'])
    
    # Fix cells that have the proper structure but might have minor issues
    if "CONTINUED_EXPERIMENT_ENABLED" in source_text and "from orchestration.paths import load_cache_file" in source_text:
        # Check if it's properly indented
        lines = cell['source']
        if isinstance(lines, str):
            lines = lines.split('\n')
        
        # Check if the import is inside the if block (should be)
        import_line_idx = None
        for j, line in enumerate(lines):
            if "from orchestration.paths import load_cache_file" in line:
                import_line_idx = j
                break
        
        if import_line_idx is not None:
            # Check if it's properly indented (should be inside if block)
            import_line = lines[import_line_idx]
            if not import_line.strip().startswith("    "):  # Should be indented
                # Fix indentation
                print(f"  Fixing indentation in cell {i}")
                new_lines = []
                in_if_block = False
                for j, line in enumerate(lines):
                    if "if CONTINUED_EXPERIMENT_ENABLED:" in line:
                        in_if_block = True
                        new_lines.append(line)
                    elif "from orchestration.paths import load_cache_file" in line and in_if_block:
                        new_lines.append("    " + line.strip())
                    else:
                        new_lines.append(line)
                cell['source'] = new_lines

if cells_to_remove:
    # Create backup
    backup_path = notebook_path.with_suffix('.ipynb.backup_cleanup')
    print(f"Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    # Write updated notebook
    print(f"Writing cleaned notebook: {notebook_path}")
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"\n[OK] Removed {len(set(cells_to_remove))} cell(s)")
    print(f"[OK] Backup saved to: {backup_path}")
else:
    print("No cells needed removal")

# Also check for and remove empty markdown cells or cells with just whitespace
empty_cells = []
for i, cell in enumerate(notebook['cells']):
    source_text = "".join(cell['source'])
    if not source_text.strip():
        empty_cells.append(i)

if empty_cells:
    print(f"\nFound {len(empty_cells)} empty cells")
    for i in sorted(empty_cells, reverse=True):
        print(f"  Removing empty cell {i}")
        del notebook['cells'][i]
    
    # Write again
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    print(f"[OK] Removed {len(empty_cells)} empty cell(s)")

print(f"\nFinal cell count: {len(notebook['cells'])}")

