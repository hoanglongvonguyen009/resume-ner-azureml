# Infrastructure Config

Configuration loading, validation, merging, and domain-specific config building.

## TL;DR / Quick Start

Load and manage experiment configurations with validation and merging.

```python
from src.infrastructure.config.loader import load_experiment_config, ExperimentConfig
from src.infrastructure.config.merging import merge_configs_with_precedence

# Load experiment configuration
config = load_experiment_config(
    config_root=Path("config/"),
    experiment_name="resume_ner_baseline"
)

# Merge configurations
merged = merge_configs_with_precedence(defaults, overrides)
```

## Overview

The `config` module provides configuration management:

- **Configuration loading**: Load experiment and domain configurations from YAML files
- **Configuration validation**: Validate configuration schemas and values
- **Configuration merging**: Merge configurations with precedence rules
- **Run mode management**: Handle run modes (force_new, reuse_if_exists, resume_if_incomplete)
- **Variant management**: Compute and find configuration variants
- **Argument overrides**: Apply command-line argument overrides to configurations

## Module Structure

- `loader.py`: Experiment configuration loading and domain config loading
- `merging.py`: Configuration merging and argument overrides
- `validation.py`: Configuration validation
- `run_mode.py`: Run mode utilities
- `run_decision.py`: Run decision logic (reuse, resume, etc.)
- `variants.py`: Configuration variant management
- `training.py`: Training-specific configuration loading
- `selection.py`: Selection-specific configuration loading
- `conversion.py`: Conversion-specific configuration loading
- `environment.py`: Environment configuration

## Usage

### Basic Example: Load Experiment Config

```python
from pathlib import Path
from src.infrastructure.config.loader import load_experiment_config

# Load experiment configuration
config = load_experiment_config(
    config_root=Path("config/"),
    experiment_name="resume_ner_baseline"
)

# Access domain configs
data_config_path = config.data_config
model_config_path = config.model_config
train_config_path = config.train_config
```

### Basic Example: Merge Configurations

```python
from src.infrastructure.config.merging import merge_configs_with_precedence

# Merge configurations (overrides take precedence)
defaults = {
    "training": {"learning_rate": 2e-5, "batch_size": 16}
}
overrides = {
    "training": {"learning_rate": 1e-5}  # Override learning_rate
}
merged = merge_configs_with_precedence(defaults, overrides)
# Result: {"training": {"learning_rate": 1e-5, "batch_size": 16}}
```

### Basic Example: Run Mode

```python
from src.infrastructure.config.run_mode import get_run_mode, RunMode

# Get run mode from config
run_mode = get_run_mode(config)
if run_mode == RunMode.FORCE_NEW:
    # Create new run
    pass
elif run_mode == RunMode.REUSE_IF_EXISTS:
    # Reuse existing run if available
    pass
```

## API Reference

### Configuration Loading

- `load_experiment_config(config_root: Path, experiment_name: str) -> ExperimentConfig`: Load experiment configuration
- `load_all_configs(config_root: Path, experiment_name: str) -> Dict[str, Any]`: Load all domain configs
- `ExperimentConfig`: Dataclass representing experiment configuration

### Configuration Merging

- `merge_configs_with_precedence(defaults: Dict, overrides: Dict) -> Dict`: Merge configurations
- `apply_argument_overrides(config: Dict, args: argparse.Namespace) -> Dict`: Apply argument overrides

### Run Mode

- `get_run_mode(config: Dict) -> RunMode`: Get run mode from config
- `is_force_new(config: Dict) -> bool`: Check if force_new mode
- `is_reuse_if_exists(config: Dict) -> bool`: Check if reuse_if_exists mode
- `is_resume_if_incomplete(config: Dict) -> bool`: Check if resume_if_incomplete mode
- `RunMode`: Enum for run modes

### Variants

- `compute_next_variant(...)`: Compute next variant number
  - **Signature**: `compute_next_variant(root_dir, config_dir, process_type, model, spec_fp=None, exec_fp=None, base_name=None)`
  - **Required parameters**: `root_dir`, `config_dir`, `process_type` ("final_training" or "hpo"), `model`
  - **For HPO**: Requires `base_name` parameter (e.g., "hpo_distilbert")
  - **For final_training**: Requires `spec_fp` and `exec_fp` parameters
  - **Note**: For HPO process type, `config_dir` must contain a valid `paths.yaml` file (used by `resolve_output_path()`)
- `find_existing_variants(...)`: Find existing variants
  - **Signature**: `find_existing_variants(root_dir, config_dir, process_type, model, spec_fp=None, exec_fp=None, base_name=None)`
  - **Required parameters**: Same as `compute_next_variant()`
  - **Note**: For HPO process type, `config_dir` must contain a valid `paths.yaml` file

**Example**:
```python
from infrastructure.config.variants import compute_next_variant
from pathlib import Path

# For HPO variants (requires paths.yaml in config_dir)
config_dir = Path("config")  # Must contain paths.yaml
next_variant = compute_next_variant(
    root_dir=Path("."),
    config_dir=config_dir,
    process_type="hpo",
    model="distilbert",
    base_name="hpo_distilbert"
)
```

For detailed signatures, see source code.

## Integration Points

### Used By

- **Training modules**: Use config loading for training configuration
- **Orchestration modules**: Use config loading for job configuration
- **Evaluation modules**: Use config loading for evaluation configuration

### Depends On

- `common/`: YAML utilities, file utilities

## Configuration Structure

### Experiment Configuration

Experiment configs are YAML files in `config/experiment/<name>.yaml`:

```yaml
name: resume_ner_baseline
data: data/baseline.yaml
model: model/distilbert.yaml
training: training/baseline.yaml
hpo: hpo/baseline.yaml
env: env/local.yaml
benchmark: benchmark/baseline.yaml
stages:
  hpo: ...
  training: ...
naming: ...
```

### Domain Configurations

Domain configs (data, model, training, HPO, etc.) are referenced by experiment configs and loaded separately.

## Testing

```bash
uvx pytest tests/infrastructure/config/
```

## Related Modules

- [`../README.md`](../README.md) - Main infrastructure module
- [`../paths/README.md`](../paths/README.md) - Path resolution uses config
- [`../../common/README.md`](../../common/README.md) - Shared utilities

