"""Tests for sweep tracker config directory inference.

Tests that verify config_dir is correctly inferred from output_dir paths,
preventing issues like looking for config in outputs/config/ instead of config/.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from infrastructure.tracking.mlflow.trackers.sweep_tracker import MLflowSweepTracker


def _make_mlflow_run(*, run_id: str, experiment_id: str = "exp-1", tags: dict[str, str] | None = None) -> MagicMock:
    run = MagicMock()
    run.info.run_id = run_id
    run.info.experiment_id = experiment_id
    run.info.run_name = f"run-{run_id}"
    run.data.tags = tags or {}
    return run


@pytest.fixture
def root_dir_with_config(tmp_path: Path) -> Path:
    """Create a root directory with config/ and src/ directories (required for repo root validation)."""
    root = tmp_path / "workspace"
    root.mkdir()
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "tags.yaml").write_text("schema_version: 1")
    src_dir = root / "src"
    src_dir.mkdir()  # Required for repository root validation
    return root


@pytest.fixture
def output_dir_structure(root_dir_with_config: Path) -> Path:
    """Create a typical output directory structure."""
    outputs = root_dir_with_config / "outputs"
    outputs.mkdir()
    hpo_dir = outputs / "hpo" / "local" / "distilbert"
    hpo_dir.mkdir(parents=True)
    return hpo_dir


class TestSweepTrackerConfigInference:
    """Test config_dir inference in sweep tracker methods."""

    def test_log_best_trial_id_infers_config_from_output_dir(
        self, root_dir_with_config: Path, output_dir_structure: Path
    ):
        """Test that _log_best_trial_id correctly infers config_dir from output_dir."""
        tracker = MLflowSweepTracker(experiment_name="test")
        
        # Create a mock study with best trial
        mock_study = Mock()
        mock_trial = Mock()
        mock_trial.number = 0
        mock_study.best_trial = mock_trial
        
        # Create mock MLflow client and runs
        mock_client = MagicMock()
        parent_run = _make_mlflow_run(
            run_id="parent-run-id",
            tags={"code.study_key_hash": "study_hash_123"},
        )
        candidate_run = _make_mlflow_run(
            run_id="child-run-id",
            tags={
                "mlflow.parentRunId": "parent-run-id",
                "trial_number": "0",
                "code.study_key_hash": "study_hash_123",
            },
        )
        active_run = _make_mlflow_run(run_id="active-run-id", experiment_id="exp-1")
        mock_client.search_runs.return_value = [candidate_run]
        mock_client.get_run.return_value = parent_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=active_run):
                with patch("mlflow.log_param") as mock_log_param:
                    with patch("mlflow.set_tag") as mock_set_tag:
                        # Call _log_best_trial_id with output_dir
                        tracker._log_best_trial_id(
                            study=mock_study,
                            parent_run_id="parent-run-id",
                            output_dir=output_dir_structure,
                        )
                        
                        # Verify tags were set (means a matching run was found and config_dir inferred)
                        assert mock_set_tag.called
                        
                        # Verify tags were set (indicating config_dir was found)
                        tag_calls = [call[0][0] for call in mock_set_tag.call_args_list]
                        assert any("best_trial" in tag for tag in tag_calls)

    def test_log_best_trial_id_finds_config_in_parent_chain(
        self, root_dir_with_config: Path
    ):
        """Test that config_dir is found by searching up parent chain."""
        tracker = MLflowSweepTracker(experiment_name="test")
        
        # Create a deep output directory structure
        deep_output = (
            root_dir_with_config 
            / "outputs" 
            / "hpo" 
            / "local" 
            / "distilbert" 
            / "study-abc123" 
            / "trial-xyz789"
        )
        deep_output.mkdir(parents=True)
        
        # Create mock study
        mock_study = Mock()
        mock_trial = Mock()
        mock_trial.number = 0
        mock_study.best_trial = mock_trial
        
        mock_client = MagicMock()
        parent_run = _make_mlflow_run(
            run_id="parent-run-id",
            tags={"code.study_key_hash": "study_hash_123"},
        )
        candidate_run = _make_mlflow_run(
            run_id="child-run-id",
            tags={
                "mlflow.parentRunId": "parent-run-id",
                "trial_number": "0",
                "code.study_key_hash": "study_hash_123",
            },
        )
        active_run = _make_mlflow_run(run_id="active-run-id", experiment_id="exp-1")
        mock_client.search_runs.return_value = [candidate_run]
        mock_client.get_run.return_value = parent_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=active_run):
                with patch("mlflow.log_param"):
                    with patch("mlflow.set_tag") as mock_set_tag:
                        # Should find config_dir at root_dir_with_config / "config"
                        tracker._log_best_trial_id(
                            study=mock_study,
                            parent_run_id="parent-run-id",
                            output_dir=deep_output,
                        )
                        
                        # Verify tags were set (config_dir was found)
                        assert mock_set_tag.called

    def test_log_best_trial_id_falls_back_to_cwd_config_when_not_found(
        self, tmp_path: Path, monkeypatch
    ):
        """Test that config_dir falls back to cwd/config when not found in parent chain."""
        tracker = MLflowSweepTracker(experiment_name="test")
        
        # Create output dir without config in parent chain
        output_dir = tmp_path / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        # Create config in cwd
        cwd_config = tmp_path / "config"
        cwd_config.mkdir()
        (cwd_config / "tags.yaml").write_text("schema_version: 1")
        
        # Change to tmp_path as cwd
        monkeypatch.chdir(tmp_path)
        
        mock_study = Mock()
        mock_trial = Mock()
        mock_trial.number = 0
        mock_study.best_trial = mock_trial
        
        mock_client = MagicMock()
        parent_run = _make_mlflow_run(
            run_id="parent-run-id",
            tags={"code.study_key_hash": "study_hash_123"},
        )
        candidate_run = _make_mlflow_run(
            run_id="child-run-id",
            tags={
                "mlflow.parentRunId": "parent-run-id",
                "trial_number": "0",
                "code.study_key_hash": "study_hash_123",
            },
        )
        active_run = _make_mlflow_run(run_id="active-run-id", experiment_id="exp-1")
        mock_client.search_runs.return_value = [candidate_run]
        mock_client.get_run.return_value = parent_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=active_run):
                with patch("mlflow.log_param"):
                    with patch("mlflow.set_tag") as mock_set_tag:
                        tracker._log_best_trial_id(
                            study=mock_study,
                            parent_run_id="parent-run-id",
                            output_dir=output_dir,
                        )
                        
                        # Should still work (falls back to cwd/config)
                        assert mock_set_tag.called

    def test_log_final_metrics_infers_config_correctly(
        self, root_dir_with_config: Path, output_dir_structure: Path
    ):
        """Test that log_final_metrics correctly infers config_dir from output_dir."""
        tracker = MLflowSweepTracker(experiment_name="test")
        
        mock_study = Mock()
        mock_trial = Mock()
        mock_trial.number = 0
        mock_trial.value = 0.5
        mock_study.best_trial = mock_trial
        mock_study.best_value = 0.5
        mock_study.best_params = {"learning_rate": 1e-4}
        mock_study.trials = [mock_trial]
        
        mock_client = MagicMock()
        # Configure best-trial lookup to succeed (so mlflow.set_tag is exercised)
        parent_run = _make_mlflow_run(
            run_id="parent-run-id",
            tags={"code.study_key_hash": "study_hash_123"},
        )
        candidate_run = _make_mlflow_run(
            run_id="child-run-id",
            tags={
                "mlflow.parentRunId": "parent-run-id",
                "trial_number": "0",
                "code.study_key_hash": "study_hash_123",
            },
        )
        mock_client.get_run.return_value = parent_run
        mock_client.search_runs.return_value = [candidate_run]
        active_run = _make_mlflow_run(run_id="active-run-id", experiment_id="exp-1")
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=active_run):
                with patch("mlflow.log_metric") as mock_log_metric:
                    with patch("mlflow.log_param") as mock_log_param:
                        with patch("mlflow.set_tag") as mock_set_tag:
                            tracker.log_final_metrics(
                                study=mock_study,
                                objective_metric="macro-f1",
                                parent_run_id="parent-run-id",
                                output_dir=output_dir_structure,
                            )
                            
                            # Verify metrics and params were logged
                            assert mock_log_metric.called
                            assert mock_log_param.called
                            # Tags should be set (best trial run id/number)
                            assert mock_set_tag.called

    def test_log_final_metrics_uses_hpo_output_dir_when_output_dir_none(
        self, root_dir_with_config: Path, output_dir_structure: Path
    ):
        """Test that log_final_metrics uses hpo_output_dir for config inference when output_dir is None."""
        tracker = MLflowSweepTracker(experiment_name="test")
        
        mock_study = Mock()
        mock_trial = Mock()
        mock_trial.number = 0
        mock_trial.value = 0.5
        mock_study.best_trial = mock_trial
        mock_study.best_value = 0.5
        mock_study.best_params = {"learning_rate": 1e-4}
        mock_study.trials = [mock_trial]
        
        mock_client = MagicMock()
        # Configure best-trial lookup to succeed so get_hpo_best_trial_run_id is called
        parent_run = _make_mlflow_run(
            run_id="parent-run-id",
            tags={"code.study_key_hash": "study_hash_123"},
        )
        candidate_run = _make_mlflow_run(
            run_id="child-run-id",
            tags={
                "mlflow.parentRunId": "parent-run-id",
                "trial_number": "0",
                "code.study_key_hash": "study_hash_123",
            },
        )
        mock_client.get_run.return_value = parent_run
        mock_client.search_runs.return_value = [candidate_run]
        active_run = _make_mlflow_run(run_id="active-run-id", experiment_id="exp-1")
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=active_run):
                with patch("mlflow.log_metric"):
                    with patch("mlflow.log_param"):
                        with patch("infrastructure.naming.mlflow.tag_keys.get_hpo_best_trial_run_id") as mock_get_tag:
                            # Capture the config_dir passed to get_hpo_best_trial_run_id
                            config_dirs_passed = []
                            
                            def capture_config_dir(config_dir):
                                config_dirs_passed.append(config_dir)
                                return "code.best_trial_run_id"
                            
                            mock_get_tag.side_effect = capture_config_dir
                            
                            # Call with output_dir=None but hpo_output_dir provided
                            tracker.log_final_metrics(
                                study=mock_study,
                                objective_metric="macro-f1",
                                parent_run_id="parent-run-id",
                                output_dir=None,  # Explicitly None
                                hpo_output_dir=output_dir_structure,  # Use this for inference
                            )
                            
                            # Verify that config_dir was inferred from hpo_output_dir
                            assert len(config_dirs_passed) > 0
                            config_dir_used = config_dirs_passed[0]
                            assert config_dir_used is not None
                            assert config_dir_used.exists(), f"Config dir {config_dir_used} should exist"
                            # Should be root_dir_with_config / "config"
                            assert config_dir_used == root_dir_with_config / "config", \
                                f"Expected {root_dir_with_config / 'config'}, got {config_dir_used}"

    def test_config_dir_not_in_outputs_directory(
        self, root_dir_with_config: Path, output_dir_structure: Path
    ):
        """Test that config_dir is NOT incorrectly inferred as outputs/config/."""
        tracker = MLflowSweepTracker(experiment_name="test")
        
        # Ensure outputs/config/ does NOT exist
        outputs_config = root_dir_with_config / "outputs" / "config"
        assert not outputs_config.exists(), "outputs/config should not exist for this test"
        
        # But root/config/ should exist
        root_config = root_dir_with_config / "config"
        assert root_config.exists(), "root/config should exist"
        
        mock_study = Mock()
        mock_trial = Mock()
        mock_trial.number = 0
        mock_study.best_trial = mock_trial
        
        mock_client = MagicMock()
        parent_run = _make_mlflow_run(
            run_id="parent-run-id",
            tags={"code.study_key_hash": "study_hash_123"},
        )
        candidate_run = _make_mlflow_run(
            run_id="child-run-id",
            tags={
                "mlflow.parentRunId": "parent-run-id",
                "trial_number": "0",
                "code.study_key_hash": "study_hash_123",
            },
        )
        active_run = _make_mlflow_run(run_id="active-run-id", experiment_id="exp-1")
        mock_client.search_runs.return_value = [candidate_run]
        mock_client.get_run.return_value = parent_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=active_run):
                with patch("mlflow.log_param"):
                    with patch("infrastructure.naming.mlflow.tag_keys.get_hpo_best_trial_run_id") as mock_get_tag:
                        # Capture the config_dir passed to get_hpo_best_trial_run_id
                        config_dirs_passed = []
                        
                        def capture_config_dir(config_dir):
                            config_dirs_passed.append(config_dir)
                            return "code.best_trial_run_id"
                        
                        mock_get_tag.side_effect = capture_config_dir
                        
                        tracker._log_best_trial_id(
                            study=mock_study,
                            parent_run_id="parent-run-id",
                            output_dir=output_dir_structure,
                        )
                        
                        # Verify that config_dir passed is NOT outputs/config/
                        assert len(config_dirs_passed) > 0
                        config_dir_used = config_dirs_passed[0]
                        assert config_dir_used is not None
                        assert config_dir_used.exists(), f"Config dir {config_dir_used} should exist"
                        
                        # Check that config_dir is not in an outputs/ subdirectory
                        # (check if any parent is named "outputs")
                        config_path_parts = config_dir_used.parts
                        outputs_index = None
                        for i, part in enumerate(config_path_parts):
                            if part == "outputs" and i < len(config_path_parts) - 1:
                                # Check if next part is "config" - that would be outputs/config/
                                if i + 1 < len(config_path_parts) and config_path_parts[i + 1] == "config":
                                    outputs_index = i
                                    break
                        
                        assert outputs_index is None, \
                            f"Config dir should not be in outputs/config/ subdirectory, got {config_dir_used}"
                        
                        # Should be root_dir_with_config / "config"
                        assert config_dir_used == root_dir_with_config / "config", \
                            f"Expected {root_dir_with_config / 'config'}, got {config_dir_used}"

