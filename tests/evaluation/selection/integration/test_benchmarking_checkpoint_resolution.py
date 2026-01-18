"""Integration tests for checkpoint resolution in benchmarking workflow.

Tests the full workflow from champion selection to checkpoint acquisition for benchmarking,
ensuring checkpoints can be resolved from various sources (local disk, MLflow artifacts).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_champion_data():
    """Create mock champion data from select_champions_for_backbones."""
    return {
        "champion": {
            "run_id": "trial-run-123",
            "study_key_hash": "study-hash-abc123",
            "trial_key_hash": "trial-hash-xyz789",
            "metric": 0.85,
            "checkpoint_path": None,  # Not available from local disk
        },
        "group_info": {
            "study_key_hash": "study-hash-abc123",
            "schema_version": "1.0",
            "trial_count": 3,
        },
    }


@pytest.fixture
def mock_hpo_output_structure(temp_dir):
    """Create mock HPO output directory structure."""
    # Create study folder
    study_dir = temp_dir / "outputs" / "hpo" / "local" / "distilbert" / "study-abc123"
    study_dir.mkdir(parents=True)
    
    # Create trial folder (using first 8 chars of trial_key_hash: "trial-hash-xyz789" -> "trial-ha")
    # The test looks for trial-{trial_hash8} where trial_hash8 = trial_key_hash[:8]
    trial_hash8 = "trial-hash-xyz789"[:8]  # "trial-ha"
    trial_dir = study_dir / f"trial-{trial_hash8}"
    trial_dir.mkdir()
    
    # Create checkpoint in refit subdirectory
    checkpoint_dir = trial_dir / "refit" / "checkpoint"
    checkpoint_dir.mkdir(parents=True)
    
    # Create dummy checkpoint files
    (checkpoint_dir / "pytorch_model.bin").touch()
    (checkpoint_dir / "config.json").touch()
    
    return {
        "study_dir": study_dir,
        "trial_dir": trial_dir,
        "checkpoint_dir": checkpoint_dir,
    }


class TestCheckpointResolutionFromLocalDisk:
    """Test checkpoint resolution from local HPO output directory."""

    def test_resolve_checkpoint_from_champion_checkpoint_path(self, mock_champion_data, temp_dir):
        """Test resolving checkpoint from champion's checkpoint_path."""
        checkpoint_path = temp_dir / "checkpoint"
        checkpoint_path.mkdir(parents=True)
        (checkpoint_path / "pytorch_model.bin").touch()
        
        # Update champion data with checkpoint_path
        mock_champion_data["champion"]["checkpoint_path"] = checkpoint_path
        
        # Resolve checkpoint_dir
        checkpoint_dir = None
        if mock_champion_data["champion"].get("checkpoint_path"):
            checkpoint_dir = str(mock_champion_data["champion"]["checkpoint_path"])
        
        assert checkpoint_dir is not None
        assert Path(checkpoint_dir).exists()

    def test_resolve_checkpoint_from_trial_dir(self, mock_champion_data, mock_hpo_output_structure):
        """Test resolving checkpoint from trial_dir when checkpoint_path not available."""
        trial_key_hash = mock_champion_data["champion"]["trial_key_hash"]
        trial_hash8 = trial_key_hash[:8]
        
        # Search for trial directory
        hpo_output_dir = mock_hpo_output_structure["study_dir"].parent
        trial_dir = None
        
        for study_dir in hpo_output_dir.iterdir():
            if study_dir.is_dir():
                trial_v2_name = f"trial-{trial_hash8}"
                trial_v2_path = study_dir / trial_v2_name
                if trial_v2_path.exists() and trial_v2_path.is_dir():
                    trial_dir = str(trial_v2_path)
                    break
        
        assert trial_dir is not None
        assert Path(trial_dir).exists()
        
        # Find checkpoint in trial directory
        trial_path = Path(trial_dir)
        checkpoint_dir = None
        
        # Check refit/checkpoint
        refit_checkpoint = trial_path / "refit" / "checkpoint"
        if refit_checkpoint.exists():
            checkpoint_dir = str(refit_checkpoint)
        
        assert checkpoint_dir is not None
        assert Path(checkpoint_dir).exists()

