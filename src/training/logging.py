"""Metric logging utilities."""

import json
from pathlib import Path
from typing import Dict

import mlflow

# Azure ML logging (works alongside MLflow)
try:
    from azureml.core import Run
    _azureml_run = Run.get_context()
    _azureml_available = True
except Exception:
    _azureml_run = None
    _azureml_available = False


def log_metrics(output_dir: Path, metrics: Dict[str, float]) -> None:
    """
    Write metrics to file and log to MLflow and Azure ML.

    Args:
        output_dir: Directory to write metrics file.
        metrics: Dictionary of metric names to values.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f)
    
    _log_to_mlflow(metrics)
    _log_to_azureml(metrics)


def _log_to_mlflow(metrics: Dict[str, float]) -> None:
    """Log metrics to MLflow."""
    for k, v in metrics.items():
        mlflow.log_metric(k, v)


def _log_to_azureml(metrics: Dict[str, float]) -> None:
    """Log metrics to Azure ML native logging."""
    if _azureml_available and _azureml_run is not None:
        for k, v in metrics.items():
            _azureml_run.log(k, v)

