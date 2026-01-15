"""Unit tests for CV trial run hash computation.

Tests cover:
1. Priority hierarchy: parent tags -> v2 computation from configs
2. Hash consistency between parent and trial runs
3. Edge cases: missing tags, missing configs, errors
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

# Import the function we're testing
from training.hpo.execution.local.cv import _create_trial_run


@pytest.fixture
def sample_configs():
    """Sample configurations for testing."""
    return {
        "data_config": {
            "name": "test_dataset",
            "version": "1.0",
            "local_path": "/tmp/data",
            "schema": {"labels": ["PER", "ORG"]},
            "split_seed": 42,
        },
        "hpo_config": {
            "search_space": {
                "learning_rate": {"type": "loguniform", "low": 1e-5, "high": 1e-3},
                "batch_size": {"type": "choice", "choices": [4, 8, 16]},
            },
            "objective": {"metric": "macro-f1", "direction": "maximize"},
            "evaluation": {
                "evaluator_version": "v1",
                "metric": {"name": "macro-f1"},
            },
        },
        "train_config": {
            "max_steps": 1000,
            "num_epochs": 3,
            "seed_policy": "fixed",
            "eval": {
                "evaluator_version": "v1",
                "metric": {"name": "macro-f1"},
            },
        },
        "backbone": "distilbert-base-uncased",
        "benchmark_config": {},
    }


@pytest.fixture
def root_dir_with_config(tmp_path: Path) -> Path:
    """Create a root directory with config/ directory."""
    root = tmp_path / "workspace"
    root.mkdir()
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "tags.yaml").write_text("schema_version: 1")
    return root


class TestCVTrialRunHashComputation:
    """Test hash computation priority hierarchy in _create_trial_run."""

    def test_priority_1_use_provided_hashes(self, sample_configs, root_dir_with_config):
        """Test Priority 1: Use hashes provided as arguments."""
        config_dir = root_dir_with_config / "config"
        output_dir = root_dir_with_config / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        provided_study_key_hash = "provided_study_hash_" + "a" * 44
        provided_study_family_hash = "provided_family_hash_" + "b" * 44
        
        trial_params = {
            "trial_number": 0,
            "learning_rate": 3e-5,
            "batch_size": 4,
        }
        
        # Mock MLflow
        mock_client = MagicMock()
        mock_active_run = MagicMock()
        mock_active_run.info.experiment_id = "exp-123"
        mock_parent_run = MagicMock()
        mock_parent_run.info.run_id = "parent-run-123"
        mock_trial_run = MagicMock()
        mock_trial_run.info.run_id = "trial-run-456"
        mock_client.get_run.return_value = mock_parent_run
        mock_client.create_run.return_value = mock_trial_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=mock_active_run):
                run_id = _create_trial_run(
                    trial_params=trial_params,
                    config_dir=config_dir,
                    backbone=sample_configs["backbone"],
                    output_dir=output_dir,
                    hpo_parent_run_id="parent-run-123",
                    study_key_hash=provided_study_key_hash,
                    study_family_hash=provided_study_family_hash,
                    data_config=sample_configs["data_config"],
                    hpo_config=sample_configs["hpo_config"],
                    train_config=sample_configs["train_config"],
                )
                
                # Verify that provided hashes were used (check tags)
                assert mock_client.create_run.called
                create_call = mock_client.create_run.call_args
                tags = create_call[1]["tags"]
                assert tags.get("code.study_key_hash") == provided_study_key_hash
                assert tags.get("code.study_family_hash") == provided_study_family_hash

    def test_priority_2_get_from_parent_tags(self, sample_configs, root_dir_with_config):
        """Test Priority 2: Get hashes from parent run tags when not provided."""
        config_dir = root_dir_with_config / "config"
        output_dir = root_dir_with_config / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        parent_study_key_hash = "parent_study_hash_" + "a" * 44
        parent_study_family_hash = "parent_family_hash_" + "b" * 44
        
        trial_params = {
            "trial_number": 0,
            "learning_rate": 3e-5,
            "batch_size": 4,
        }
        
        # Mock MLflow
        mock_client = MagicMock()
        mock_active_run = MagicMock()
        mock_active_run.info.experiment_id = "exp-123"
        mock_parent_run = MagicMock()
        mock_parent_run.info.run_id = "parent-run-123"
        mock_parent_run.data.tags.get.side_effect = lambda key: {
            "code.study_key_hash": parent_study_key_hash,
            "code.study_family_hash": parent_study_family_hash,
        }.get(key)
        mock_trial_run = MagicMock()
        mock_trial_run.info.run_id = "trial-run-456"
        mock_client.get_run.return_value = mock_parent_run
        mock_client.create_run.return_value = mock_trial_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=mock_active_run):
                run_id = _create_trial_run(
                    trial_params=trial_params,
                    config_dir=config_dir,
                    backbone=sample_configs["backbone"],
                    output_dir=output_dir,
                    hpo_parent_run_id="parent-run-123",
                    study_key_hash=None,  # Not provided
                    study_family_hash=None,  # Not provided
                    data_config=sample_configs["data_config"],
                    hpo_config=sample_configs["hpo_config"],
                    train_config=sample_configs["train_config"],
                )
                
                # Verify parent run was queried
                assert mock_client.get_run.called
                
                # Verify that parent hashes were used
                assert mock_client.create_run.called
                create_call = mock_client.create_run.call_args
                tags = create_call[1]["tags"]
                assert tags.get("code.study_key_hash") == parent_study_key_hash
                assert tags.get("code.study_family_hash") == parent_study_family_hash

    def test_priority_3_compute_v2_from_configs(
        self, sample_configs, root_dir_with_config
    ):
        """Test Priority 3: Compute v2 hashes from configs when parent tags missing."""
        config_dir = root_dir_with_config / "config"
        output_dir = root_dir_with_config / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        trial_params = {
            "trial_number": 0,
            "learning_rate": 3e-5,
            "batch_size": 4,
        }
        
        # Mock MLflow
        mock_client = MagicMock()
        mock_active_run = MagicMock()
        mock_active_run.info.experiment_id = "exp-123"
        mock_parent_run = MagicMock()
        mock_parent_run.info.run_id = "parent-run-123"
        mock_parent_run.data.tags.get.return_value = None  # No tags
        mock_trial_run = MagicMock()
        mock_trial_run.info.run_id = "trial-run-456"
        mock_client.get_run.return_value = mock_parent_run
        mock_client.create_run.return_value = mock_trial_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=mock_active_run):
                run_id = _create_trial_run(
                    trial_params=trial_params,
                    config_dir=config_dir,
                    backbone=sample_configs["backbone"],
                    output_dir=output_dir,
                    hpo_parent_run_id="parent-run-123",
                    study_key_hash=None,
                    study_family_hash=None,
                    data_config=sample_configs["data_config"],
                    hpo_config=sample_configs["hpo_config"],
                    train_config=sample_configs["train_config"],
                )
                
                # Verify v2 hash was computed from configs
                assert mock_client.create_run.called
                create_call = mock_client.create_run.call_args
                tags = create_call[1]["tags"]
                
                # Should have computed v2 study_key_hash
                computed_hash = tags.get("code.study_key_hash")
                assert computed_hash is not None
                assert isinstance(computed_hash, str)
                assert len(computed_hash) == 64  # SHA256 hex

    def test_hash_consistency_with_parent(self, sample_configs, root_dir_with_config):
        """Test that trial run hash matches parent run hash (consistency check)."""
        config_dir = root_dir_with_config / "config"
        output_dir = root_dir_with_config / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        # Compute expected v2 hash (same logic as parent)
        from infrastructure.naming.mlflow.hpo_keys import (
            build_hpo_study_key_v2,
            compute_data_fingerprint,
            compute_eval_fingerprint,
        )
        from infrastructure.naming.mlflow.hpo_keys import (
            build_hpo_study_key_hash,
            build_hpo_study_family_key,
            build_hpo_study_family_hash,
        )
        
        data_fp = compute_data_fingerprint(sample_configs["data_config"])
        eval_config = sample_configs["train_config"].get("eval", {})
        eval_fp = compute_eval_fingerprint(eval_config)
        study_key_v2 = build_hpo_study_key_v2(
            data_config=sample_configs["data_config"],
            hpo_config=sample_configs["hpo_config"],
            train_config=sample_configs["train_config"],
            model=sample_configs["backbone"],
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        expected_study_key_hash = build_hpo_study_key_hash(study_key_v2)
        
        trial_params = {
            "trial_number": 0,
            "learning_rate": 3e-5,
            "batch_size": 4,
        }
        
        # Mock MLflow - parent has the v2 hash
        mock_client = MagicMock()
        mock_active_run = MagicMock()
        mock_active_run.info.experiment_id = "exp-123"
        mock_parent_run = MagicMock()
        mock_parent_run.info.run_id = "parent-run-123"
        mock_parent_run.data.tags.get.side_effect = lambda key: {
            "code.study_key_hash": expected_study_key_hash,
        }.get(key)
        mock_trial_run = MagicMock()
        mock_trial_run.info.run_id = "trial-run-456"
        mock_client.get_run.return_value = mock_parent_run
        mock_client.create_run.return_value = mock_trial_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=mock_active_run):
                run_id = _create_trial_run(
                    trial_params=trial_params,
                    config_dir=config_dir,
                    backbone=sample_configs["backbone"],
                    output_dir=output_dir,
                    hpo_parent_run_id="parent-run-123",
                    study_key_hash=None,
                    study_family_hash=None,
                    data_config=sample_configs["data_config"],
                    hpo_config=sample_configs["hpo_config"],
                    train_config=sample_configs["train_config"],
                )
                
                # Verify trial run hash matches parent hash
                create_call = mock_client.create_run.call_args
                tags = create_call[1]["tags"]
                assert tags.get("code.study_key_hash") == expected_study_key_hash

    def test_missing_train_config_still_computes_hash(
        self, sample_configs, root_dir_with_config
    ):
        """Test that hash computation works even if train_config is missing eval section."""
        config_dir = root_dir_with_config / "config"
        output_dir = root_dir_with_config / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        trial_params = {
            "trial_number": 0,
            "learning_rate": 3e-5,
        }
        
        # Train config without eval (should use hpo_config.evaluation or objective)
        train_config_no_eval = {
            "max_steps": 1000,
        }
        
        # Mock MLflow
        mock_client = MagicMock()
        mock_active_run = MagicMock()
        mock_active_run.info.experiment_id = "exp-123"
        mock_parent_run = MagicMock()
        mock_parent_run.data.tags.get.return_value = None
        mock_trial_run = MagicMock()
        mock_trial_run.info.run_id = "trial-run-456"
        mock_client.get_run.return_value = mock_parent_run
        mock_client.create_run.return_value = mock_trial_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=mock_active_run):
                run_id = _create_trial_run(
                    trial_params=trial_params,
                    config_dir=config_dir,
                    backbone=sample_configs["backbone"],
                    output_dir=output_dir,
                    hpo_parent_run_id="parent-run-123",
                    study_key_hash=None,
                    study_family_hash=None,
                    data_config=sample_configs["data_config"],
                    hpo_config=sample_configs["hpo_config"],
                    train_config=train_config_no_eval,  # No eval section
                )
                
                # Should still compute hash (uses hpo_config.evaluation or objective)
                assert mock_client.create_run.called
                create_call = mock_client.create_run.call_args
                tags = create_call[1]["tags"]
                computed_hash = tags.get("code.study_key_hash")
                assert computed_hash is not None
                assert len(computed_hash) == 64

    def test_error_handling_parent_run_not_found(
        self, sample_configs, root_dir_with_config
    ):
        """Test that errors when fetching parent run are handled gracefully."""
        config_dir = root_dir_with_config / "config"
        output_dir = root_dir_with_config / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        trial_params = {
            "trial_number": 0,
        }
        
        # Mock MLflow - parent run fetch fails
        mock_client = MagicMock()
        mock_active_run = MagicMock()
        mock_active_run.info.experiment_id = "exp-123"
        mock_client.get_run.side_effect = Exception("Parent run not found")
        mock_trial_run = MagicMock()
        mock_trial_run.info.run_id = "trial-run-456"
        mock_client.create_run.return_value = mock_trial_run
        
        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            with patch("mlflow.active_run", return_value=mock_active_run):
                # Should not crash, fallback to v2 computation
                run_id = _create_trial_run(
                    trial_params=trial_params,
                    config_dir=config_dir,
                    backbone=sample_configs["backbone"],
                    output_dir=output_dir,
                    hpo_parent_run_id="parent-run-123",
                    study_key_hash=None,
                    study_family_hash=None,
                    data_config=sample_configs["data_config"],
                    hpo_config=sample_configs["hpo_config"],
                    train_config=sample_configs["train_config"],
                )
                
                # Should still create trial run (fallback to v2 computation)
                assert mock_client.create_run.called

    def test_no_hpo_parent_run_id_returns_none(self, sample_configs, root_dir_with_config):
        """Test that None is returned when hpo_parent_run_id is not provided."""
        config_dir = root_dir_with_config / "config"
        output_dir = root_dir_with_config / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        trial_params = {
            "trial_number": 0,
        }
        
        # Should return None when no parent run ID
        run_id = _create_trial_run(
            trial_params=trial_params,
            config_dir=config_dir,
            backbone=sample_configs["backbone"],
            output_dir=output_dir,
            hpo_parent_run_id=None,  # No parent
            study_key_hash=None,
            study_family_hash=None,
            data_config=sample_configs["data_config"],
            hpo_config=sample_configs["hpo_config"],
            train_config=sample_configs["train_config"],
        )
        
        assert run_id is None


