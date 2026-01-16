# Training Core

Core training components: model training, evaluation, metrics computation, and checkpoint management.

## TL;DR / Quick Start

Train models, evaluate performance, and manage checkpoints.

```python
from src.training.core.trainer import train_model
from src.training.core.evaluator import evaluate_model
from src.training.core.metrics import compute_metrics

# Train a model
train_model(
    config=config,
    train_data=train_samples,
    val_data=val_samples,
    output_dir=Path("outputs/checkpoint")
)

# Evaluate a model
metrics = evaluate_model(
    model=model,
    tokenizer=tokenizer,
    eval_data=val_samples,
    label2id=label2id
)
```

## Overview

The `core` module provides the fundamental training components:

- **Model training**: Training loop with validation, checkpointing, and early stopping
- **Model evaluation**: Evaluate models on validation/test data
- **Metrics computation**: Compute precision, recall, F1, and other metrics
- **Checkpoint management**: Load, validate, and resolve checkpoint paths
- **Cross-validation utilities**: K-fold splitting and fold data management
- **Model creation**: Create models and tokenizers from configuration

## Module Structure

- `trainer.py`: Main training loop and training logic
- `evaluator.py`: Model evaluation on datasets
- `metrics.py`: Metrics computation (precision, recall, F1)
- `model.py`: Model and tokenizer creation
- `checkpoint_loader.py`: Checkpoint loading and validation
- `cv_utils.py`: Cross-validation utilities (K-fold splitting)
- `utils.py`: Training utilities (seed setting, etc.)

## Usage

### Basic Example: Training

```python
from pathlib import Path
from src.training.core.trainer import train_model

# Train model
train_model(
    config={
        "model": {"backbone": "distilbert-base-uncased", "num_labels": 5},
        "training": {
            "learning_rate": 2e-5,
            "batch_size": 16,
            "epochs": 3,
            "random_seed": 42
        }
    },
    train_data=train_samples,
    val_data=val_samples,
    output_dir=Path("outputs/checkpoint")
)
```

### Basic Example: Evaluation

```python
from src.training.core.evaluator import evaluate_model

# Evaluate model
metrics = evaluate_model(
    model=model,
    tokenizer=tokenizer,
    eval_data=val_samples,
    label2id={"O": 0, "PERSON": 1, "ORG": 2}
)

print(f"F1 Score: {metrics['f1']}")
print(f"Precision: {metrics['precision']}")
print(f"Recall: {metrics['recall']}")
```

### Basic Example: Cross-Validation

```python
from src.training.core.cv_utils import create_kfold_splits

# Create K-fold splits
splits = create_kfold_splits(
    dataset=train_data,
    n_folds=5,
    random_seed=42,
    stratified=True
)

# Access fold data
for fold_idx, (train_fold, val_fold) in enumerate(splits):
    # Train on train_fold, validate on val_fold
    pass
```

## API Reference

- `train_model(...)`: Train a model with given configuration and data
- `evaluate_model(...)`: Evaluate a model on evaluation data
- `create_model_and_tokenizer(...)`: Create model and tokenizer from config
- `compute_metrics(...)`: Compute evaluation metrics from predictions
- `validate_checkpoint(...)`: Validate checkpoint directory structure
- `resolve_training_checkpoint_path(...)`: Resolve checkpoint path from config
- `create_kfold_splits(...)`: Create K-fold cross-validation splits
- `set_seed(seed: int) -> None`: Set random seed for reproducibility

For detailed signatures, see source code.

## Integration Points

### Used By

- **Training orchestrator**: Uses trainer for training workflows
- **HPO modules**: Uses trainer for trial execution
- **Testing modules**: Uses evaluator and metrics for validation

### Depends On

- `torch`: PyTorch for model training
- `transformers`: Hugging Face transformers for models and tokenizers
- `data/`: Data loading utilities

## Testing

```bash
uvx pytest tests/training/core/
```

## Related Modules

- [`../README.md`](../README.md) - Main training module
- [`../hpo/README.md`](../hpo/README.md) - HPO uses core training
- [`../../data/README.md`](../../data/README.md) - Data loading utilities

