# Evaluation

Model evaluation, selection, and benchmarking utilities for choosing the best configuration from HPO results.

## TL;DR / Quick Start

Select best configurations from HPO results and benchmark model performance.

```python
from src.evaluation.selection import select_best_configuration_across_studies
from src.evaluation.benchmarking import benchmark_best_trials

# Select best configuration across HPO studies
best_config = select_best_configuration_across_studies(
    hpo_output_dir=Path("outputs/hpo"),
    hpo_config=hpo_config,
    accuracy_threshold=0.95
)

# Benchmark best trials
benchmark_best_trials(
    best_trials=best_trials,
    test_data_path=Path("dataset/test.json")
)
```

## Overview

The `evaluation` module provides evaluation and selection capabilities:

- **Model selection**: Select best configuration from HPO results using accuracy-speed tradeoffs
- **Benchmarking**: Measure inference performance (latency, throughput) for model checkpoints
- **Artifact acquisition**: Acquire model checkpoints and artifacts for evaluation
- **Study analysis**: Analyze HPO studies and extract statistics
- **Experiment discovery**: Discover HPO experiments and benchmark results

This module helps choose the best model configuration after HPO by considering both accuracy and inference speed.

## Key Concepts

- **Selection logic**: Accuracy-speed tradeoff with configurable thresholds
- **Speed scores**: Normalized speed scores (from benchmarks or parameter proxies)
- **Best trial selection**: Select best trial per backbone, then best overall
- **Benchmarking**: Measure actual inference performance to replace parameter proxies

## Module Structure

This module is organized into the following submodules:

- `selection/`: Model selection logic
  - Selection algorithms, artifact discovery, trial finding, study analysis
- `benchmarking/`: Benchmarking utilities
  - Inference performance measurement, model comparison, orchestration

See individual submodule READMEs for detailed documentation:
- [`selection/README.md`](selection/README.md) - Model selection logic
- [`benchmarking/README.md`](benchmarking/README.md) - Benchmarking utilities

## Usage

### Basic Workflow: Select Best Configuration

```python
from pathlib import Path
from src.evaluation.selection import select_best_configuration_across_studies

# Select best configuration from HPO results
best_config = select_best_configuration_across_studies(
    hpo_output_dir=Path("outputs/hpo"),
    hpo_config={
        "objective_metric": "macro-f1"
    },
    accuracy_threshold=0.95,  # Select fastest model within 95% of best accuracy
    use_relative_threshold=True
)

print(f"Best backbone: {best_config['backbone']}")
print(f"Best accuracy: {best_config['accuracy']}")
print(f"Speed score: {best_config['speed_score']}")
```

### Basic Workflow: Benchmark Best Trials

```python
from src.evaluation.benchmarking import benchmark_best_trials

# Benchmark best trials from selection
benchmark_best_trials(
    best_trials=[
        {"backbone": "distilbert", "trial_path": Path("outputs/hpo/distilbert/trial_0")},
        {"backbone": "deberta", "trial_path": Path("outputs/hpo/deberta/trial_1")}
    ],
    test_data_path=Path("dataset/test.json"),
    batch_sizes=[1, 8, 16]
)
```

## API Reference

### Selection

- `select_best_configuration_across_studies(...)`: Select best configuration across multiple backbone studies
- `select_best_configuration(...)`: Select best configuration from AzureML sweep job
- `extract_best_config_from_study(...)`: Extract best config from Optuna study
- `find_best_trials_for_backbones(...)`: Find best trials for each backbone
- `acquire_best_model_checkpoint(...)`: Acquire best model checkpoint
- `SelectionLogic`: Selection logic class with threshold application

### Benchmarking

- `benchmark_best_trials(...)`: Benchmark multiple best trials
- `benchmark_model(...)`: Benchmark a single model checkpoint
- `compare_models(...)`: Compare benchmark results across models
- `run_benchmarking(...)`: Run benchmarking workflow

For detailed signatures, see source code or submodule documentation.

## Integration Points

### Dependencies

- `training/`: HPO studies and trial execution
- `infrastructure/`: Path resolution, MLflow tracking
- `data/`: Data loading for benchmarking

### Used By

- **Notebooks**: Use evaluation for best config selection
- **Orchestration**: Use evaluation for workflow orchestration

## Examples

### Example 1: Local Selection

```python
from pathlib import Path
from src.evaluation.selection import select_best_configuration_across_studies

# Select from local HPO results
best_config = select_best_configuration_across_studies(
    hpo_output_dir=Path("outputs/hpo"),
    hpo_config={"objective_metric": "macro-f1"},
    accuracy_threshold=0.95,
    use_relative_threshold=True
)
```

### Example 2: AzureML Selection

```python
from src.evaluation.selection import select_best_configuration

# Select from AzureML sweep job
best_config = select_best_configuration(
    sweep_job=completed_sweep_job,
    ml_client=ml_client,
    objective_metric="macro-f1"
)
```

## Best Practices

1. **Use accuracy thresholds**: Always use accuracy thresholds for accuracy-speed tradeoffs
2. **Benchmark before selection**: Run benchmarks to get real speed scores instead of parameter proxies
3. **Cache selection results**: Use selection cache to avoid recomputing selections
4. **Validate selections**: Always validate selected configurations before use

## Notes

- Selection uses accuracy-speed tradeoff with configurable thresholds
- Speed scores come from benchmarks (if available) or parameter proxies (fallback)
- Selection supports both local (Optuna) and AzureML HPO results
- `src/selection/` module is deprecated (use `evaluation.selection` instead)

## Testing

```bash
uvx pytest tests/evaluation/
```

## Related Modules

- [`selection/README.md`](selection/README.md) - Model selection logic
- [`benchmarking/README.md`](benchmarking/README.md) - Benchmarking utilities
- [`../training/README.md`](../training/README.md) - Training and HPO
- [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure layer
- [`../benchmarking/README.md`](../benchmarking/README.md) - Standalone benchmarking module

