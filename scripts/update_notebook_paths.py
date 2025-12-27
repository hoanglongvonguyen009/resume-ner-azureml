"""Script to update notebook cells to use centralized path configuration."""

import json
import sys
from pathlib import Path


def update_best_config_saving_cell(cell_source):
    """Update the cell that saves best configuration cache."""
    if "save_json(BEST_CONFIG_CACHE_FILE, best_configuration)" not in "".join(cell_source):
        return None
    
    new_source = """from orchestration.paths import (
    resolve_output_path,
    save_cache_with_dual_strategy,
)
from datetime import datetime

# Use centralized path resolution
BEST_CONFIG_CACHE_DIR = resolve_output_path(
    ROOT_DIR,
    CONFIG_DIR,
    "cache",
    subcategory="best_configurations"
)

# Generate timestamp and identifiers
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backbone = best_configuration.get('backbone', 'unknown')
trial_name = best_configuration.get('trial_name', 'unknown')

# Save using dual file strategy
timestamped_file, latest_file, index_file = save_cache_with_dual_strategy(
    root_dir=ROOT_DIR,
    config_dir=CONFIG_DIR,
    cache_type="best_configurations",
    data=best_configuration,
    backbone=backbone,
    identifier=trial_name,
    timestamp=timestamp,
    additional_metadata={
        "experiment_name": experiment_config.name if 'experiment_config' in locals() else "unknown",
        "hpo_study_name": hpo_config.get('study_name', 'unknown') if 'hpo_config' in locals() else "unknown",
    }
)

# Also save to legacy location for backward compatibility
LEGACY_CACHE_FILE = ROOT_DIR / "notebooks" / "best_configuration_cache.json"
save_json(LEGACY_CACHE_FILE, best_configuration)

print(f"Best configuration selected:")
print(f"  Backbone: {backbone}")
print(f"  Trial: {trial_name}")
print(f"  Best {hpo_config['objective']['metric']}: {best_configuration.get('selection_criteria', {}).get('best_value'):.4f}")

# Show selection reasoning (if available)
selection_criteria = best_configuration.get('selection_criteria', {})
if 'reason' in selection_criteria:
    print(f"  Selection reason: {selection_criteria['reason']}")
if 'accuracy_diff_from_best' in selection_criteria:
    print(f"  Accuracy difference from best: {selection_criteria['accuracy_diff_from_best']:.4f}")

# Show all candidates (if available)
if 'all_candidates' in selection_criteria:
    print(f"\\nAll candidates considered:")
    for c in selection_criteria['all_candidates']:
        marker = "✓" if c['backbone'] == backbone else " "
        print(f"  {marker} {c['backbone']}: acc={c['accuracy']:.4f}, speed={c['speed_score']:.2f}x")

print(f"\\n✓ Saved timestamped cache: {timestamped_file}")
print(f"✓ Updated latest cache: {latest_file}")
print(f"✓ Updated index: {index_file}")
print(f"✓ Saved legacy cache (backward compatibility): {LEGACY_CACHE_FILE}")
print(f"\\n  Cache directory: {BEST_CONFIG_CACHE_DIR}")
"""
    return new_source.split('\n')


def update_best_config_loading_cell(cell_source):
    """Update the cell that loads best configuration cache."""
    source_text = "".join(cell_source)
    if "best_configuration = load_json(BEST_CONFIG_CACHE_FILE" not in source_text:
        return None
    
    new_source = """from orchestration.paths import load_cache_file

# Try loading from centralized cache first
best_configuration = load_cache_file(
    ROOT_DIR, CONFIG_DIR, "best_configurations", use_latest=True
)

# Fallback to legacy location
if best_configuration is None:
    LEGACY_CACHE_FILE = ROOT_DIR / "notebooks" / "best_configuration_cache.json"
    best_configuration = load_json(LEGACY_CACHE_FILE, default=None)

if best_configuration is None:
    raise FileNotFoundError(
        f"Best configuration cache not found.\\n"
        f"Please run Step P1-3.6: Best Configuration Selection first.\\n"
        f"Cache directory: {resolve_output_path(ROOT_DIR, CONFIG_DIR, 'cache', subcategory='best_configurations')}"
    )
"""
    return new_source.split('\n')


