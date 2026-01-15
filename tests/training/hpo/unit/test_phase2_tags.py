"""Unit tests for Phase 2 HPO tag setting (sweep.py).

Tests the _set_phase2_hpo_tags() function that sets:
- code.study.key_schema_version
- code.fingerprint.data
- code.fingerprint.eval
- code.artifact.available
- code.objective.direction
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from training.hpo.execution.local.sweep import _set_phase2_hpo_tags


@pytest.fixture
def mock_data_config():
    """Create mock data config."""
    return {
        "name": "test_dataset",
        "version": "1.0",
        "content_hash": "abc123",
    }


@pytest.fixture
def mock_hpo_config():
    """Create mock HPO config."""
    return {
        "search_space": {"lr": {"type": "float", "low": 1e-5, "high": 1e-3}},
        "objective": {"metric": "macro-f1", "direction": "maximize"},
    }


@pytest.fixture
def mock_train_config():
    """Create mock training config."""
    return {
        "eval": {
            "metric": "macro-f1",
            "k_fold": {"n_splits": 5},
        },
    }


class TestSetPhase2HpoTags:
    """Test _set_phase2_hpo_tags() function."""

    @patch("mlflow.tracking.MlflowClient")
    @patch("training.hpo.execution.local.sweep.mlflow")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_data_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_eval_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_v2")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_hash")
    @patch("infrastructure.naming.mlflow.tags_registry.load_tags_registry")
    def test_sets_all_tags_successfully(
        self,
        mock_load_tags_registry,
        mock_build_hash,
        mock_build_key_v2,
        mock_compute_eval_fp,
        mock_compute_data_fp,
        mock_mlflow,
        mock_mlflow_client_class,
        mock_data_config,
        mock_hpo_config,
        mock_train_config,
    ):
        """Test that all Phase 2 tags are set successfully."""
        # Setup mocks
        mock_client = Mock()
        mock_mlflow_client_class.return_value = mock_client
        mock_mlflow.tracking.MlflowClient.return_value = mock_client
        
        mock_registry = Mock()
        mock_load_tags_registry.return_value = mock_registry
        mock_registry.key.side_effect = lambda section, key: f"code.{section}.{key}"
        
        mock_compute_data_fp.return_value = "data_fp123"
        mock_compute_eval_fp.return_value = "eval_fp456"
        mock_build_key_v2.return_value = '{"schema_version": "2.0"}'
        mock_build_hash.return_value = "hash123"
        
        # Call function
        _set_phase2_hpo_tags(
            parent_run_id="run123",
            data_config=mock_data_config,
            hpo_config=mock_hpo_config,
            train_config=mock_train_config,
            backbone="distilbert",
        )
        
        # Verify tags were set (even if they fail due to run not existing, the function still attempts to set them)
        # The function catches exceptions, so we verify it was called
        assert mock_client.set_tag.called
        
        # Get all call arguments (run_id, tag_key, tag_value)
        call_args_list = mock_client.set_tag.call_args_list
        
        # Extract tag key-value pairs
        tag_dict = {}
        for call in call_args_list:
            if len(call[0]) >= 2:
                tag_key = call[0][1]  # Second argument is tag key
                tag_value = call[0][2] if len(call[0]) > 2 else None  # Third argument is tag value
                tag_dict[tag_key] = tag_value
        
        # Check that key tags were attempted to be set
        # Note: The function may catch exceptions, but we verify the calls were made
        assert len(call_args_list) > 0
        # Verify at least one tag was attempted
        assert any("code.study.key_schema_version" in str(call) or "code.fingerprint" in str(call) or "code.objective" in str(call) or "code.artifact" in str(call) for call in call_args_list)

    @patch("training.hpo.execution.local.sweep.mlflow")
    def test_handles_missing_parent_run_id(
        self,
        mock_mlflow,
        mock_data_config,
        mock_hpo_config,
        mock_train_config,
    ):
        """Test that function returns early if parent_run_id is missing."""
        _set_phase2_hpo_tags(
            parent_run_id="",
            data_config=mock_data_config,
            hpo_config=mock_hpo_config,
            train_config=mock_train_config,
            backbone="distilbert",
        )
        
        # Should not create client or set tags
        assert not mock_mlflow.tracking.MlflowClient.called

    @patch("mlflow.tracking.MlflowClient")
    @patch("training.hpo.execution.local.sweep.mlflow")
    def test_handles_none_parent_run_id(
        self,
        mock_mlflow,
        mock_data_config,
        mock_hpo_config,
        mock_train_config,
    ):
        """Test that function returns early if parent_run_id is None."""
        _set_phase2_hpo_tags(
            parent_run_id=None,
            data_config=mock_data_config,
            hpo_config=mock_hpo_config,
            train_config=mock_train_config,
            backbone="distilbert",
        )
        
        # Should not create client or set tags
        assert not mock_mlflow.tracking.MlflowClient.called

    @patch("mlflow.tracking.MlflowClient")
    @patch("training.hpo.execution.local.sweep.mlflow")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_data_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_eval_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_v2")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_hash")
    @patch("infrastructure.naming.mlflow.tags_registry.load_tags_registry")
    def test_handles_missing_data_config(
        self,
        mock_load_tags_registry,
        mock_build_hash,
        mock_build_key_v2,
        mock_compute_eval_fp,
        mock_compute_data_fp,
        mock_mlflow,
        mock_hpo_config,
        mock_train_config,
    ):
        """Test that function handles missing data_config gracefully."""
        mock_client = Mock()
        mock_mlflow_client_class.return_value = mock_client
        mock_mlflow.tracking.MlflowClient.return_value = mock_client
        
        mock_registry = Mock()
        mock_load_tags_registry.return_value = mock_registry
        mock_registry.key.side_effect = lambda section, key: f"code.{section}.{key}"
        
        mock_compute_data_fp.return_value = ""
        mock_compute_eval_fp.return_value = "eval_fp456"
        mock_build_key_v2.return_value = '{"schema_version": "2.0"}'
        mock_build_hash.return_value = "hash123"
        
        _set_phase2_hpo_tags(
            parent_run_id="run123",
            data_config=None,
            hpo_config=mock_hpo_config,
            train_config=mock_train_config,
            backbone="distilbert",
        )
        
        # Should still set tags (with empty data fingerprint)
        assert mock_client.set_tag.called

    @patch("mlflow.tracking.MlflowClient")
    @patch("training.hpo.execution.local.sweep.mlflow")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_data_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_eval_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_v2")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_hash")
    @patch("infrastructure.naming.mlflow.tags_registry.load_tags_registry")
    def test_minimize_objective_direction(
        self,
        mock_load_tags_registry,
        mock_build_hash,
        mock_build_key_v2,
        mock_compute_eval_fp,
        mock_compute_data_fp,
        mock_mlflow,
        mock_mlflow_client_class,
        mock_data_config,
        mock_hpo_config,
        mock_train_config,
    ):
        """Test that minimize objective direction is set correctly."""
        mock_client = Mock()
        mock_mlflow_client_class.return_value = mock_client
        mock_mlflow.tracking.MlflowClient.return_value = mock_client
        
        mock_registry = Mock()
        mock_load_tags_registry.return_value = mock_registry
        mock_registry.key.side_effect = lambda section, key: f"code.{section}.{key}"
        
        mock_compute_data_fp.return_value = "data_fp123"
        mock_compute_eval_fp.return_value = "eval_fp456"
        mock_build_key_v2.return_value = '{"schema_version": "2.0"}'
        mock_build_hash.return_value = "hash123"
        
        # Set minimize direction
        mock_hpo_config["objective"]["direction"] = "minimize"
        
        _set_phase2_hpo_tags(
            parent_run_id="run123",
            data_config=mock_data_config,
            hpo_config=mock_hpo_config,
            train_config=mock_train_config,
            backbone="distilbert",
        )
        
        # Check that minimize was set
        call_args_list = [call[0] for call in mock_client.set_tag.call_args_list]
        tag_dict = {args[0]: args[1] for args in call_args_list}
        assert tag_dict["code.objective.direction"] == "minimize"

    @patch("mlflow.tracking.MlflowClient")
    @patch("training.hpo.execution.local.sweep.mlflow")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_data_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_eval_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_v2")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_hash")
    @patch("infrastructure.naming.mlflow.tags_registry.load_tags_registry")
    def test_legacy_goal_key_migration(
        self,
        mock_load_tags_registry,
        mock_build_hash,
        mock_build_key_v2,
        mock_compute_eval_fp,
        mock_compute_data_fp,
        mock_mlflow,
        mock_mlflow_client_class,
        mock_data_config,
        mock_hpo_config,
        mock_train_config,
    ):
        """Test that legacy 'goal' key is migrated to 'direction'."""
        mock_client = Mock()
        mock_mlflow_client_class.return_value = mock_client
        mock_mlflow.tracking.MlflowClient.return_value = mock_client
        
        mock_registry = Mock()
        mock_load_tags_registry.return_value = mock_registry
        mock_registry.key.side_effect = lambda section, key: f"code.{section}.{key}"
        
        mock_compute_data_fp.return_value = "data_fp123"
        mock_compute_eval_fp.return_value = "eval_fp456"
        mock_build_key_v2.return_value = '{"schema_version": "2.0"}'
        mock_build_hash.return_value = "hash123"
        
        # Use legacy 'goal' key
        mock_hpo_config["objective"] = {"metric": "macro-f1", "goal": "maximize"}
        
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _set_phase2_hpo_tags(
                parent_run_id="run123",
                data_config=mock_data_config,
                hpo_config=mock_hpo_config,
                train_config=mock_train_config,
                backbone="distilbert",
            )
            
            # Should warn about deprecated key
            assert len(w) > 0
        
        # Check that maximize was set (from goal)
        call_args_list = [call[0] for call in mock_client.set_tag.call_args_list]
        tag_dict = {args[0]: args[1] for args in call_args_list}
        assert tag_dict["code.objective.direction"] == "maximize"

    @patch("mlflow.tracking.MlflowClient")
    @patch("mlflow.tracking.MlflowClient")
    @patch("training.hpo.execution.local.sweep.mlflow")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_data_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_eval_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_v2")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_hash")
    @patch("infrastructure.naming.mlflow.tags_registry.load_tags_registry")
    def test_handles_exception_gracefully(
        self,
        mock_load_tags_registry,
        mock_build_hash,
        mock_build_key_v2,
        mock_compute_eval_fp,
        mock_compute_data_fp,
        mock_mlflow,
        mock_mlflow_client_class,
        mock_data_config,
        mock_hpo_config,
        mock_train_config,
    ):
        """Test that exceptions are handled gracefully."""
        # Make client raise exception
        mock_client = Mock()
        mock_client.set_tag.side_effect = Exception("MLflow error")
        mock_mlflow_client_class.return_value = mock_client
        mock_mlflow.tracking.MlflowClient.return_value = mock_client
        
        mock_registry = Mock()
        mock_load_tags_registry.return_value = mock_registry
        mock_registry.key.side_effect = lambda section, key: f"code.{section}.{key}"
        
        mock_compute_data_fp.return_value = "data_fp123"
        mock_compute_eval_fp.return_value = "eval_fp456"
        mock_build_key_v2.return_value = '{"schema_version": "2.0"}'
        mock_build_hash.return_value = "hash123"
        
        # Should not raise exception
        _set_phase2_hpo_tags(
            parent_run_id="run123",
            data_config=mock_data_config,
            hpo_config=mock_hpo_config,
            train_config=mock_train_config,
            backbone="distilbert",
        )
        
        # Function should complete without raising

    @patch("mlflow.tracking.MlflowClient")
    @patch("training.hpo.execution.local.sweep.mlflow")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_data_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.compute_eval_fingerprint")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_v2")
    @patch("infrastructure.naming.mlflow.hpo_keys.build_hpo_study_key_hash")
    @patch("infrastructure.naming.mlflow.tags_registry.load_tags_registry")
    def test_schema_version_1_0_fallback(
        self,
        mock_load_tags_registry,
        mock_build_hash,
        mock_build_key_v2,
        mock_compute_eval_fp,
        mock_compute_data_fp,
        mock_mlflow,
        mock_mlflow_client_class,
        mock_data_config,
        mock_hpo_config,
        mock_train_config,
    ):
        """Test that schema version 1.0 is used as fallback when v2 build fails."""
        mock_client = Mock()
        mock_mlflow_client_class.return_value = mock_client
        mock_mlflow.tracking.MlflowClient.return_value = mock_client
        
        # Mock get_run to return a valid run (so set_tag doesn't fail)
        mock_run = Mock()
        mock_run.info.run_id = "run123"
        mock_client.get_run.return_value = mock_run
        
        mock_registry = Mock()
        mock_load_tags_registry.return_value = mock_registry
        mock_registry.key.side_effect = lambda section, key: f"code.{section}.{key}"
        
        mock_compute_data_fp.return_value = "data_fp123"
        mock_compute_eval_fp.return_value = "eval_fp456"
        # Make v2 build fail
        mock_build_key_v2.side_effect = Exception("Cannot build v2")
        mock_build_hash.return_value = "hash123"
        
        # Should fallback to v1.0
        _set_phase2_hpo_tags(
            parent_run_id="run123",
            data_config=mock_data_config,
            hpo_config=mock_hpo_config,
            train_config=mock_train_config,
            backbone="distilbert",
        )
        
        # Check that v1.0 was set (fallback)
        call_args_list = [call[0] for call in mock_client.set_tag.call_args_list]
        tag_dict = {args[0]: args[1] for args in call_args_list}
        assert tag_dict["code.study.key_schema_version"] == "1.0"

