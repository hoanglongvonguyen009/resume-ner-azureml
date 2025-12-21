"""MLflow utility functions for experiment tracking."""

from __future__ import annotations

from typing import Optional

import mlflow


def setup_mlflow_for_stage(
    experiment_name: str,
    tracking_uri: Optional[str] = None
) -> None:
    """Setup MLflow tracking for a specific stage.

    Args:
        experiment_name: MLflow experiment name.
        tracking_uri: Optional tracking URI (uses default if None).
    """
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

