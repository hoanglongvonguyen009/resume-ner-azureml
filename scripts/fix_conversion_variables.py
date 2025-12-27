"""Fix missing variables in conversion section: checkpoint_dir, backbone, conversion_output_dir."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find the cell that loads training cache (before conversion_args)
training_cache_cell_idx = None
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        if "training_cache = load_cache_file" in source_text and "final_training" in source_text:
            training_cache_cell_idx = i
            break

if training_cache_cell_idx is None:
    print("Could not find training cache loading cell")
    exit(1)

print(f"Found training cache loading cell at index {training_cache_cell_idx}")

# Find the conversion_args cell
conversion_args_cell_idx = None
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        if "conversion_args = [" in source_text and "model_conversion.convert_to_onnx" in source_text:
            conversion_args_cell_idx = i
            break

if conversion_args_cell_idx is None:
    print("Could not find conversion_args cell")
    exit(1)

print(f"Found conversion_args cell at index {conversion_args_cell_idx}")

# Check if variables are already defined between these cells
needs_variables_cell = True
for i in range(training_cache_cell_idx + 1, conversion_args_cell_idx):
    cell = notebook['cells'][i]
    if cell['cell_type'] == 'code':
        source_text = "".join(cell['source'])
        if "checkpoint_dir = " in source_text and "backbone = " in source_text and "conversion_output_dir = " in source_text:
            print(f"Variables already defined in cell {i}")
            needs_variables_cell = False
            break

if needs_variables_cell:
    # Create cell to define missing variables
    variables_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": """# Extract checkpoint directory, backbone, and create conversion output directory
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
""".split('\n')
    }
    
    # Insert the cell before conversion_args cell
    notebook['cells'].insert(conversion_args_cell_idx, variables_cell)
    print(f"  Inserted variables definition cell at index {conversion_args_cell_idx}")

# Create backup
backup_path = notebook_path.with_suffix('.ipynb.backup_conversion_vars')
print(f"Creating backup: {backup_path}")
with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

# Write updated notebook
print(f"Writing updated notebook: {notebook_path}")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print("[OK] Added missing conversion variables")

