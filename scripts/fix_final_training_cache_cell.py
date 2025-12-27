"""Fix final training cache cell by adding missing checkpoint/metrics checking cell."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find the cell that saves final training cache
cache_saving_cell_idx = None
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        if "Prepare cache data" in source_text and "final_training_cache_data" in source_text:
            cache_saving_cell_idx = i
            break

if cache_saving_cell_idx is None:
    print("Could not find final training cache saving cell")
    exit(1)

print(f"Found cache saving cell at index {cache_saving_cell_idx}")

# Check if the checkpoint/metrics checking cell exists before it
prev_cell = notebook['cells'][cache_saving_cell_idx - 1] if cache_saving_cell_idx > 0 else None
prev_source = "".join(prev_cell['source']) if prev_cell and prev_cell['cell_type'] == 'code' else ""

if "Check actual checkpoint location" in prev_source or "checkpoint_source" in prev_source:
    print("Checkpoint checking cell already exists")
else:
    print("Adding checkpoint/metrics checking cell before cache saving cell")
    
    # Create the missing cell
    checkpoint_check_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": """import json
import shutil
from pathlib import Path
import os

# Check actual checkpoint location
# The training script may save to outputs/checkpoint instead of final_output_dir/checkpoint
actual_checkpoint = ROOT_DIR / "outputs" / "checkpoint"
actual_metrics = ROOT_DIR / "outputs" / METRICS_FILENAME
expected_checkpoint = final_output_dir / "checkpoint"
expected_metrics = final_output_dir / METRICS_FILENAME

print("Checking training completion...")
print(f"  Expected checkpoint: {expected_checkpoint} (exists: {expected_checkpoint.exists()})")
print(f"  Actual checkpoint: {actual_checkpoint} (exists: {actual_checkpoint.exists()})")
print(f"  Expected metrics: {expected_metrics} (exists: {expected_metrics.exists()})")
print(f"  Actual metrics: {actual_metrics} (exists: {actual_metrics.exists()})")

# Determine which checkpoint and metrics to use
checkpoint_source = None
metrics_file = None

if expected_checkpoint.exists() and any(expected_checkpoint.iterdir()):
    checkpoint_source = expected_checkpoint
    print(f"✓ Using expected checkpoint location: {checkpoint_source}")
elif actual_checkpoint.exists() and any(actual_checkpoint.iterdir()):
    checkpoint_source = actual_checkpoint
    print(f"✓ Using actual checkpoint location: {checkpoint_source}")
    # Update final_output_dir to match actual location
    final_output_dir = actual_checkpoint.parent

if expected_metrics.exists():
    metrics_file = expected_metrics
elif actual_metrics.exists():
    metrics_file = actual_metrics

# Load metrics if available
metrics = None
if metrics_file and metrics_file.exists():
    with open(metrics_file, "r") as f:
        metrics = json.load(f)
    print(f"✓ Metrics loaded from: {metrics_file}")
    print(f"  Metrics: {metrics}")
elif checkpoint_source:
    print(f"⚠ Warning: Metrics file not found, but checkpoint exists.")
    metrics = {"status": "completed", "checkpoint_found": True}
else:
    raise FileNotFoundError(
        f"Training completed but no checkpoint found.\\n"
        f"  Expected: {expected_checkpoint}\\n"
        f"  Actual: {actual_checkpoint}\\n"
        f"  Please check training logs for errors."
    )
""".split('\n')
    }
    
    # Insert the cell before the cache saving cell
    notebook['cells'].insert(cache_saving_cell_idx, checkpoint_check_cell)
    print(f"  Inserted checkpoint checking cell at index {cache_saving_cell_idx}")

# Create backup
backup_path = notebook_path.with_suffix('.ipynb.backup_fix')
print(f"Creating backup: {backup_path}")
with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

# Write updated notebook
print(f"Writing updated notebook: {notebook_path}")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print("[OK] Fixed final training cache cell")

