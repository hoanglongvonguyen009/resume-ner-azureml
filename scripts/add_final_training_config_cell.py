"""Add missing cell to create final_training_config after loading best_configuration."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find the cell that loads best_configuration
best_config_loading_cell_idx = None
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        if "best_configuration = load_cache_file" in source_text and "best_configurations" in source_text:
            best_config_loading_cell_idx = i
            break

if best_config_loading_cell_idx is None:
    print("Could not find best_configuration loading cell")
    exit(1)

print(f"Found best_configuration loading cell at index {best_config_loading_cell_idx}")

# Check if final_training_config is already created in the next cell
next_cell_idx = best_config_loading_cell_idx + 1
if next_cell_idx < len(notebook['cells']):
    next_cell = notebook['cells'][next_cell_idx]
    if next_cell['cell_type'] == 'code':
        next_source = "".join(next_cell['source'])
        if "final_training_config = build_final_training_config" in next_source:
            print("final_training_config creation cell already exists")
            exit(0)

# Create the missing cell
final_training_config_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": """# Build final training configuration from best HPO configuration
final_training_config = build_final_training_config(
    best_config=best_configuration,
    train_config=train_config,
    random_seed=DEFAULT_RANDOM_SEED,
)

print(f"Final training configuration:")
print(f"  Backbone: {final_training_config['backbone']}")
print(f"  Learning rate: {final_training_config['learning_rate']}")
print(f"  Batch size: {final_training_config['batch_size']}")
print(f"  Dropout: {final_training_config['dropout']}")
print(f"  Weight decay: {final_training_config['weight_decay']}")
print(f"  Epochs: {final_training_config['epochs']}")
print(f"  Random seed: {final_training_config['random_seed']}")
print(f"  Early stopping: {final_training_config['early_stopping_enabled']}")
""".split('\n')
}

# Insert the cell after best_configuration loading cell
notebook['cells'].insert(best_config_loading_cell_idx + 1, final_training_config_cell)
print(f"  Inserted final_training_config creation cell at index {best_config_loading_cell_idx + 1}")

# Create backup
backup_path = notebook_path.with_suffix('.ipynb.backup_final_config')
print(f"Creating backup: {backup_path}")
with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

# Write updated notebook
print(f"Writing updated notebook: {notebook_path}")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print("[OK] Added final_training_config creation cell")

