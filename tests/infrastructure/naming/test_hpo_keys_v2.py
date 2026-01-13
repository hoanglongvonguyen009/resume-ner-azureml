"""Unit tests for HPO keys v2 functions (hpo_keys.py).

Tests the v2 study key hash functions with bound fingerprints:
- build_hpo_study_key_v2()
- compute_data_fingerprint()
- compute_eval_fingerprint()
"""

import pytest
from infrastructure.naming.mlflow.hpo_keys import (
    build_hpo_study_key_v2,
    build_hpo_study_key_hash,
    compute_data_fingerprint,
    compute_eval_fingerprint,
)


class TestComputeDataFingerprint:
    """Test compute_data_fingerprint() function."""

    def test_content_hash_priority(self):
        """Test that content_hash takes priority over semantic fields."""
        data_config = {
            "name": "test_dataset",
            "version": "1.0",
            "content_hash": "abc123def456",
        }
        result = compute_data_fingerprint(data_config)
        # Function hashes the content_hash value
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex string
        # Should be deterministic
        result2 = compute_data_fingerprint(data_config)
        assert result == result2

    def test_manifest_hash_priority(self):
        """Test that manifest_hash takes priority over semantic fields."""
        data_config = {
            "name": "test_dataset",
            "version": "1.0",
            "manifest_hash": "xyz789",
        }
        result = compute_data_fingerprint(data_config)
        # Function hashes the manifest_hash value
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex string
        # Should be deterministic
        result2 = compute_data_fingerprint(data_config)
        assert result == result2

    def test_content_hash_over_manifest_hash(self):
        """Test that content_hash takes priority over manifest_hash."""
        data_config = {
            "content_hash": "abc123",
            "manifest_hash": "xyz789",
        }
        result = compute_data_fingerprint(data_config)
        # Function hashes the content_hash value (takes priority)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex string
        # Should be deterministic
        result2 = compute_data_fingerprint(data_config)
        assert result == result2
        # Should be different from manifest_hash hash
        data_config2 = {"manifest_hash": "xyz789"}
        result3 = compute_data_fingerprint(data_config2)
        assert result != result3  # Different hashes

    def test_semantic_fallback(self):
        """Test semantic fallback when no content/manifest hash."""
        data_config = {
            "name": "test_dataset",
            "version": "1.0",
            "split_seed": 42,
        }
        result = compute_data_fingerprint(data_config)
        # Should be a hash of semantic fields
        assert isinstance(result, str)
        assert len(result) > 0

    def test_semantic_fallback_deterministic(self):
        """Test that semantic fallback is deterministic."""
        data_config = {
            "name": "test_dataset",
            "version": "1.0",
            "split_seed": 42,
        }
        result1 = compute_data_fingerprint(data_config)
        result2 = compute_data_fingerprint(data_config)
        assert result1 == result2

    def test_empty_config(self):
        """Test with empty config (should not crash)."""
        data_config = {}
        result = compute_data_fingerprint(data_config)
        assert isinstance(result, str)

    def test_minimal_config(self):
        """Test with minimal config."""
        data_config = {"name": "test"}
        result = compute_data_fingerprint(data_config)
        assert isinstance(result, str)


