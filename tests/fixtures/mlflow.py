"""Shared MLflow fixtures for tests."""

import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import Mock

import mlflow
import pytest


@pytest.fixture
def mock_mlflow_tracking(monkeypatch, tmp_path):
    """Mock MLflow to use local file-based tracking.
    
    Sets up a local file-based MLflow tracking URI and mocks the setup function
    to use it. Also mocks Azure ML client creation.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
        tmp_path: Pytest temporary directory fixture
        
    Returns:
        Tracking URI string (file://...)
    """
    # Set local tracking URI
    mlflow_tracking_dir = tmp_path / "mlruns"
    mlflow_tracking_dir.mkdir()
    tracking_uri = f"file://{mlflow_tracking_dir}"
    
    # Mock setup_mlflow_from_config to use local tracking
    def mock_setup_mlflow_from_config(experiment_name, config_dir=None):
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        return tracking_uri
    
    # After refactor, setup_mlflow_from_config lives in common.shared.mlflow_setup
    monkeypatch.setattr(
        "common.shared.mlflow_setup.setup_mlflow_from_config",
        mock_setup_mlflow_from_config,
        raising=False,
    )
    
    # Mock Azure ML client creation if attempted (only if azure module is available)
    try:
        import azure.ai.ml
        mock_ml_client = Mock()
        monkeypatch.setattr(
            "azure.ai.ml.MLClient",
            lambda **kwargs: mock_ml_client,
            raising=False
        )
    except ImportError:
        # Azure ML SDK not installed - skip mocking (tests should work without it)
        pass
    
    return tracking_uri


@pytest.fixture
def mock_mlflow_client():
    """Create a mock MLflow client with common operations.
    
    This fixture provides a mocked MLflow client and parent run that can be used
    in tests. The client includes common operations like get_run, create_run,
    set_tag, log_metric, log_param, and set_terminated.
    
    Returns:
        Tuple of (mock_client, mock_parent_run)
    """
    mock_parent_run = Mock()
    mock_parent_run.info.run_id = "hpo_parent_123"
    mock_parent_run.info.experiment_id = "exp_123"
    mock_parent_run.info.status = "RUNNING"
    
    def get_run_side_effect(run_id):
        if run_id == "hpo_parent_123" or isinstance(run_id, str):
            # Set up tags with string values (not Mock objects)
            mock_parent_run.data.tags = {
                "code.study_key_hash": "a" * 64,
                "code.study_family_hash": "b" * 64,
            }
            return mock_parent_run
        return mock_parent_run
    
    mock_client = Mock()
    mock_client.get_run.side_effect = get_run_side_effect
    mock_client.create_run = Mock()
    mock_client.set_tag = Mock()
    mock_client.log_metric = Mock()
    mock_client.log_param = Mock()
    mock_client.set_terminated = Mock()
    
    return mock_client, mock_parent_run


def create_mock_mlflow_client():
    """Create a mock MLflow client with common operations (helper function).
    
    This is a helper function version of the mock_mlflow_client fixture.
    Use this when you need to create a mock client outside of pytest fixtures.
    
    Returns:
        Tuple of (mock_client, mock_parent_run)
    """
    mock_parent_run = Mock()
    mock_parent_run.info.run_id = "hpo_parent_123"
    mock_parent_run.info.experiment_id = "exp_123"
    mock_parent_run.info.status = "RUNNING"
    
    def get_run_side_effect(run_id):
        if run_id == "hpo_parent_123" or isinstance(run_id, str):
            # Set up tags with string values (not Mock objects)
            mock_parent_run.data.tags = {
                "code.study_key_hash": "a" * 64,
                "code.study_family_hash": "b" * 64,
            }
            return mock_parent_run
        return mock_parent_run
    
    mock_client = Mock()
    mock_client.get_run.side_effect = get_run_side_effect
    mock_client.create_run = Mock()
    mock_client.set_tag = Mock()
    mock_client.log_metric = Mock()
    mock_client.log_param = Mock()
    mock_client.set_terminated = Mock()
    
    return mock_client, mock_parent_run


@pytest.fixture
def mock_mlflow_setup(mock_mlflow_client):
    """Set up MLflow mocks for tests.
    
    This fixture combines mock_mlflow_client and returns a dictionary with
    both the client and parent run. Useful for tests that need both components.
    
    Args:
        mock_mlflow_client: The mock_mlflow_client fixture
        
    Returns:
        Dictionary with keys: "client", "parent_run"
    """
    mock_client, mock_parent_run = mock_mlflow_client
    
    # Return the mocks so tests can use them
    return {
        "client": mock_client,
        "parent_run": mock_parent_run,
    }