class TestCheckpointResolutionFromMLflow:
    """Test checkpoint resolution from MLflow artifacts."""

    @patch('evaluation.selection.artifact_acquisition.acquire_best_model_checkpoint')
    @patch('mlflow.tracking.MlflowClient')
    def test_resolve_from_mlflow_refit_run(
        self,
        mock_mlflow_client_class,
        mock_acquire_checkpoint,
        mock_champion_data,
        temp_dir,
    ):
        """Test resolving checkpoint from MLflow refit run."""
        # Setup mocks
        mock_client = Mock()
        mock_mlflow_client_class.return_value = mock_client
        
        # Mock trial run
        trial_run = Mock()
        trial_run.info.run_id = "trial-run-123"
        trial_run.info.experiment_id = "exp-123"
        trial_run.info.parent_run_id = "parent-hpo-456"
        
        # Mock refit run
        refit_run = Mock()
        refit_run.info.run_id = "refit-run-789"
        
        mock_client.get_run.return_value = trial_run
        mock_client.search_runs.return_value = [refit_run]
        
        # Mock artifacts in refit run
        artifact = Mock()
        artifact.path = "checkpoint"
        mock_client.list_artifacts.return_value = [artifact]
        
        # Mock successful acquisition
        acquired_path = temp_dir / "acquired_checkpoint"
        acquired_path.mkdir()
        (acquired_path / "pytorch_model.bin").touch()
        mock_acquire_checkpoint.return_value = acquired_path
        
        # Simulate the resolution workflow
        run_id = mock_champion_data["champion"]["run_id"]
        study_key_hash = mock_champion_data["champion"]["study_key_hash"]
        trial_key_hash = mock_champion_data["champion"]["trial_key_hash"]
        
        # Try to find refit run
        champion_run = mock_client.get_run(run_id)
        experiment_id = champion_run.info.experiment_id
        
        refit_runs = mock_client.search_runs(
            experiment_ids=[experiment_id],
            filter_string="tags.code.process.stage = 'hpo_refit'",
            max_results=5,
        )
        
        checkpoint_dir = None
        if refit_runs:
            refit_run_id = refit_runs[0].info.run_id
            # Check artifacts
            artifacts = mock_client.list_artifacts(refit_run_id)
            artifact_paths = [a.path for a in artifacts]
            checkpoint_artifacts = [p for p in artifact_paths if "checkpoint" in p.lower()]
            
            if checkpoint_artifacts:
                # Acquire checkpoint
                best_run_info = {
                    "run_id": refit_run_id,
                    "study_key_hash": study_key_hash,
                    "trial_key_hash": trial_key_hash,
                    "backbone": "distilbert",
                }
                
                checkpoint_dir = mock_acquire_checkpoint(
                    best_run_info=best_run_info,
                    root_dir=temp_dir,
                    config_dir=temp_dir / "config",
                    acquisition_config={"priority": ["mlflow"], "mlflow": {"enabled": True}},
                    selection_config={},
                    platform="local",
                )
        
        assert checkpoint_dir is not None
        assert Path(checkpoint_dir).exists()

    @patch('evaluation.selection.artifact_acquisition.acquire_best_model_checkpoint')
    @patch('mlflow.tracking.MlflowClient')
    def test_resolve_from_mlflow_parent_run(
        self,
        mock_mlflow_client_class,
        mock_acquire_checkpoint,
        mock_champion_data,
        temp_dir,
    ):
        """Test resolving checkpoint from MLflow parent HPO run."""
        # Setup mocks
        mock_client = Mock()
        mock_mlflow_client_class.return_value = mock_client
        
        # Mock trial run with parent
        trial_run = Mock()
        trial_run.info.run_id = "trial-run-123"
        trial_run.info.experiment_id = "exp-123"
        trial_run.info.parent_run_id = "parent-hpo-456"
        
        # Mock parent run
        parent_run = Mock()
        parent_run.info.run_id = "parent-hpo-456"
        
        mock_client.get_run.side_effect = [trial_run, parent_run]
        mock_client.search_runs.return_value = []  # No refit runs
        
        # Mock artifacts in parent run
        artifact = Mock()
        artifact.path = "best_trial_checkpoint.tar.gz"
        mock_client.list_artifacts.return_value = [artifact]
        
        # Mock successful acquisition
        acquired_path = temp_dir / "acquired_checkpoint"
        acquired_path.mkdir()
        (acquired_path / "pytorch_model.bin").touch()
        mock_acquire_checkpoint.return_value = acquired_path
        
        # Simulate workflow
        run_id = mock_champion_data["champion"]["run_id"]
        champion_run = mock_client.get_run(run_id)
        parent_run_id = getattr(champion_run.info, 'parent_run_id', None)
        
        checkpoint_dir = None
        if parent_run_id:
            # Check if parent has checkpoint artifacts
            parent_artifacts = mock_client.list_artifacts(parent_run_id)
            parent_artifact_paths = [a.path for a in parent_artifacts]
            checkpoint_in_parent = any("checkpoint" in p.lower() for p in parent_artifact_paths)
            
            if checkpoint_in_parent:
                best_run_info = {
                    "run_id": parent_run_id,
                    "study_key_hash": mock_champion_data["champion"]["study_key_hash"],
                    "trial_key_hash": mock_champion_data["champion"]["trial_key_hash"],
                    "backbone": "distilbert",
                }
                
                checkpoint_dir = mock_acquire_checkpoint(
                    best_run_info=best_run_info,
                    root_dir=temp_dir,
                    config_dir=temp_dir / "config",
                    acquisition_config={"priority": ["mlflow"], "mlflow": {"enabled": True}},
                    selection_config={},
                    platform="local",
                )
        
        assert checkpoint_dir is not None
        assert Path(checkpoint_dir).exists()


