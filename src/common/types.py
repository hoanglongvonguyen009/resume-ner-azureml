from __future__ import annotations

"""Shared type definitions for the codebase.

This module provides Protocol types for MLflow objects and TypedDict types
for common configuration patterns to improve type safety across the codebase.
"""

from typing import Protocol, TypedDict, Optional, Dict, Any


# MLflow Run Types (Protocol-based for structural typing)

class MLflowRunInfo(Protocol):
    """Protocol for MLflow RunInfo object."""
    run_id: str
    experiment_id: str
    status: str
    start_time: int
    end_time: Optional[int]


class MLflowRunData(Protocol):
    """Protocol for MLflow RunData object."""
    tags: Dict[str, str]
    metrics: Dict[str, float]
    params: Dict[str, str]


class MLflowRun(Protocol):
    """Protocol for MLflow Run object."""
    info: MLflowRunInfo
    data: MLflowRunData


# Config Dictionary Types

class HPOConfigDict(TypedDict, total=False):
    """HPO configuration dictionary structure."""
    n_trials: int
    timeout: Optional[int]
    study_name: Optional[str]
    pruner: Optional[str]
    cleanup: Dict[str, Any]
    # Add other common HPO config fields as needed


class TrainingConfigDict(TypedDict, total=False):
    """Training configuration dictionary structure."""
    batch_size: int
    learning_rate: float
    epochs: int
    # Add other common training config fields as needed


class DataConfigDict(TypedDict, total=False):
    """Data configuration dictionary structure."""
    train_split: float
    val_split: float
    test_split: Optional[float]
    # Add other common data config fields as needed


class BenchmarkConfigDict(TypedDict, total=False):
    """Benchmark configuration dictionary structure."""
    dataset_path: str
    batch_size: int
    # Add other common benchmark config fields as needed

