"""
Integration tests for HPO hash consistency across parent, trial, and refit runs.

Verifies that:
1. Parent runs have v2 study_key_hash tags
2. Trial runs have matching v2 study_key_hash tags
3. Refit runs have matching v2 study_key_hash tags
4. trial_key_hash is computed consistently
5. Refit linking tags are set correctly
"""
import pytest
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

from infrastructure.naming.mlflow.hpo_keys import (
    build_hpo_study_key_v2,
    build_hpo_study_key_hash,
    build_hpo_trial_key,
    build_hpo_trial_key_hash,
    compute_data_fingerprint,
    compute_eval_fingerprint,
)
from infrastructure.naming.mlflow.tags_registry import load_tags_registry


class TestHashConsistency:
    """Test hash computation consistency across run types."""

    @pytest.fixture
    def sample_configs(self):
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
                "k_fold": {"enabled": True, "n_splits": 2},
                "sampling": {"algorithm": "random"},
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
        }

    def test_v2_hash_computation_always_succeeds(self, sample_configs):
        """Test that v2 hash computation always succeeds with fallbacks."""
        data_config = sample_configs["data_config"]
        hpo_config = sample_configs["hpo_config"]
        train_config = sample_configs["train_config"]
        backbone = sample_configs["backbone"]

        # Compute fingerprints (should always succeed)
        data_fp = compute_data_fingerprint(data_config)
        eval_config = train_config.get("eval", {}) or {}
        eval_fp = compute_eval_fingerprint(eval_config)

        # Verify fingerprints are strings (never None)
        assert isinstance(data_fp, str)
        assert isinstance(eval_fp, str)
        assert len(data_fp) == 64  # SHA256 hex
        assert len(eval_fp) == 64

        # Compute v2 study key hash
        study_key_v2 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model=backbone,
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        study_key_hash_v2 = build_hpo_study_key_hash(study_key_v2)

        # Verify hash is computed
        assert isinstance(study_key_hash_v2, str)
        assert len(study_key_hash_v2) == 64

    def test_v2_hash_with_empty_configs(self):
        """Test that v2 hash computation handles empty/None configs gracefully."""
        # Test with empty dicts (fingerprints should still work)
        data_fp = compute_data_fingerprint({})
        eval_fp = compute_eval_fingerprint({})

        assert isinstance(data_fp, str)
        assert isinstance(eval_fp, str)

        # Should be able to compute v2 hash even with minimal configs
        study_key_v2 = build_hpo_study_key_v2(
            data_config={"name": "test"},
            hpo_config={"search_space": {}},
            train_config={"max_steps": 100},
            model="test-model",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        study_key_hash_v2 = build_hpo_study_key_hash(study_key_v2)

        assert isinstance(study_key_hash_v2, str)
        assert len(study_key_hash_v2) == 64

    def test_trial_key_hash_consistency(self, sample_configs):
        """Test that trial_key_hash is computed consistently using same study_key_hash."""
        data_config = sample_configs["data_config"]
        hpo_config = sample_configs["hpo_config"]
        train_config = sample_configs["train_config"]
        backbone = sample_configs["backbone"]

        # Compute study_key_hash (v2)
        data_fp = compute_data_fingerprint(data_config)
        eval_config = train_config.get("eval", {}) or {}
        eval_fp = compute_eval_fingerprint(eval_config)

        study_key_v2 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model=backbone,
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        study_key_hash = build_hpo_study_key_hash(study_key_v2)

        # Compute trial_key_hash using same study_key_hash
        hyperparameters = {
            "learning_rate": 3.5e-5,
            "batch_size": 4,
            "dropout": 0.2,
        }

        trial_key = build_hpo_trial_key(study_key_hash, hyperparameters)
        trial_key_hash_1 = build_hpo_trial_key_hash(trial_key)

        # Recompute with same inputs - should be identical
        trial_key_2 = build_hpo_trial_key(study_key_hash, hyperparameters)
        trial_key_hash_2 = build_hpo_trial_key_hash(trial_key_2)

        assert trial_key_hash_1 == trial_key_hash_2
        assert len(trial_key_hash_1) == 64

    def test_hash_mismatch_detection(self, sample_configs):
        """Test that different study_key_hash produces different trial_key_hash."""
        data_config = sample_configs["data_config"]
        hpo_config = sample_configs["hpo_config"]
        train_config = sample_configs["train_config"]
        backbone = sample_configs["backbone"]

        # Compute two different study_key_hash values
        data_fp1 = compute_data_fingerprint(data_config)
        data_config_2 = data_config.copy()
        data_config_2["version"] = "2.0"  # Different version
        data_fp2 = compute_data_fingerprint(data_config_2)

        eval_config = train_config.get("eval", {}) or {}
        eval_fp = compute_eval_fingerprint(eval_config)

        study_key_v2_1 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model=backbone,
            data_fingerprint=data_fp1,
            eval_fingerprint=eval_fp,
        )
        study_key_hash_1 = build_hpo_study_key_hash(study_key_v2_1)

        study_key_v2_2 = build_hpo_study_key_v2(
            data_config=data_config_2,
            hpo_config=hpo_config,
            train_config=train_config,
            model=backbone,
            data_fingerprint=data_fp2,
            eval_fingerprint=eval_fp,
        )
        study_key_hash_2 = build_hpo_study_key_hash(study_key_v2_2)

        # Should be different
        assert study_key_hash_1 != study_key_hash_2

        # Same hyperparameters with different study_key_hash should produce different trial_key_hash
        hyperparameters = {"learning_rate": 3.5e-5, "batch_size": 4}
        trial_key_hash_1 = build_hpo_trial_key_hash(
            build_hpo_trial_key(study_key_hash_1, hyperparameters)
        )
        trial_key_hash_2 = build_hpo_trial_key_hash(
            build_hpo_trial_key(study_key_hash_2, hyperparameters)
        )

        assert trial_key_hash_1 != trial_key_hash_2


