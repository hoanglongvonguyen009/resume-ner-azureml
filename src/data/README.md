# Data

Data loading and processing utilities for training, evaluation, and benchmarking.

## TL;DR / Quick Start

Load datasets, process data, and combine datasets for training workflows.

```python
# Note: Import directly from submodules
from src.data.loaders.dataset_loader import load_dataset, ResumeNERDataset, build_label_list
from src.data.processing.data_combiner import combine_datasets

# Load dataset from JSON files
dataset = load_dataset("dataset/")
# Returns: {"train": [...], "validation": [...], "test": [...]}

# Build label list from config
labels = build_label_list(data_config)
# Returns: ["O", "PERSON", "ORG", ...]

# Combine old and new datasets
combined = combine_datasets(
    old_dataset_path=Path("old_dataset/"),
    new_dataset_path=Path("new_dataset/"),
    strategy="combined"
)
```

## Overview

The `data` module provides utilities for:

- **Data loading**: Load datasets from JSON files, create PyTorch datasets, and handle test data for benchmarking
- **Data processing**: Combine datasets for continued training scenarios
- **Dataset utilities**: Build label lists, split datasets, and encode annotations

This module is used by training workflows, evaluation/testing, and benchmarking modules.

## Module Structure

- `loaders/`: Data loading utilities
  - `dataset_loader.py`: Main dataset loading, ResumeNERDataset class, label building
  - `benchmark_loader.py`: Test data loading for benchmarking
- `processing/`: Data processing utilities
  - `data_combiner.py`: Dataset combination for continued training

## Usage

### Basic Example: Loading Datasets

```python
from src.data.loaders.dataset_loader import load_dataset

# Load dataset from directory containing train.json and optionally validation.json, test.json
dataset = load_dataset("dataset/")

# Access splits
train_data = dataset["train"]  # List of training samples
val_data = dataset["validation"]  # List of validation samples (empty if not present)
test_data = dataset["test"]  # List of test samples (empty if not present)

# Each sample is a dict with "text" and "annotations" keys
sample = train_data[0]
print(sample["text"])  # "John Smith worked at Microsoft."
print(sample["annotations"])  # [[0, 10, "PERSON"], [21, 30, "ORG"]]
```

### Basic Example: Building Label Lists

```python
from src.data.loaders.dataset_loader import build_label_list

# Build label list from data configuration
data_config = {
    "schema": {
        "entity_types": ["PERSON", "ORG", "LOCATION"]
    }
}
labels = build_label_list(data_config)
# Returns: ["O", "LOCATION", "ORG", "PERSON"]
# Note: "O" is always first, then sorted entity types
```

### Basic Example: Creating PyTorch Dataset

```python
from src.data.loaders.dataset_loader import ResumeNERDataset
from transformers import AutoTokenizer

# Create tokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

# Create dataset
dataset = ResumeNERDataset(
    samples=train_data,
    tokenizer=tokenizer,
    max_length=512,
    label2id={"O": 0, "PERSON": 1, "ORG": 2}
)

# Use with DataLoader
from torch.utils.data import DataLoader
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
```

### Basic Example: Combining Datasets

```python
from src.data.processing.data_combiner import combine_datasets
from pathlib import Path

# Combine old and new datasets
combined = combine_datasets(
    old_dataset_path=Path("outputs/previous_training/dataset/"),
    new_dataset_path=Path("dataset/new_data/"),
    strategy="combined",  # Options: "new_only", "combined", "append"
    validation_ratio=0.1,
    random_seed=42
)

# Result contains combined train and validation splits
train_combined = combined["train"]
val_combined = combined["validation"]
```

### Advanced Example: Loading Test Texts for Benchmarking

```python
from src.data.loaders.benchmark_loader import load_test_texts
from pathlib import Path

# Load test texts from JSON file
# Supports both list of strings and list of dicts with 'text' field
test_texts = load_test_texts(Path("dataset/test.json"))

# Use for benchmarking
for text in test_texts:
    # Process text...
    pass
```

## API Reference

### Data Loaders

- `load_dataset(data_path: str) -> Dict[str, Any]`: Load dataset from JSON files in directory
- `build_label_list(data_config: Dict[str, Any]) -> List[str]`: Build label list from data configuration
- `ResumeNERDataset`: PyTorch-compatible dataset class for NER token classification
- `load_test_texts(file_path: Path) -> List[str]`: Load test texts from JSON file for benchmarking
- `split_train_test(...) -> Tuple[List, List]`: Split dataset into train/test with optional stratification
- `save_split_files(...) -> None`: Save split datasets to JSON files

### Data Processing

- `combine_datasets(old_dataset_path: Optional[Path], new_dataset_path: Path, strategy: str = "combined", validation_ratio: float = 0.1, random_seed: int = 42) -> Dict[str, List[Dict[str, Any]]]`: Combine datasets for continued training

For detailed signatures, see source code.

## Integration Points

### Used By

- **Training modules**: Uses `load_dataset`, `ResumeNERDataset`, `build_label_list` for training workflows
- **Testing modules**: Uses `load_dataset` for validation and testing
- **Benchmarking modules**: Uses `load_test_texts` from `benchmark_loader.py` for inference benchmarking (consolidated from duplicate implementation in `evaluation.benchmarking`)

### Depends On

- `torch`: For PyTorch Dataset class (lazy import)
- `sklearn`: For train_test_split functionality
- Standard library: json, pathlib

## Data Format

### Dataset JSON Format

Datasets are stored as JSON files with the following structure:

**train.json / validation.json / test.json**:
```json
[
  {
    "text": "John Smith worked at Microsoft.",
    "annotations": [
      [0, 10, "PERSON"],
      [21, 30, "ORG"]
    ]
  },
  ...
]
```

- `text`: String containing the document text
- `annotations`: List of `[start_char, end_char, entity_type]` tuples
  - Character offsets are inclusive start, exclusive end (Python slice style)

### Data Configuration Format

Data configuration used by `build_label_list`:
```json
{
  "schema": {
    "entity_types": ["PERSON", "ORG", "LOCATION"]
  }
}
```

## Testing

```bash
uvx pytest tests/data/
```

## Related Modules

- [`../training/README.md`](../training/README.md) - Training workflows use data loaders
- [`../testing/README.md`](../testing/README.md) - Testing uses data loaders for validation
- [`../benchmarking/README.md`](../benchmarking/README.md) - Benchmarking uses test data loaders