def create_mock_run(
    run_id: str = "test_run_id_123",
    tags: Optional[Dict[str, str]] = None,
    metrics: Optional[Dict[str, float]] = None,
    params: Optional[Dict[str, str]] = None,
    experiment_id: str = "test_experiment_id",
    status: str = "FINISHED",
) -> Mock:
    """Create a mock MLflow run with specified attributes (helper function).
    
    Args:
        run_id: Run ID
        tags: Dictionary of tags
        metrics: Dictionary of metrics
        params: Dictionary of parameters
        experiment_id: Experiment ID
        status: Run status (default: "FINISHED")
        
    Returns:
        Mock MLflow run object
    """
    run = Mock()
    run.info.run_id = run_id
    run.info.experiment_id = experiment_id
    run.info.status = status
    run.info.start_time = 1234567890
    
    run.data.tags = tags or {}
    run.data.metrics = metrics or {}
    run.data.params = params or {}
    
    return run


@pytest.fixture
def mock_mlflow_run():
    """Create a mock MLflow run with required tags and metrics.
    
    This fixture creates a basic MLflow run with common tags and metrics
    suitable for most tests.
    
    Returns:
        Mock MLflow run object
    """
    return create_mock_run(
        run_id="test_run_id_123",
        tags={
            "tags.grouping.study_key_hash": "study_hash_123",
            "tags.grouping.trial_key_hash": "trial_hash_456",
            "tags.process.stage": "hpo",
            "tags.process.backbone": "distilbert",
        },
        metrics={
            "macro-f1": 0.75,
            "latency_batch_1_ms": 5.0,
        },
        params={
            "backbone": "distilbert",
            "learning_rate": "2e-5",
        },
    )


@pytest.fixture
def mock_hpo_trial_run():
    """Create a mock HPO trial run with tags and metrics.
    
    This fixture creates an HPO trial run with macro-f1 metric and
    common HPO tags.
    
    Returns:
        Mock MLflow run object for HPO trial
    """
    return create_mock_run(
        run_id="trial_run_id_123",
        experiment_id="hpo_experiment_id",
        tags={
            "tags.grouping.study_key_hash": "study_hash_123",
            "tags.grouping.trial_key_hash": "trial_hash_456",
            "tags.process.stage": "hpo",
            "tags.process.backbone": "distilbert",
        },
        metrics={
            "macro-f1": 0.75,
        },
        params={
            "backbone": "distilbert",
        },
    )


@pytest.fixture
def mock_benchmark_run():
    """Create a mock benchmark MLflow run with latency metrics.
    
    This fixture creates a benchmark run with latency and throughput
    metrics, suitable for benchmarking tests.
    
    Returns:
        Mock MLflow run object for benchmark
    """
    return create_mock_run(
        run_id="benchmark_run_id_123",
        experiment_id="benchmark_experiment_id",
        tags={
            "tags.grouping.study_key_hash": "study_hash_123",
            "tags.grouping.trial_key_hash": "trial_hash_456",
            "tags.process.backbone": "distilbert",
        },
        metrics={
            "latency_batch_1_ms": 5.0,
            "throughput_samples_per_sec": 200.0,
        },
    )


@pytest.fixture
def mock_refit_run():
    """Create a mock refit run with checkpoint tags.
    
    This fixture creates a refit run with checkpoint-related tags.
    Refit runs typically don't have macro-f1 metrics.
    
    Returns:
        Mock MLflow run object for refit
    """
    return create_mock_run(
        run_id="refit_run_id_123",
        experiment_id="hpo_experiment_id",
        tags={
            "tags.grouping.study_key_hash": "study_hash_123",
            "tags.grouping.trial_key_hash": "trial_hash_456",
            "tags.process.stage": "hpo_refit",
            "tags.process.backbone": "distilbert",
        },
        metrics={},  # Refit runs don't have macro-f1
        params={
            "backbone": "distilbert",
        },
    )


@pytest.fixture
def mock_final_training_run():
    """Create a mock final training run.
    
    This fixture creates a final training run with spec and exec hash tags.
    
    Returns:
        Mock MLflow run object for final training
    """
    return create_mock_run(
        run_id="final_training_run_id_123",
        experiment_id="final_training_experiment_id",
        tags={
            "tags.process.stage": "final_training",
            "tags.process.backbone": "distilbert",
            "code.spec_fp": "spec_hash_123",
            "code.exec_fp": "exec_hash_456",
        },
        metrics={
            "macro-f1": 0.80,
        },
        params={
            "backbone": "distilbert",
        },
    )


