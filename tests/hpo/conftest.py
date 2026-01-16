"""Shared pytest fixtures for HPO integration tests."""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, Any

# Import shared fixtures
_fixtures_path = Path(__file__).parent.parent / "fixtures"
sys.path.insert(0, str(_fixtures_path.parent))
from fixtures import tiny_dataset as shared_tiny_dataset
from fixtures.configs import hpo_config_smoke, hpo_config_minimal
from fixtures.mlflow import mock_mlflow_client, mock_mlflow_setup
from fixtures.config_dirs import config_dir


# Use shared config_dir fixture from fixtures.config_dirs
# Alias for backward compatibility
tmp_config_dir = config_dir


@pytest.fixture
def tmp_project_structure(tmp_path, config_dir):
    """Create temporary project structure with src/training module."""
    # Create src/training module structure (required for trial execution)
    src_dir = tmp_path / "src" / "training"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("# Training module")
    
    return tmp_path


# Use shared tiny_dataset fixture
tiny_dataset = shared_tiny_dataset


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory for HPO."""
    output_dir = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
    output_dir.mkdir(parents=True)
    return output_dir


# Use shared MLflow fixtures from fixtures.mlflow
# mock_mlflow_client and mock_mlflow_setup are imported above


# Use shared HPO config fixtures from fixtures.configs
# hpo_config_smoke and hpo_config_minimal are imported above


@pytest.fixture
def train_config_minimal():
    """Minimal training config for HPO tests."""
    return {"training": {"epochs": 1}}


@pytest.fixture
def data_config_minimal():
    """Minimal data config for HPO tests."""
    return {"dataset_name": "test_data", "dataset_version": "v1"}


@pytest.fixture
def mock_training_subprocess(tmp_output_dir):
    """Mock training subprocess to return success and create metrics.json."""
    from common.constants import METRICS_FILENAME
    
    def subprocess_side_effect(*args, **kwargs):
        # Extract output_dir from environment variable (AZURE_ML_OUTPUT_CHECKPOINT)
        output_path = None
        if "env" in kwargs:
            env = kwargs["env"]
            if "AZURE_ML_OUTPUT_CHECKPOINT" in env:
                output_path = Path(env["AZURE_ML_OUTPUT_CHECKPOINT"])
            elif "AZURE_ML_OUTPUT_checkpoint" in env:
                output_path = Path(env["AZURE_ML_OUTPUT_checkpoint"])
        
        # Fallback: try to extract from command args
        if not output_path:
            cmd = args[0] if args else []
            for i, arg in enumerate(cmd):
                if isinstance(arg, str) and arg == "--output-dir" and i + 1 < len(cmd):
                    output_path = Path(cmd[i + 1])
                    break
        
        # If we found an output path, create metrics there
        if output_path:
            output_path.mkdir(parents=True, exist_ok=True)
            metrics_file = output_path / METRICS_FILENAME
            metrics_file.write_text(json.dumps({"macro-f1": 0.75}))
        
        # Also proactively create metrics in any existing CV fold folders
        study_folders = list(tmp_output_dir.glob("study-*"))
        for study_folder in study_folders:
            for trial_folder in study_folder.glob("trial-*"):
                cv_folder = trial_folder / "cv"
                if cv_folder.exists():
                    for fold_folder in cv_folder.glob("fold*"):
                        fold_folder.mkdir(parents=True, exist_ok=True)
                        metrics_file = fold_folder / METRICS_FILENAME
                        if not metrics_file.exists():
                            metrics_file.write_text(json.dumps({"macro-f1": 0.75}))
                else:
                    trial_folder.mkdir(parents=True, exist_ok=True)
                    metrics_file = trial_folder / METRICS_FILENAME
                    if not metrics_file.exists():
                        metrics_file.write_text(json.dumps({"macro-f1": 0.75}))
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Training completed"
        mock_result.stderr = ""
        return mock_result
    
    return subprocess_side_effect



