"""MLflow client utilities.

Centralized MLflow client creation with error handling.
"""

from typing import Optional

from mlflow.tracking import MlflowClient

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def get_mlflow_client() -> Optional[MlflowClient]:
    """
    Get MLflow client instance with error handling.
    
    Returns:
        MlflowClient instance or None if creation fails.
    """
    try:
        from mlflow.tracking import MlflowClient
        return MlflowClient()
    except Exception as e:
        logger.warning(f"Could not create MLflow client: {e}")
        return None


def create_mlflow_client() -> MlflowClient:
    """
    Create MLflow client instance (raises exception on failure).
    
    Returns:
        MlflowClient instance.
        
    Raises:
        Exception: If client creation fails.
    """
    from mlflow.tracking import MlflowClient
    return MlflowClient()

