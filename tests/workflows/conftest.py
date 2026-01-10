"""Shared pytest fixtures for workflow E2E tests."""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

# Add fixtures to path
_fixtures_path = Path(__file__).parent.parent / "fixtures"
sys.path.insert(0, str(_fixtures_path.parent))

# Import shared fixtures
from fixtures import (
    tiny_dataset,
    mock_mlflow_tracking,
    validate_path_structure,
    validate_run_name,
    validate_tags,
)


@pytest.fixture
def mock_mlflow(monkeypatch):
    """Mock mlflow module for tests."""
    mock_mlflow_module = MagicMock()
    monkeypatch.setattr("mlflow", mock_mlflow_module, raising=False)
    return mock_mlflow_module


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess execution for tests.
    
    Returns a Mock object that can be configured with side_effect.
    Patches subprocess.run so tests can control its behavior.
    """
    mock_run = Mock()
    
    # Patch subprocess.run
    monkeypatch.setattr("subprocess.run", mock_run, raising=False)
    
    # Return the mock so tests can set mock_subprocess.side_effect
    # This will control what subprocess.run returns
    return mock_run


# Re-export for convenience
__all__ = [
    "tiny_dataset",
    "mock_mlflow_tracking",
    "mock_mlflow",
    "mock_subprocess",
    "validate_path_structure",
    "validate_run_name",
    "validate_tags",
]