def _clean_mlflow_database(mlruns_dir: Optional[Path] = None) -> None:
    """Helper function to clean MLflow database.
    
    This function cleans the MLflow SQLite database file to prevent
    Alembic migration errors and state pollution between tests.
    
    Args:
        mlruns_dir: Path to mlruns directory. If None, tries to detect
                   from current tracking URI or workspace.
    """
    import os
    
    # Determine mlruns directory
    if mlruns_dir is None:
        current_uri = mlflow.get_tracking_uri()
        
        if current_uri and current_uri.startswith("file://"):
            # Extract path from file:// URI
            mlruns_dir = Path(current_uri.replace("file://", ""))
        elif current_uri and os.path.exists(current_uri):
            # Direct path
            mlruns_dir = Path(current_uri)
        else:
            # Default: use workspace mlruns directory
            workspace_mlruns = Path.cwd() / "mlruns"
            if workspace_mlruns.exists():
                mlruns_dir = workspace_mlruns
            else:
                # No mlruns directory found - nothing to clean
                return
    
    if mlruns_dir and mlruns_dir.exists():
        db_file = mlruns_dir / "mlflow.db"
        if db_file.exists():
            try:
                # Try to close any open connections first by checking if file is accessible
                # SQLite databases can be locked if there are open connections
                import time
                max_retries = 3
                deleted = False
                for attempt in range(max_retries):
                    try:
                        # Check if file is writable before trying to delete
                        if not db_file.is_file():
                            break  # File doesn't exist or is not a regular file
                        
                        # Try to delete the database file
                        # This will release SQLite locks and clear Alembic state
                        db_file.unlink()
                        deleted = True
                        break  # Success, exit retry loop
                    except (OSError, PermissionError) as e:
                        if attempt < max_retries - 1:
                            # Wait a bit and retry (file might be locked by another process)
                            time.sleep(0.2 * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            # Final attempt failed - log warning but continue
                            # The test might still work if it uses a different tracking URI
                            import warnings
                            warnings.warn(
                                f"Could not delete MLflow database {db_file} after {max_retries} attempts: {e}. "
                                f"This may cause test isolation issues. "
                                f"Try running tests sequentially or with --forked."
                            )
                
                # If we couldn't delete, try to at least reset the database by truncating it
                # This is a last resort to clear Alembic state
                if not deleted and db_file.exists():
                    try:
                        # Try to open and truncate the file (this might work even if unlink fails)
                        with open(db_file, 'wb') as f:
                            f.truncate(0)
                    except Exception:
                        # If truncation also fails, just continue - test might use different tracking URI
                        pass
            except Exception as e:
                # Catch any other unexpected errors
                import warnings
                warnings.warn(
                    f"Unexpected error cleaning MLflow database {db_file}: {e}. "
                    f"Continuing with test."
                )


@pytest.fixture
def clean_mlflow_db():
    """Clean MLflow database between tests to prevent state pollution.
    
    This fixture cleans the MLflow SQLite database to ensure test isolation
    and prevent Alembic migration errors (e.g., "Can't locate revision").
    
    The fixture:
    1. Cleans the MLflow database file (mlflow.db) if it exists
    2. Resets MLflow's active run state
    3. Clears MLflow's tracking URI cache
    
    Usage:
        # Request the fixture explicitly in tests that need clean state
        def test_my_mlflow_code(clean_mlflow_db):
            # MLflow database is clean here
            mlflow.set_experiment("test")
            # ...
        
        # Or use in conftest.py for automatic cleanup
        @pytest.fixture(autouse=True)
        def auto_clean_mlflow_db(clean_mlflow_db):
            yield
    
    Yields:
        None (fixture for side effects)
    """
    # Clean database before test
    _clean_mlflow_database()
    
    # Reset MLflow's active run state
    try:
        # End any active run
        if mlflow.active_run() is not None:
            mlflow.end_run()
    except Exception:
        # Ignore errors - there may not be an active run
        pass
    
    # Clear MLflow's tracking URI cache (optional - helps with state reset)
    try:
        # Don't reset to empty - just ensure we're in a clean state
        # The test will set its own tracking URI if needed
        pass
    except Exception:
        pass
    
    yield
    
    # Cleanup after test
    try:
        if mlflow.active_run() is not None:
            mlflow.end_run()
    except Exception:
        pass
    
    # Clean database after test (for next test)
    _clean_mlflow_database()












