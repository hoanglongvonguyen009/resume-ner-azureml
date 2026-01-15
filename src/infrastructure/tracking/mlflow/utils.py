from __future__ import annotations

"""
@meta
name: tracking_mlflow_utils
type: utility
domain: tracking
responsibility:
  - Provide retry logic with exponential backoff for MLflow operations
  - Handle retryable errors gracefully
inputs:
  - Functions to retry
outputs:
  - Function results or exceptions
tags:
  - utility
  - tracking
  - mlflow
  - retry
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow utility functions for retry logic."""
import os
import random
import time
from pathlib import Path
from typing import Any, Callable, Optional

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)

def retry_with_backoff(
    func: Callable,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    operation_name: str = "operation"
) -> Any:
    """
    Retry a function with exponential backoff and jitter.

    Args:
        func: Function to retry (callable that takes no arguments).
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.
        max_delay: Maximum delay in seconds.
        operation_name: Name of operation for logging.

    Returns:
        Result of func() if successful.

    Raises:
        Exception: Original exception if all retries exhausted.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()
            # Detect retryable errors
            is_retryable = any(
                code in error_str
                for code in ['429', '503', '504', 'timeout', 'connection', 'temporary', 'rate limit']
            )

            if not is_retryable or attempt == max_retries - 1:
                # Not retryable or last attempt - raise original exception
                raise

            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)  # 10% jitter
            total_delay = delay + jitter

            logger.debug(
                f"Retry {attempt + 1}/{max_retries} for {operation_name} "
                f"after {total_delay:.2f}s (error: {str(e)[:100]})"
            )
            time.sleep(total_delay)

    # Should never reach here, but just in case
    raise RuntimeError(f"Retry logic exhausted for {operation_name}")


def get_mlflow_run_id() -> Optional[str]:
    """
    Get MLflow run ID from active run or environment variable.
    
    This function checks for an active MLflow run first, then falls back
    to the MLFLOW_RUN_ID environment variable. This provides a unified
    way to detect the current run ID across different execution contexts.
    
    Returns:
        Run ID string if found, None otherwise.
    """
    try:
        import mlflow
        active_run = mlflow.active_run()
        if active_run:
            return active_run.info.run_id
    except Exception:
        pass
    return os.environ.get("MLFLOW_RUN_ID")


# Re-export infer_config_dir from paths.utils for backward compatibility
import warnings
from infrastructure.paths.utils import infer_config_dir

def infer_config_dir_from_path(path: Optional[Path]) -> Path:
    """
    Infer config directory by searching up the parent chain from a given path.
    
    **DEPRECATED**: Use `infrastructure.paths.utils.infer_config_dir()` instead.
    This function is kept for backward compatibility and re-exports the new function.
    
    Args:
        path: Starting path to search from (e.g., output_dir, checkpoint_dir).
              If None, searches from current working directory.
    
    Returns:
        Path to config directory. Falls back to Path.cwd() / "config" if not found.
    """
    warnings.warn(
        "infer_config_dir_from_path is deprecated. "
        "Please use infrastructure.paths.utils.infer_config_dir() instead. "
        "This function will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return infer_config_dir(path=path)

