"""Update git branch references in notebook from feature/google-colab-compute to gg."""
import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/01_orchestrate_training_colab.ipynb")

# Load notebook
with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
    notebook = json.load(f)

# Update all occurrences
updated = False
for cell in notebook["cells"]:
    if "source" in cell:
        source = cell["source"]
        if isinstance(source, list):
            source_text = "".join(source)
        else:
            source_text = source
        
        if "feature/google-colab-compute" in source_text:
            # Replace in list format
            new_source = []
            for line in source:
                if "feature/google-colab-compute" in line:
                    line = line.replace("feature/google-colab-compute", "gg")
                    updated = True
                new_source.append(line)
            cell["source"] = new_source

if updated:
    # Save notebook
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    print(f"Updated notebook: {NOTEBOOK_PATH}")
    print("  Changed branch references from 'feature/google-colab-compute' to 'gg'")
else:
    print("No changes needed")

