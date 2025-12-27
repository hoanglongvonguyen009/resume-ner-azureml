"""Fix formatting of conversion variables cell - ensure proper line breaks."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find and fix the conversion variables cell
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        if "Extract checkpoint directory, backbone" in source_text:
            # Fix the source - split by lines properly
            new_source = """# Extract checkpoint directory, backbone, and create conversion output directory
from datetime import datetime

# Get checkpoint directory from training cache
checkpoint_source = Path(training_cache.get("output_dir", "")) / "checkpoint"
if not checkpoint_source.exists():
    # Try alternative location
    checkpoint_source = Path(training_cache.get("output_dir", "")) / CHECKPOINT_DIRNAME
    if not checkpoint_source.exists():
        raise FileNotFoundError(
            f"Checkpoint not found in training cache output_dir: {training_cache.get('output_dir', '')}"
        )

checkpoint_dir = checkpoint_source
print(f"Using checkpoint: {checkpoint_dir}")

# Extract backbone from training cache
backbone = training_cache.get("backbone", "unknown")
if backbone == "unknown":
    # Try to get from config
    backbone = training_cache.get("config", {}).get("backbone", "unknown")
    if backbone == "unknown":
        raise ValueError("Could not determine backbone from training cache")

# Extract backbone name (e.g., "distilbert" from "distilbert-base-uncased")
backbone_name = backbone.split("-")[0] if "-" in backbone else backbone

# Generate conversion run ID
conversion_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create conversion output directory
conversion_output_dir = CONVERSION_OUTPUT_DIR / f"{backbone_name}_{conversion_run_id}"
conversion_output_dir.mkdir(parents=True, exist_ok=True)

print(f"Conversion output directory: {conversion_output_dir}")
print(f"Backbone: {backbone}")
print(f"Conversion Run ID: {conversion_run_id}")
"""
            cell['source'] = new_source.split('\n')
            print(f"  Fixed formatting in cell {i}")
            break

# Create backup
backup_path = notebook_path.with_suffix('.ipynb.backup_format_fix')
print(f"Creating backup: {backup_path}")
with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

# Write updated notebook
print(f"Writing updated notebook: {notebook_path}")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print("[OK] Fixed conversion cell formatting")

