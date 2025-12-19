"""Cross-validation utilities for k-fold splitting and management."""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from sklearn.model_selection import KFold


def create_kfold_splits(
    dataset: List[Any],
    k: int = 5,
    random_seed: int = 42,
    shuffle: bool = True,
) -> List[Tuple[List[int], List[int]]]:
    """
    Create k-fold splits at document level.

    Args:
        dataset: List of dataset samples (documents).
        k: Number of folds.
        random_seed: Random seed for reproducibility.
        shuffle: Whether to shuffle data before splitting.

    Returns:
        List of (train_indices, val_indices) tuples, one per fold.
        Each tuple contains lists of indices for training and validation sets.

    Example:
        >>> splits = create_kfold_splits(dataset, k=5)
        >>> train_idx, val_idx = splits[0]
        >>> train_data = [dataset[i] for i in train_idx]
        >>> val_data = [dataset[i] for i in val_idx]
    """
    n_samples = len(dataset)
    if n_samples < k:
        raise ValueError(
            f"Cannot create {k} folds with only {n_samples} samples. "
            f"Reduce k or increase dataset size."
        )

    if shuffle:
        kf = KFold(n_splits=k, shuffle=shuffle, random_state=random_seed)
    else:
        kf = KFold(n_splits=k, shuffle=shuffle)
    indices = np.arange(n_samples)

    splits = []
    for train_idx, val_idx in kf.split(indices):
        splits.append((train_idx.tolist(), val_idx.tolist()))

    return splits


def get_fold_data(
    dataset: List[Any],
    train_indices: List[int],
    val_indices: List[int],
) -> Tuple[List[Any], List[Any]]:
    """
    Extract fold-specific data using indices.

    Args:
        dataset: Full dataset list.
        train_indices: List of training indices.
        val_indices: List of validation indices.

    Returns:
        Tuple of (train_data, val_data) lists.
    """
    train_data = [dataset[i] for i in train_indices]
    val_data = [dataset[i] for i in val_indices]
    return train_data, val_data


def save_fold_splits(
    splits: List[Tuple[List[int], List[int]]],
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save fold splits to JSON file for reproducibility.

    Args:
        splits: List of (train_indices, val_indices) tuples.
        output_path: Path to save JSON file.
        metadata: Optional metadata dictionary to include (e.g., k, random_seed).

    Example:
        >>> splits = create_kfold_splits(dataset, k=5)
        >>> save_fold_splits(splits, Path("splits.json"), {"k": 5, "random_seed": 42})
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert splits to serializable format
    splits_data = [
        {"train_indices": train_idx, "val_indices": val_idx}
        for train_idx, val_idx in splits
    ]

    data = {
        "splits": splits_data,
        "n_folds": len(splits),
        "metadata": metadata or {},
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_fold_splits(input_path: Path) -> Tuple[List[Tuple[List[int], List[int]]], Dict[str, Any]]:
    """
    Load fold splits from JSON file.

    Args:
        input_path: Path to JSON file containing saved splits.

    Returns:
        Tuple of (splits, metadata) where:
        - splits: List of (train_indices, val_indices) tuples
        - metadata: Dictionary containing metadata (k, random_seed, etc.)

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.

    Example:
        >>> splits, metadata = load_fold_splits(Path("splits.json"))
        >>> print(f"Loaded {len(splits)} folds with seed {metadata.get('random_seed')}")
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Fold splits file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "splits" not in data:
        raise ValueError(f"Invalid splits file format: missing 'splits' key")

    splits = [
        (split["train_indices"], split["val_indices"])
        for split in data["splits"]
    ]

    metadata = data.get("metadata", {})

    return splits, metadata

