"""Update final_training_config cell to ensure train_config is available."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find the cell that creates final_training_config
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        if "final_training_config = build_final_training_config" in source_text:
            # Update the cell to ensure train_config is available
            new_source = """# Build final training configuration from best HPO configuration
# Use train_config from configs if available, otherwise load it
if 'train_config' not in locals():
    train_config = configs.get("train", {})

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
"""
            cell['source'] = new_source.split('\n')
            print(f"  Updated cell {i}")
            break

# Create backup
backup_path = notebook_path.with_suffix('.ipynb.backup_update_config')
print(f"Creating backup: {backup_path}")
with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

# Write updated notebook
print(f"Writing updated notebook: {notebook_path}")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print("[OK] Updated final_training_config cell")