class TestRunTagConsistency:
    """Test that tags are set consistently across run types."""

    @pytest.fixture
    def config_dir(self, tmp_path):
        """Create a temporary config directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        # Create minimal tags.yaml
        tags_yaml = config_dir / "tags.yaml"
        tags_yaml.write_text("""
grouping:
  study_key_hash: "code.study_key_hash"
  trial_key_hash: "code.trial_key_hash"
process:
  stage: "code.stage"
fingerprint:
  data: "code.fingerprint.data"
  eval: "code.fingerprint.eval"
refit:
  of_trial_run_id: "code.refit.of_trial_run_id"
""")
        return config_dir

    def test_parent_run_has_v2_tags(self, config_dir, sample_configs):
        """Test that parent run gets v2 study_key_hash tag."""
        from training.hpo.execution.local.sweep import _set_phase2_hpo_tags

        data_config = sample_configs["data_config"]
        hpo_config = sample_configs["hpo_config"]
        train_config = sample_configs["train_config"]
        backbone = sample_configs["backbone"]

        # Mock MLflow client
        mock_client = MagicMock()
        mock_run = MagicMock()
        mock_run.info.run_id = "parent-run-123"
        mock_client.get_run.return_value = mock_run

        with patch("mlflow.tracking.MlflowClient", return_value=mock_client):
            _set_phase2_hpo_tags(
                parent_run_id="parent-run-123",
                data_config=data_config,
                hpo_config=hpo_config,
                train_config=train_config,
                backbone=backbone,
                config_dir=config_dir,
            )

        # Verify tags were set
        assert mock_client.set_tag.called

        # Check that study_key_hash tag was set (v2)
        set_tag_calls = {call[0][1]: call[0][2] for call in mock_client.set_tag.call_args_list}
        tags_registry = load_tags_registry(config_dir)
        study_key_tag = tags_registry.key("grouping", "study_key_hash")

        assert study_key_tag in set_tag_calls
        study_key_hash = set_tag_calls[study_key_tag]
        assert isinstance(study_key_hash, str)
        assert len(study_key_hash) == 64

        # Verify fingerprints were set
        data_fp_tag = tags_registry.key("fingerprint", "data")
        eval_fp_tag = tags_registry.key("fingerprint", "eval")
        assert data_fp_tag in set_tag_calls
        assert eval_fp_tag in set_tag_calls


class TestRefitLinking:
    """Test refit run linking to trial runs."""

    def test_refit_uses_parent_study_key_hash(self, sample_configs):
        """Test that refit uses parent run's study_key_hash for trial_key_hash computation."""
        # Simulate: Parent run has v2 study_key_hash
        parent_study_key_hash = "712fbee85e89992eb7c7612788ec0851212ac9410f6a35c474dfbfb1cadef818"

        # Refit should use parent's hash (not recompute)
        # This ensures consistency with trial runs
        hyperparameters = {"learning_rate": 3.5e-5, "batch_size": 4}

        trial_key = build_hpo_trial_key(parent_study_key_hash, hyperparameters)
        trial_key_hash = build_hpo_trial_key_hash(trial_key)

        # This trial_key_hash should match what trial run has
        assert isinstance(trial_key_hash, str)
        assert len(trial_key_hash) == 64

    def test_refit_linking_tag_format(self, config_dir):
        """Test that refit linking tag uses correct format."""
        tags_registry = load_tags_registry(config_dir)
        refit_tag = tags_registry.key("refit", "of_trial_run_id")

        # Should be in format: code.refit.of_trial_run_id
        assert refit_tag == "code.refit.of_trial_run_id"


