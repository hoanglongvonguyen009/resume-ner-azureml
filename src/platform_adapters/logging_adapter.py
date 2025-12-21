"""Logging adapters for different platforms."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class LoggingAdapter(ABC):
    """Abstract interface for platform-specific logging."""

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Log metrics to platform-specific logging system.

        Args:
            metrics: Dictionary of metric names to values.
        """
        pass

    @abstractmethod
    def log_params(self, params: Dict[str, Any]) -> None:
        """
        Log parameters to platform-specific logging system.

        Args:
            params: Dictionary of parameter names to values.
        """
        pass


class AzureMLLoggingAdapter(LoggingAdapter):
    """Logging adapter for Azure ML jobs."""

    def __init__(self):
        """Initialize Azure ML logging adapter."""
        self._azureml_run = None
        self._try_init_azureml()

    def _try_init_azureml(self) -> None:
        """Try to initialize Azure ML run context."""
        try:
            from azureml.core import Run
            self._azureml_run = Run.get_context()
        except Exception:
            # Azure ML not available (e.g., running locally)
            self._azureml_run = None

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        """Log metrics to both MLflow and Azure ML native logging."""
        import mlflow
        # Only log scalar metrics (skip nested dictionaries like 'per_entity')
        for k, v in metrics.items():
            if isinstance(v, (int, float, str, bool)):
                mlflow.log_metric(k, v)
            # Skip nested dictionaries - they're saved in metrics.json but not logged to MLflow

        # Also log to Azure ML native logging if available
        if self._azureml_run is not None:
            for k, v in metrics.items():
                if isinstance(v, (int, float, str, bool)):
                    self._azureml_run.log(k, v)

    def log_params(self, params: Dict[str, Any]) -> None:
        """Log parameters to both MLflow and Azure ML native logging."""
        import mlflow
        mlflow.log_params(params)

        # Azure ML native logging doesn't have a direct params equivalent,
        # but we can log them as metrics with a prefix if needed
        if self._azureml_run is not None:
            for k, v in params.items():
                if isinstance(v, (int, float, str, bool)):
                    self._azureml_run.log(f"param_{k}", v)


class LocalLoggingAdapter(LoggingAdapter):
    """Logging adapter for local execution."""

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        """Log metrics to MLflow only."""
        import mlflow
        # Only log scalar metrics (skip nested dictionaries like 'per_entity')
        for k, v in metrics.items():
            if isinstance(v, (int, float, str, bool)):
                mlflow.log_metric(k, v)
            # Skip nested dictionaries - they're saved in metrics.json but not logged to MLflow

    def log_params(self, params: Dict[str, Any]) -> None:
        """Log parameters to MLflow only."""
        import mlflow
        mlflow.log_params(params)
