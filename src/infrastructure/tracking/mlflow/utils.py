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


def infer_config_dir_from_path(path: Optional[Path]) -> Path:
    """
    Infer config directory by searching up the parent chain from a given path.
    
    This function searches up the directory tree from the given path to find
    a parent directory that contains a "config" subdirectory. This ensures
    config directories are found correctly regardless of directory structure depth.
    
    When path is None or no config is found in the path's parent chain, it searches
    from the current working directory up to find the project root (where both
    config/ and src/ exist), ensuring correct behavior when running from notebooks
    or subdirectories.
    
    Args:
        path: Starting path to search from (e.g., output_dir, checkpoint_dir).
              If None, searches from current working directory.
    
    Returns:
        Path to config directory. Falls back to Path.cwd() / "config" if not found.
    
    Examples:
        >>> # Typical structure: /workspace/outputs/hpo/...
        >>> # Will find: /workspace/config
        >>> infer_config_dir_from_path(Path("/workspace/outputs/hpo/local/distilbert"))
        Path("/workspace/config")
        
        >>> # Deep structure: /workspace/outputs/hpo/local/distilbert/study-abc/trial-xyz
        >>> # Will still find: /workspace/config
        >>> infer_config_dir_from_path(Path("/workspace/outputs/hpo/local/distilbert/study-abc/trial-xyz"))
        Path("/workspace/config")
        
        >>> # When running from notebook: /workspace/notebooks/
        >>> # Will find: /workspace/config (by searching up from cwd)
        >>> infer_config_dir_from_path(None)
        Path("/workspace/config")
    """
    # First, try searching from the provided path
    if path is not None:
        for parent in path.parents:
            candidate = parent / "config"
            if candidate.exists():
                return candidate
    
    # If path is None or no config found in path's parent chain,
    # search from current working directory to find project root
    # (where both config/ and src/ exist)
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        candidate = parent / "config"
        if candidate.exists() and (parent / "src").exists():
            # Found project root with both config/ and src/
            return candidate
    
    # Last resort: fall back to cwd/config if not found
    return Path.cwd() / "config"

