"""Verify and fix notebook updates."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

print("\nChecking cells for centralized paths usage:")
print("=" * 60)

issues_found = False

for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    
    source_text = "".join(cell['source'])
    
    # Check for old patterns
    if "save_json(BEST_CONFIG_CACHE_FILE, best_configuration)" in source_text:
        print(f"  [ISSUE] Cell {i}: Still uses old BEST_CONFIG_CACHE_FILE saving")
        issues_found = True
    
    if "best_configuration = load_json(BEST_CONFIG_CACHE_FILE" in source_text:
        print(f"  [ISSUE] Cell {i}: Still uses old BEST_CONFIG_CACHE_FILE loading")
        issues_found = True
    
    if "save_json(FINAL_TRAINING_CACHE_FILE," in source_text and "save_cache_with_dual_strategy" not in source_text:
        print(f"  [ISSUE] Cell {i}: Still uses old FINAL_TRAINING_CACHE_FILE saving")
        issues_found = True
    
    if "training_cache = load_json(FINAL_TRAINING_CACHE_FILE" in source_text and "load_cache_file" not in source_text:
        print(f"  [ISSUE] Cell {i}: Still uses old FINAL_TRAINING_CACHE_FILE loading")
        issues_found = True
    
    # Check for new patterns
    if "save_cache_with_dual_strategy" in source_text:
        print(f"  [OK] Cell {i}: Uses save_cache_with_dual_strategy")
    
    if "load_cache_file" in source_text:
        print(f"  [OK] Cell {i}: Uses load_cache_file")
        
        # Check for duplicates
        if source_text.count("from orchestration.paths import load_cache_file") > 1:
            print(f"  [WARNING] Cell {i}: Has duplicate load_cache_file imports")
            issues_found = True

if not issues_found:
    print("\n[OK] All cells updated successfully!")
else:
    print("\n[WARNING] Some issues found - may need manual fixes")

print("\nSummary:")
print(f"  Total cells: {len(notebook['cells'])}")
print(f"  Code cells: {sum(1 for c in notebook['cells'] if c['cell_type'] == 'code')}")

