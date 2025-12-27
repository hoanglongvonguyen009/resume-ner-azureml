# Continued Training Guide

This guide explains how to use the continued training feature to fine-tune models on new datasets by loading checkpoints from previous training runs.

## Overview

Continued training allows you to:
- Fine-tune models on new domain-specific data
- Perform incremental learning with additional training samples
- Adapt models to new data distributions while preserving learned knowledge

## Configuration

### Step 1: Create Continued Training Config

Create or modify `config/train_continued.yaml`:

```yaml
# Checkpoint loading configuration
checkpoint:
  source_path: "outputs/final_training/{backbone}_{run_id}/checkpoint"
  validate: true

# Dataset combination configuration
data:
  strategy: "combined"  # "new_only", "combined", or "append"
  old_dataset_path: "../dataset_tiny/seed0"
  new_dataset_path: "../dataset_new"
  create_new_validation: true
  validation_ratio: 0.1
  random_seed: 42

# Training hyperparameters (override base config)
training:
  learning_rate: 1e-5  # Lower LR for fine-tuning
  epochs: 3  # Fewer epochs
  early_stopping:
    enabled: false
```

### Step 2: Create Experiment Config

Create `config/experiment/resume_ner_continued.yaml`:

```yaml
experiment_name: "resume_ner_continued"

data_config: "data/resume_tiny.yaml"
model_config: "model/distilbert.yaml"
train_config: "train_continued.yaml"  # Use continued training config
hpo_config: "hpo/prod.yaml"
env_config: "env/azure.yaml"
benchmark_config: "benchmark.yaml"

continued_training:
  base_experiment: "resume_ner_baseline"
  checkpoint_selection: "latest"
  previous_training_cache: "notebooks/best_configuration_cache.json"
  
  new_data:
    local_path: "../dataset_new"

stages:
  training:
    aml_experiment: "resume-ner-continued"
    backbones:
      - "distilbert"

naming:
  include_backbone_in_experiment: true
```

## Data Combination Strategies

### 1. `new_only`
Train only on the new dataset. Useful when you want to completely replace the training data.

```yaml
data:
  strategy: "new_only"
  new_dataset_path: "../dataset_new"
```

### 2. `combined`
Merge old and new datasets and shuffle them together. This is the recommended strategy for most use cases.

```yaml
data:
  strategy: "combined"
  old_dataset_path: "../dataset_tiny/seed0"
  new_dataset_path: "../dataset_new"
  validation_ratio: 0.1
```

### 3. `append`
Append new data to old data without shuffling. Useful when you want to preserve the original order.

```yaml
data:
  strategy: "append"
  old_dataset_path: "../dataset_tiny/seed0"
  new_dataset_path: "../dataset_new"
```

## Checkpoint Resolution

The checkpoint path is resolved in the following priority order:

1. **Environment Variable**: `CHECKPOINT_PATH` (highest priority)
2. **Config File**: `config["training"]["checkpoint"]["source_path"]`
3. **Previous Training Cache**: JSON file containing previous training output directory

### Pattern Resolution

The checkpoint path supports pattern replacement:
- `{backbone}` - Replaced with backbone name (e.g., "distilbert")
- `{run_id}` - Replaced with run ID (e.g., "20251227_220407")

Example:
```yaml
checkpoint:
  source_path: "outputs/final_training/{backbone}_{run_id}/checkpoint"
```

## Usage in Notebook

### Enable Continued Training

In `notebooks/01_orchestrate_training_colab.ipynb`, find the "Step P1-3.8: Continued Training" section and set:

```python
CONTINUED_EXPERIMENT_ENABLED = True
```

### Automatic Workflow

The notebook will:
1. Load the continued training experiment config
2. Resolve the checkpoint path from previous training
3. Combine datasets according to the specified strategy
4. Run training with the checkpoint loaded

### Manual Checkpoint Path

You can also set the checkpoint path manually via environment variable:

```python
import os
os.environ["CHECKPOINT_PATH"] = "path/to/checkpoint"
```

## Best Practices

### Learning Rate
- Use a lower learning rate (e.g., 1e-5) compared to initial training (2e-5)
- This prevents overwriting learned features too aggressively

### Epochs
- Use fewer epochs (2-3) since the model is already trained
- Monitor validation metrics to avoid overfitting

### Early Stopping
- Consider disabling early stopping for continued training
- The model may need a few epochs to adapt to new data

### Data Strategy
- Use `combined` strategy for balanced learning from both datasets
- Use `new_only` if new data completely replaces old data
- Use `append` if you want to preserve data order

## Troubleshooting

### Checkpoint Not Found

**Error**: `Warning: Checkpoint path ... doesn't exist`

**Solution**:
1. Verify the checkpoint directory exists
2. Check that it contains `config.json` and model files
3. Update the checkpoint path in config or set `CHECKPOINT_PATH` environment variable

### Label Mismatch

**Error**: `Warning: Label mappings differ between checkpoint and config`

**Solution**:
- Ensure the new dataset uses the same label schema as the checkpoint
- The model will use the config labels, but this may cause issues if labels differ significantly

### Dataset Not Found

**Error**: `FileNotFoundError: Dataset path not found`

**Solution**:
1. Verify dataset paths in `config/train_continued.yaml`
2. Use absolute paths or paths relative to the config directory
3. Ensure `train.json` exists in the dataset directory

### Invalid Strategy

**Error**: `ValueError: Invalid strategy`

**Solution**:
- Use one of: `"new_only"`, `"combined"`, or `"append"`
- Ensure old dataset path is provided for `"combined"` and `"append"` strategies

## Examples

### Example 1: Fine-tuning on New Domain

```yaml
# config/train_continued.yaml
checkpoint:
  source_path: "outputs/final_training/distilbert_20251227_220407/checkpoint"

data:
  strategy: "combined"
  old_dataset_path: "../dataset_general"
  new_dataset_path: "../dataset_medical"  # Medical domain data
  validation_ratio: 0.15

training:
  learning_rate: 5e-6  # Very low LR for domain adaptation
  epochs: 5
```

### Example 2: Incremental Learning

```yaml
data:
  strategy: "append"
  old_dataset_path: "../dataset_v1"
  new_dataset_path: "../dataset_v2"  # Additional samples

training:
  learning_rate: 1e-5
  epochs: 2
```

## Integration with MLflow

Continued training runs are tracked in MLflow with:
- Experiment name: `{experiment_name}-continued-{backbone}`
- Run name: `{backbone}_continued_{run_id}`
- Tag: `training_type: "continued"`

## API Reference

### `resolve_checkpoint_path()`

Resolves checkpoint path from config, environment, or cache.

```python
from training.checkpoint_loader import resolve_checkpoint_path

checkpoint_path = resolve_checkpoint_path(
    config=config_dict,
    previous_cache_path=Path("cache.json"),
    backbone="distilbert",
    run_id="20251227_220407",
)
```

### `combine_datasets()`

Combines datasets according to specified strategy.

```python
from training.data_combiner import combine_datasets

combined = combine_datasets(
    old_dataset_path=Path("old_dataset"),
    new_dataset_path=Path("new_dataset"),
    strategy="combined",
    validation_ratio=0.1,
    random_seed=42,
)
```

### `create_model_and_tokenizer()`

Loads model from checkpoint if path is provided.

```python
from training.model import create_model_and_tokenizer

model, tokenizer, device = create_model_and_tokenizer(
    config=config_dict,
    label2id=label2id,
    id2label=id2label,
    checkpoint_path="path/to/checkpoint",  # Optional
)
```