def update_final_training_saving_cell(cell_source):
    """Update the cell that saves final training cache."""
    source_text = "".join(cell_source)
    if "save_json(FINAL_TRAINING_CACHE_FILE" not in source_text or "Save cache file with actual paths" not in source_text:
        return None
    
    # Find the save_json call and replace the section
    new_source = """from orchestration.paths import (
    resolve_output_path,
    save_cache_with_dual_strategy,
)
from datetime import datetime

# Prepare cache data
final_training_cache_data = {
    "output_dir": str(final_output_dir),
    "backbone": final_training_config["backbone"],
    "run_id": final_training_run_id,
    "config": final_training_config,
    "metrics": metrics,  # Include metrics if available
}

# Save using dual file strategy
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backbone = final_training_config["backbone"].replace('-', '_').replace('/', '_')
run_id = final_training_run_id.replace('-', '_')

timestamped_file, latest_file, index_file = save_cache_with_dual_strategy(
    root_dir=ROOT_DIR,
    config_dir=CONFIG_DIR,
    cache_type="final_training",
    data=final_training_cache_data,
    backbone=backbone,
    identifier=run_id,
    timestamp=timestamp,
    additional_metadata={
        "checkpoint_path": str(checkpoint_source) if checkpoint_source else None,
    }
)

# Also save to legacy location for backward compatibility
LEGACY_CACHE_FILE = ROOT_DIR / "notebooks" / "final_training_cache.json"
save_json(LEGACY_CACHE_FILE, final_training_cache_data)

print(f"✓ Saved timestamped final training cache: {timestamped_file}")
print(f"✓ Updated latest cache: {latest_file}")
print(f"✓ Updated index: {index_file}")
print(f"✓ Saved legacy cache: {LEGACY_CACHE_FILE}")
"""
    return new_source.split('\n')


def update_final_training_loading_cell(cell_source):
    """Update the cell that loads final training cache for conversion."""
    source_text = "".join(cell_source)
    if "training_cache = load_json(FINAL_TRAINING_CACHE_FILE" not in source_text:
        return None
    
    new_source = """from orchestration.paths import load_cache_file

# Try loading from centralized cache first
training_cache = load_cache_file(
    ROOT_DIR, CONFIG_DIR, "final_training", use_latest=True
)

# Fallback to legacy location
if training_cache is None:
    LEGACY_CACHE_FILE = ROOT_DIR / "notebooks" / "final_training_cache.json"
    training_cache = load_json(LEGACY_CACHE_FILE, default=None)

# Try to restore from Google Drive if still not found
if training_cache is None:
    if restore_from_drive("final_training_cache.json", LEGACY_CACHE_FILE, is_directory=False):
        training_cache = load_json(LEGACY_CACHE_FILE, default=None)

if training_cache is None:
    raise FileNotFoundError(
        f"Final training cache not found locally or in backup.\\n"
        f"Please run Step P1-3.7: Final Training first."
    )
"""
    return new_source.split('\n')


