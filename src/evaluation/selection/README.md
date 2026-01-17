# Evaluation Selection

Model selection logic for choosing the best configuration from HPO results with accuracy-speed tradeoffs.

## TL;DR / Quick Start

Select the best configuration from HPO studies considering both accuracy and inference speed.

```python
from src.evaluation.selection import select_best_configuration_across_studies

# Select best configuration
best_config = select_best_configuration_across_studies(
    hpo_output_dir=Path("outputs/hpo"),
    hpo_config={"objective_metric": "macro-f1"},
    accuracy_threshold=0.95,
    use_relative_threshold=True
)
```

## Overview

The `selection` module provides model selection capabilities:

- **Selection algorithms**: Select best configuration using accuracy-speed tradeoffs
- **Artifact discovery**: Discover and acquire model checkpoints and artifacts
- **Trial finding**: Find best trials from HPO studies
- **Study analysis**: Analyze HPO studies and extract statistics
- **Caching**: Cache selection results for performance
- **MLflow integration**: Select from MLflow-tracked HPO runs

Selection supports both local (Optuna) and AzureML HPO results, with automatic speed score computation from benchmarks or parameter proxies.

## Module Structure

- `selection_logic.py`: Core selection logic (threshold application, speed normalization)
- `local_selection.py`: Local selection from Optuna studies
- `mlflow_selection.py`: MLflow-based selection from AzureML sweep jobs
- `selection.py`: AzureML sweep job selection
- `trial_finder.py`: Trial finding and discovery
- `study_summary.py`: Study analysis and statistics
- `artifact_acquisition.py`: Artifact discovery and acquisition
- `artifact_unified/`: Unified artifact discovery and validation
- `disk_loader.py`: Disk-based loading of trials and benchmarks
- `cache.py`: Selection result caching
- `experiment_discovery.py`: Experiment discovery utilities
- `workflows/`: Selection workflows

## Usage

### Basic Example: Local Selection

```python
from pathlib import Path
from src.evaluation.selection import select_best_configuration_across_studies

# Select from local HPO results
best_config = select_best_configuration_across_studies(
    hpo_output_dir=Path("outputs/hpo"),
    hpo_config={
        "objective_metric": "macro-f1"
    },
    accuracy_threshold=0.95,  # Select fastest within 95% of best accuracy
    use_relative_threshold=True,
    min_accuracy_gain=0.01  # Require 1% accuracy gain for slower models
)

print(f"Selected: {best_config['backbone']}")
print(f"Accuracy: {best_config['accuracy']:.4f}")
print(f"Speed score: {best_config['speed_score']:.2f}")
```

### Basic Example: AzureML Selection

```python
from src.evaluation.selection import select_best_configuration

# Select from AzureML sweep job
best_config = select_best_configuration(
    sweep_job=completed_sweep_job,
    ml_client=ml_client,
    objective_metric="macro-f1"
)
```

### Basic Example: Extract Best from Study

```python
# Use canonical import from training.hpo (where the function is implemented)
from src.training.hpo.core.study import extract_best_config_from_study
import optuna

# Extract best config from Optuna study
study = optuna.load_study(study_name="my_study", storage="sqlite:///study.db")
best_config = extract_best_config_from_study(study)
```

### Basic Example: Find Best Trials

```python
from src.evaluation.selection import find_best_trials_for_backbones

# Find best trials for each backbone
best_trials = find_best_trials_for_backbones(
    hpo_output_dir=Path("outputs/hpo"),
    backbones=["distilbert", "deberta"]
)
```

## API Reference

### Selection Functions

- `select_best_configuration_across_studies(...)`: Select best configuration across multiple backbone studies
- `select_best_configuration(...)`: Select best configuration from AzureML sweep job
- `extract_best_config_from_study(...)`: **Import from `training.hpo.core.study`** - Extract best config from Optuna study (canonical location)
- `select_production_configuration(...)`: Alias for `select_best_configuration`

### Trial Finding

- `find_best_trials_for_backbones(...)`: Find best trials for each backbone
- `find_study_folder_in_backbone_dir(...)`: Find v2 study folder in backbone directory
  - Searches for v2 format folders: `study-{study8}` (e.g., `study-c3659fea`)
  - Returns the first v2 study folder found, or None if not found
  - Supports v2 hash-based folder structure only
- `get_trial_hash_info(...)`: Get trial hash information

### Artifact Acquisition

- `acquire_best_model_checkpoint(...)`: Acquire best model checkpoint
- `load_best_trial_from_disk(...)`: Load best trial from disk
- `load_cached_best_model(...)`: Load cached best model

### Study Analysis

- `extract_cv_statistics(...)`: Extract cross-validation statistics
- `load_study_from_disk(...)`: Load Optuna study from disk
- `print_study_summaries(...)`: Print study summaries
- `format_study_summary_line(...)`: Format study summary line

### Selection Logic

- `SelectionLogic`: Selection logic class
  - `normalize_speed_scores(...)`: Normalize speed scores relative to fastest
  - `apply_threshold(...)`: Apply accuracy-speed tradeoff threshold
- `MODEL_SPEED_SCORES`: Dictionary of model speed scores (parameter proxies)

### Caching

- `compute_selection_cache_key(...)`: Compute cache key for selection
- `load_cached_best_model(...)`: Load cached best model
- `save_best_model_cache(...)`: Save best model to cache

For detailed signatures, see source code.

## Integration Points

### Used By

- **Evaluation workflows**: Use selection for best config selection
- **Notebooks**: Use selection for interactive best config selection
- **Orchestration**: Use selection for workflow orchestration

### Depends On

- `training/`: HPO studies and trial execution
- `infrastructure/`: Path resolution, MLflow tracking
- `common/`: Logging utilities

## Selection Algorithm

The selection algorithm:

1. **Find best trial per backbone**: Extract best trial from each backbone's HPO study
2. **Load speed scores**: Load benchmark speed scores (if available) or use parameter proxies
3. **Normalize speed scores**: Normalize relative to fastest model
4. **Apply threshold**: Select fastest model within accuracy threshold
5. **Return best configuration**: Return selected configuration with metadata

## Speed Scores

Speed scores can come from:
- **Benchmarks**: Actual inference performance from `benchmark.json` files
- **Parameter proxies**: Fallback to `MODEL_SPEED_SCORES` based on parameter count

## Testing

```bash
uvx pytest tests/evaluation/selection/
```

## Related Modules

- [`../README.md`](../README.md) - Main evaluation module
- [`../benchmarking/README.md`](../benchmarking/README.md) - Benchmarking utilities
- [`../../training/README.md`](../../training/README.md) - Training and HPO
- [`../../infrastructure/README.md`](../../infrastructure/README.md) - Infrastructure layer

## Notes

- Selection supports both local (Optuna) and AzureML HPO results
- Speed scores are automatically normalized relative to fastest model
- Selection cache improves performance for repeated selections