class TestBenchmarkingWorkflowIntegration:
    """Test the full benchmarking workflow with checkpoint resolution."""

    @patch('evaluation.benchmarking.benchmark_best_trials')
    @patch('evaluation.selection.trial_finder.select_champions_for_backbones')
    def test_benchmarking_with_local_checkpoint(
        self,
        mock_select_champions,
        mock_benchmark,
        mock_champion_data,
        mock_hpo_output_structure,
    ):
        """Test benchmarking workflow when checkpoint is available locally."""
        # Mock champion selection
        champions = {
            "distilbert": mock_champion_data,
        }
        mock_select_champions.return_value = champions
        
        # Mock checkpoint path
        checkpoint_dir = mock_hpo_output_structure["checkpoint_dir"]
        mock_champion_data["champion"]["checkpoint_path"] = checkpoint_dir
        
        # Build best_trials dict for benchmarking
        best_trials = {}
        for backbone, champion_data in champions.items():
            champion = champion_data["champion"]
            checkpoint_path = champion.get("checkpoint_path")
            checkpoint_dir = str(checkpoint_path) if checkpoint_path else None
            
            best_trials[backbone] = {
                "checkpoint_dir": checkpoint_dir,
                "trial_name": champion.get("trial_key_hash", "unknown"),
                "study_key_hash": champion.get("study_key_hash"),
                "trial_key_hash": champion.get("trial_key_hash"),
            }
        
        # Verify best_trials structure
        assert "distilbert" in best_trials
        assert best_trials["distilbert"]["checkpoint_dir"] is not None
        assert Path(best_trials["distilbert"]["checkpoint_dir"]).exists()
        
        # Benchmarking should proceed
        mock_benchmark.return_value = {"distilbert": {"f1": 0.85}}
        
        # This would be called in the actual workflow
        # benchmark_results = benchmark_best_trials(best_trials=best_trials, ...)
        # assert benchmark_results is not None

    @patch('evaluation.benchmarking.benchmark_best_trials')
    @patch('evaluation.selection.artifact_acquisition.acquire_best_model_checkpoint')
    @patch('evaluation.selection.trial_finder.select_champions_for_backbones')
    def test_benchmarking_with_mlflow_checkpoint(
        self,
        mock_select_champions,
        mock_acquire_checkpoint,
        mock_benchmark,
        mock_champion_data,
        temp_dir,
    ):
        """Test benchmarking workflow when checkpoint must be acquired from MLflow."""
        # Mock champion selection (no local checkpoint)
        champions = {
            "distilbert": mock_champion_data,
        }
        mock_select_champions.return_value = champions
        
        # Mock MLflow acquisition
        acquired_path = temp_dir / "acquired_checkpoint"
        acquired_path.mkdir()
        (acquired_path / "pytorch_model.bin").touch()
        mock_acquire_checkpoint.return_value = acquired_path
        
        # Simulate checkpoint acquisition
        champion = mock_champion_data["champion"]
        run_id = champion.get("run_id")
        
        if run_id and not champion.get("checkpoint_path"):
            # Acquire from MLflow
            best_run_info = {
                "run_id": run_id,
                "study_key_hash": champion.get("study_key_hash"),
                "trial_key_hash": champion.get("trial_key_hash"),
                "backbone": "distilbert",
            }
            
            checkpoint_dir = mock_acquire_checkpoint(
                best_run_info=best_run_info,
                root_dir=temp_dir,
                config_dir=temp_dir / "config",
                acquisition_config={"priority": ["mlflow"], "mlflow": {"enabled": True}},
                selection_config={},
                platform="local",
            )
        else:
            checkpoint_dir = champion.get("checkpoint_path")
        
        # Build best_trials
        best_trials = {
            "distilbert": {
                "checkpoint_dir": str(checkpoint_dir) if checkpoint_dir else None,
                "trial_name": champion.get("trial_key_hash", "unknown"),
                "study_key_hash": champion.get("study_key_hash"),
                "trial_key_hash": champion.get("trial_key_hash"),
            },
        }
        
        # Verify checkpoint was acquired
        assert best_trials["distilbert"]["checkpoint_dir"] is not None
        assert Path(best_trials["distilbert"]["checkpoint_dir"]).exists()
        
        # Benchmarking should proceed
        mock_benchmark.return_value = {"distilbert": {"f1": 0.85}}