def update_continued_training_loading_cell(cell_source):
    """Update the cell that loads cache for continued training."""
    source_text = "".join(cell_source)
    if "previous_cache_path = ROOT_DIR / continued_training_config.get" not in source_text:
        return None
    
    # Check if already updated (has load_cache_file import)
    if "from orchestration.paths import load_cache_file" in source_text:
        # Check for duplicates
        if source_text.count("from orchestration.paths import load_cache_file") > 1:
            # Remove duplicates - rebuild the cell properly
            lines = []
            seen_import = False
            seen_load = False
            in_cache_section = False
            
            for line in cell_source:
                line_str = "".join(line) if isinstance(line, list) else line
                
                # Skip duplicate imports
                if "from orchestration.paths import load_cache_file" in line_str:
                    if not seen_import:
                        lines.append("from orchestration.paths import load_cache_file\n")
                        seen_import = True
                    continue
                
                # Skip duplicate load_cache_file calls
                if "previous_training = load_cache_file(" in line_str:
                    if not seen_load:
                        lines.append("    # Try loading from centralized cache first\n")
                        lines.append("    previous_training = load_cache_file(\n")
                        lines.append("        ROOT_DIR, CONFIG_DIR, \"final_training\", use_latest=True\n")
                        lines.append("    )\n")
                        lines.append("\n")
                        lines.append("    # Fallback to legacy location\n")
                        lines.append("    if previous_training is None:\n")
                        seen_load = True
                        in_cache_section = True
                    continue
                
                # Skip duplicate fallback sections
                if in_cache_section and ("# Fallback to legacy location" in line_str or 
                                        "previous_cache_path = ROOT_DIR / continued_training_config.get" in line_str):
                    if "previous_cache_path" in line_str:
                        lines.append("        previous_cache_path = ROOT_DIR / continued_training_config.get(\n")
                        in_cache_section = False
                    continue
                
                if in_cache_section and "previous_training = load_json(previous_cache_path" in line_str:
                    lines.append("        previous_training = load_json(previous_cache_path, default=None)\n")
                    in_cache_section = False
                    continue
                
                # Normal line
                lines.append(line)
            
            return lines
        return None
    
    # Find and replace the cache loading section
    lines = cell_source.copy()
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        line_str = "".join(line) if isinstance(line, list) else line
        
        if "previous_cache_path = ROOT_DIR / continued_training_config.get" in line_str and i > 0:
            # Check if we're inside the CONTINUED_EXPERIMENT_ENABLED block
            # Insert the new code before this line
            new_lines.append("    from orchestration.paths import load_cache_file\n")
            new_lines.append("\n")
            new_lines.append("    # Try loading from centralized cache first\n")
            new_lines.append("    previous_training = load_cache_file(\n")
            new_lines.append("        ROOT_DIR, CONFIG_DIR, \"final_training\", use_latest=True\n")
            new_lines.append("    )\n")
            new_lines.append("\n")
            new_lines.append("    # Fallback to legacy location\n")
            new_lines.append("    if previous_training is None:\n")
            new_lines.append(line)  # Keep the previous_cache_path line
            # Skip the next load_json line
            i += 1
            if i < len(lines) and "previous_training = load_json(previous_cache_path" in "".join(lines[i]):
                new_lines.append(lines[i])
                i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    return new_lines if new_lines != lines else None


def update_notebook(notebook_path):
    """Update notebook with centralized path configuration."""
    notebook_path = Path(notebook_path)
    
    print(f"Reading notebook: {notebook_path}")
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    updated_cells = 0
    
    for i, cell in enumerate(notebook['cells']):
        if cell['cell_type'] != 'code':
            continue
        
        source = cell['source']
        if isinstance(source, str):
            source = source.split('\n')
        
        # Try each update function
        new_source = None
        
        if update_best_config_saving_cell(source):
            new_source = update_best_config_saving_cell(source)
            print(f"  Updated cell {i}: Best configuration cache saving")
        elif update_best_config_loading_cell(source):
            new_source = update_best_config_loading_cell(source)
            print(f"  Updated cell {i}: Best configuration cache loading")
        elif update_final_training_saving_cell(source):
            new_source = update_final_training_saving_cell(source)
            print(f"  Updated cell {i}: Final training cache saving")
        elif update_final_training_loading_cell(source):
            new_source = update_final_training_loading_cell(source)
            print(f"  Updated cell {i}: Final training cache loading")
        elif update_continued_training_loading_cell(source):
            new_source = update_continued_training_loading_cell(source)
            print(f"  Updated cell {i}: Continued training cache loading")
        
        if new_source:
            cell['source'] = new_source
            updated_cells += 1
    
    if updated_cells > 0:
        # Create backup
        backup_path = notebook_path.with_suffix('.ipynb.backup')
        print(f"Creating backup: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)
        
        # Write updated notebook
        print(f"Writing updated notebook: {notebook_path}")
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)
        
        print(f"\n[OK] Updated {updated_cells} cell(s)")
        print(f"[OK] Backup saved to: {backup_path}")
    else:
        print("No cells needed updating")


if __name__ == "__main__":
    notebook_path = Path(__file__).parent.parent / "notebooks" / "01_orchestrate_training_colab.ipynb"
    
    if len(sys.argv) > 1:
        notebook_path = Path(sys.argv[1])
    
    if not notebook_path.exists():
        print(f"Error: Notebook not found: {notebook_path}")
        sys.exit(1)
    
    update_notebook(notebook_path)