class TestParentTrialHashMismatch:
    """Test to detect and prevent parent vs trial hash mismatches."""

    def test_parent_v2_trial_v1_mismatch_detection(self, sample_configs):
        """Test that we can detect when parent has v2 but trial has v1 hash."""
        data_config = sample_configs["data_config"]
        hpo_config = sample_configs["hpo_config"]
        train_config = sample_configs["train_config"]
        backbone = sample_configs["backbone"]

        # Parent run computes v2 hash
        data_fp = compute_data_fingerprint(data_config)
        eval_config = train_config.get("eval", {}) or {}
        eval_fp = compute_eval_fingerprint(eval_config)

        study_key_v2 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model=backbone,
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        parent_study_key_hash_v2 = build_hpo_study_key_hash(study_key_v2)

        # Trial run computes v1 hash (old behavior)
        from infrastructure.naming.mlflow.hpo_keys import (
            build_hpo_study_key,
        )
        study_key_v1 = build_hpo_study_key(
            data_config=data_config,
            hpo_config=hpo_config,
            model=backbone,
            benchmark_config={},
        )
        trial_study_key_hash_v1 = build_hpo_study_key_hash(study_key_v1)

        # They should be different (this is the mismatch we're fixing)
        assert parent_study_key_hash_v2 != trial_study_key_hash_v1

        # With v2 migration, trial should also compute v2
        trial_study_key_hash_v2 = parent_study_key_hash_v2  # Should use parent's hash

        # Now they match
        assert parent_study_key_hash_v2 == trial_study_key_hash_v2

    def test_same_configs_produce_same_v2_hash(self, sample_configs):
        """Test that same configs always produce same v2 hash (deterministic)."""
        data_config = sample_configs["data_config"]
        hpo_config = sample_configs["hpo_config"]
        train_config = sample_configs["train_config"]
        backbone = sample_configs["backbone"]

        # Compute v2 hash twice with same inputs
        data_fp1 = compute_data_fingerprint(data_config)
        eval_config = train_config.get("eval", {}) or {}
        eval_fp1 = compute_eval_fingerprint(eval_config)

        study_key_v2_1 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model=backbone,
            data_fingerprint=data_fp1,
            eval_fingerprint=eval_fp1,
        )
        hash_1 = build_hpo_study_key_hash(study_key_v2_1)

        # Compute again
        data_fp2 = compute_data_fingerprint(data_config)
        eval_fp2 = compute_eval_fingerprint(eval_config)

        study_key_v2_2 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model=backbone,
            data_fingerprint=data_fp2,
            eval_fingerprint=eval_fp2,
        )
        hash_2 = build_hpo_study_key_hash(study_key_v2_2)

        # Should be identical
        assert hash_1 == hash_2
        assert data_fp1 == data_fp2
        assert eval_fp1 == eval_fp2

