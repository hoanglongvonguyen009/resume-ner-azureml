"""
@meta
name: server_launcher
type: utility
domain: deployment
responsibility:
  - Start API server programmatically
  - Check server health
  - Get server information
inputs:
  - ONNX model path
  - Checkpoint directory
  - Server configuration
outputs:
  - Running server process
  - Server health status
tags:
  - utility
  - api
  - server-management
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Utilities for starting and managing API server."""

import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

import requests

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def start_api_server(
    onnx_path: Path,
    checkpoint_dir: Path,
    host: str = "0.0.0.0",
    port: int = 8000,
    background: bool = False,
) -> Optional[subprocess.Popen]:
    """
    Start API server programmatically.
    
    Args:
        onnx_path: Path to ONNX model file
        checkpoint_dir: Path to checkpoint directory
        host: Server host (default: "0.0.0.0")
        port: Server port (default: 8000)
        background: If True, run server in background (default: False)
    
    Returns:
        subprocess.Popen object if background=True, None if background=False (foreground)
    
    Raises:
        ValueError: If paths don't exist
        RuntimeError: If server fails to start
    """
    # Validate paths
    if not onnx_path.exists():
        raise ValueError(f"ONNX model path does not exist: {onnx_path}")
    if not checkpoint_dir.exists():
        raise ValueError(f"Checkpoint directory does not exist: {checkpoint_dir}")
    
    # Build command
    cmd = [
        sys.executable,
        "-m",
        "src.deployment.api.cli.run_api",
        "--onnx-model",
        str(onnx_path),
        "--checkpoint",
        str(checkpoint_dir),
        "--host",
        host,
        "--port",
        str(port),
    ]
    
    logger.info(f"Starting API server: {' '.join(cmd)}")
    
    if background:
        # Run in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.info(f"Server started in background (PID: {process.pid})")
        return process
    else:
        # Run in foreground (blocking)
        logger.info("Starting server in foreground (blocking)...")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Server failed to start: {e}") from e
        return None


def check_server_health(
    base_url: str = "http://localhost:8000",
    timeout: int = 5,
) -> bool:
    """
    Check if server is running and healthy.
    
    Args:
        base_url: Base URL of the server (default: "http://localhost:8000")
        timeout: Request timeout in seconds (default: 5)
    
    Returns:
        True if server is healthy, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/health", timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.debug(f"Health check failed: {e}")
        return False


def get_server_info(
    base_url: str = "http://localhost:8000",
    timeout: int = 5,
) -> dict[str, Any]:
    """
    Get server information.
    
    Args:
        base_url: Base URL of the server (default: "http://localhost:8000")
        timeout: Request timeout in seconds (default: 5)
    
    Returns:
        Dictionary with server information, or empty dict if server unavailable
    """
    try:
        response = requests.get(f"{base_url}/info", timeout=timeout)
        if response.status_code == 200:
            return response.json()
        return {}
    except requests.exceptions.RequestException as e:
        logger.debug(f"Failed to get server info: {e}")
        return {}


def wait_for_server(
    base_url: str = "http://localhost:8000",
    timeout: int = 30,
    check_interval: float = 1.0,
) -> bool:
    """
    Wait for server to become available.
    
    Args:
        base_url: Base URL of the server (default: "http://localhost:8000")
        timeout: Maximum time to wait in seconds (default: 30)
        check_interval: Interval between checks in seconds (default: 1.0)
    
    Returns:
        True if server becomes available, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_server_health(base_url, timeout=2):
            return True
        time.sleep(check_interval)
    return False

