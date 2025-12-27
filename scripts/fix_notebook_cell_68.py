"""Fix cell 68 in the notebook - continued training cache loading."""

import json
from pathlib import Path

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find cell 68 (index 67)
cell = notebook['cells'][67]

# Replace the source with correct code
cell['source'] = """# Resolve checkpoint path and prepare dataset for continued training
if CONTINUED_EXPERIMENT_ENABLED:
    # Get previous training cache
    from orchestration.paths import load_cache_file
    
    # Try loading from centralized cache first
    previous_training = load_cache_file(
        ROOT_DIR, CONFIG_DIR, "final_training", use_latest=True
    )
    
    # Fallback to legacy location
    if previous_training is None:
        previous_cache_path = ROOT_DIR / continued_training_config.get(
            "previous_training_cache", 
            "notebooks/final_training_cache.json"
        )
        previous_training = load_json(previous_cache_path, default=None)
    
    if previous_training:
        # Get checkpoint directory from previous training
        previous_output_dir = Path(previous_training.get("output_dir", ""))
        if previous_output_dir.exists():
            previous_checkpoint_dir = previous_output_dir / "checkpoint"
        else:
            # Try to get from final_training_cache.json
            final_training_cache = load_json(
                ROOT_DIR / "notebooks" / "final_training_cache.json",
                default=None
            )
            if final_training_cache:
                previous_output_dir = Path(final_training_cache.get("output_dir", ""))
                previous_checkpoint_dir = previous_output_dir / "checkpoint"
            else:
                previous_checkpoint_dir = None
    else:
        previous_checkpoint_dir = None
    
    # Resolve checkpoint path using checkpoint loader
    backbone = continued_configs["model"]["backbone"].split("-")[0] if "-" in continued_configs["model"]["backbone"] else continued_configs["model"]["backbone"]
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Add checkpoint config to training config for resolution
    continued_configs["training"]["checkpoint"] = checkpoint_config
    continued_configs["training"]["run_id"] = run_id
    continued_configs["_config_dir"] = CONFIG_DIR
    
    checkpoint_path = resolve_checkpoint_path(
        config=continued_configs,
        previous_cache_path=previous_cache_path if previous_training else None,
        backbone=backbone,
        run_id=run_id,
    )
    
    if checkpoint_path:
        print(f"✓ Resolved checkpoint: {checkpoint_path}")
    else:
        print("⚠ No checkpoint found. Will create new model from backbone.")
        checkpoint_path = None
    
    # Prepare dataset based on strategy
    data_strategy = data_config_continued.get("strategy", "combined")
    new_dataset_path_str = data_config_continued.get("new_dataset_path")
    
    if not new_dataset_path_str:
        # Try to get from experiment config
        new_data_config = continued_training_config.get("new_data", {})
        new_dataset_path_str = new_data_config.get("local_path")
        if new_dataset_path_str:
            new_dataset_path = (CONFIG_DIR / new_dataset_path_str).resolve()
        else:
            # Fallback to data config
            new_dataset_path = DATASET_LOCAL_PATH
    else:
        new_dataset_path = (CONFIG_DIR / new_dataset_path_str).resolve() if not Path(new_dataset_path_str).is_absolute() else Path(new_dataset_path_str)
    
    print(f"New dataset path: {new_dataset_path}")
    
    # Combine datasets based on strategy
    if data_strategy == "new_only":
        combined_dataset = load_dataset(str(new_dataset_path))
        print(f"✓ Using new dataset only ({len(combined_dataset.get('train', []))} samples)")
    else:
        old_dataset_path_str = data_config_continued.get("old_dataset_path")
        if old_dataset_path_str:
            old_dataset_path = (CONFIG_DIR / old_dataset_path_str).resolve() if not Path(old_dataset_path_str).is_absolute() else Path(old_dataset_path_str)
        else:
            old_dataset_path = DATASET_LOCAL_PATH
        
        validation_ratio = data_config_continued.get("validation_ratio", 0.1)
        random_seed = data_config_continued.get("random_seed", 42)
        
        combined_dataset = combine_datasets(
            old_dataset_path=old_dataset_path,
            new_dataset_path=new_dataset_path,
            strategy=data_strategy,
            validation_ratio=validation_ratio,
            random_seed=random_seed,
        )
        print(f"✓ Combined datasets using '{data_strategy}' strategy")
        print(f"  Total training samples: {len(combined_dataset.get('train', []))}")
        print(f"  Validation samples: {len(combined_dataset.get('validation', []))}")
    
    # Update data config with combined dataset path (temporary location)
    # We'll save the combined dataset to a temp location
    combined_dataset_dir = ROOT_DIR / "outputs" / "continued_training" / "combined_dataset"
    combined_dataset_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(combined_dataset_dir / "train.json", "w") as f:
        json.dump(combined_dataset.get("train", []), f, indent=2)
    if combined_dataset.get("validation"):
        with open(combined_dataset_dir / "validation.json", "w") as f:
            json.dump(combined_dataset["validation"], f, indent=2)
    
    CONTINUED_DATASET_PATH = combined_dataset_dir
    print(f"✓ Combined dataset saved to: {CONTINUED_DATASET_PATH}")
else:
    print("Skipping continued training setup (disabled)")
""".split('\n')

# Create backup
backup_path = notebook_path.with_suffix('.ipynb.backup2')
print(f"Creating backup: {backup_path}")
with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

# Write updated notebook
print(f"Writing updated notebook: {notebook_path}")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print("[OK] Fixed cell 68")