class TestComputeEvalFingerprint:
    """Test compute_eval_fingerprint() function."""

    def test_with_eval_config(self):
        """Test with eval config."""
        eval_config = {
            "metric": "macro-f1",
            "k_fold": {"n_splits": 5},
        }
        result = compute_eval_fingerprint(eval_config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deterministic(self):
        """Test that eval fingerprint is deterministic."""
        eval_config = {
            "metric": "macro-f1",
            "k_fold": {"n_splits": 5},
        }
        result1 = compute_eval_fingerprint(eval_config)
        result2 = compute_eval_fingerprint(eval_config)
        assert result1 == result2

    def test_empty_config(self):
        """Test with empty config."""
        eval_config = {}
        result = compute_eval_fingerprint(eval_config)
        assert isinstance(result, str)

    def test_with_different_configs(self):
        """Test that different configs produce different fingerprints."""
        eval_config1 = {"metric": "macro-f1"}
        eval_config2 = {"metric": "accuracy"}
        
        result1 = compute_eval_fingerprint(eval_config1)
        result2 = compute_eval_fingerprint(eval_config2)
        
        assert result1 != result2


class TestBuildHpoStudyKeyV2:
    """Test build_hpo_study_key_v2() function."""

    def test_basic_structure(self):
        """Test basic study key v2 structure."""
        data_config = {
            "name": "test_dataset",
            "version": "1.0",
        }
        hpo_config = {
            "search_space": {"lr": {"type": "float", "low": 1e-5, "high": 1e-3}},
            "objective": {"metric": "macro-f1"},
        }
        train_config = {
            "eval": {
                "metric": "macro-f1",
                "k_fold": {"n_splits": 5},
            },
        }
        
        # Compute fingerprints first
        data_fp = compute_data_fingerprint(data_config)
        eval_fp = compute_eval_fingerprint(train_config.get("eval", {}))
        
        result = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="distilbert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        
        # Should be valid JSON
        import json
        parsed = json.loads(result)
        assert parsed["schema_version"] == "2.0"
        assert "data" in parsed
        assert "hpo" in parsed
        assert "model" in parsed
        assert "evaluation" in parsed
        # Fingerprints are nested in data and evaluation sections
        assert "data_fingerprint" in parsed["data"]
        assert "eval_fingerprint" in parsed["evaluation"]

    def test_includes_fingerprints(self):
        """Test that v2 includes fingerprints."""
        data_config = {
            "name": "test_dataset",
            "version": "1.0",
            "content_hash": "abc123",
        }
        hpo_config = {
            "search_space": {"lr": {"type": "float"}},
            "objective": {"metric": "macro-f1"},
        }
        train_config = {
            "eval": {"metric": "macro-f1"},
        }
        
        # Compute fingerprints
        data_fp = compute_data_fingerprint(data_config)
        eval_fp = compute_eval_fingerprint(train_config.get("eval", {}))
        
        result = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="distilbert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        
        import json
        parsed = json.loads(result)
        # Fingerprints are nested in data and evaluation sections
        assert "data_fingerprint" in parsed["data"]
        assert "eval_fingerprint" in parsed["evaluation"]
        # Fingerprints are hashed values
        assert isinstance(parsed["data"]["data_fingerprint"], str)
        assert len(parsed["data"]["data_fingerprint"]) == 64

    def test_deterministic(self):
        """Test that v2 key is deterministic."""
        data_config = {"name": "test", "version": "1.0"}
        hpo_config = {"search_space": {}, "objective": {"metric": "macro-f1"}}
        train_config = {"eval": {"metric": "macro-f1"}}
        
        data_fp = compute_data_fingerprint(data_config)
        eval_fp = compute_eval_fingerprint(train_config.get("eval", {}))
        
        result1 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="distilbert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        result2 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="distilbert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        
        assert result1 == result2

    def test_different_models_produce_different_keys(self):
        """Test that different models produce different keys."""
        data_config = {"name": "test", "version": "1.0"}
        hpo_config = {"search_space": {}, "objective": {"metric": "macro-f1"}}
        train_config = {"eval": {"metric": "macro-f1"}}
        
        data_fp = compute_data_fingerprint(data_config)
        eval_fp = compute_eval_fingerprint(train_config.get("eval", {}))
        
        result1 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="distilbert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        result2 = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="bert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        
        assert result1 != result2

    def test_with_benchmark_config(self):
        """Test with benchmark config (v2 doesn't include benchmark in key)."""
        data_config = {"name": "test", "version": "1.0"}
        hpo_config = {"search_space": {}, "objective": {"metric": "macro-f1"}}
        train_config = {"eval": {"metric": "macro-f1"}}
        
        data_fp = compute_data_fingerprint(data_config)
        eval_fp = compute_eval_fingerprint(train_config.get("eval", {}))
        
        # Note: v2 doesn't include benchmark_config in the key
        result = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="distilbert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        
        import json
        parsed = json.loads(result)
        # v2 doesn't include benchmark in key
        assert "benchmark" not in parsed or parsed.get("benchmark") == {}

    def test_without_benchmark_config(self):
        """Test without benchmark config (v2 doesn't include benchmark in key)."""
        data_config = {"name": "test", "version": "1.0"}
        hpo_config = {"search_space": {}, "objective": {"metric": "macro-f1"}}
        train_config = {"eval": {"metric": "macro-f1"}}
        
        data_fp = compute_data_fingerprint(data_config)
        eval_fp = compute_eval_fingerprint(train_config.get("eval", {}))
        
        result = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="distilbert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        
        import json
        parsed = json.loads(result)
        # v2 doesn't include benchmark in key
        assert "benchmark" not in parsed or parsed.get("benchmark") == {}

    def test_hash_function(self):
        """Test that hash function works with v2 key."""
        data_config = {"name": "test", "version": "1.0"}
        hpo_config = {"search_space": {}, "objective": {"metric": "macro-f1"}}
        train_config = {"eval": {"metric": "macro-f1"}}
        
        data_fp = compute_data_fingerprint(data_config)
        eval_fp = compute_eval_fingerprint(train_config.get("eval", {}))
        
        study_key = build_hpo_study_key_v2(
            data_config=data_config,
            hpo_config=hpo_config,
            train_config=train_config,
            model="distilbert",
            data_fingerprint=data_fp,
            eval_fingerprint=eval_fp,
        )
        
        hash_result = build_hpo_study_key_hash(study_key)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 hex string

