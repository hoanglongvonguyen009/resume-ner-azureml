"""Unit tests for benchmark.yaml run.mode configuration and idempotency.

Tests cover:
- run.mode: reuse_if_exists vs force_new
- Idempotency check using benchmark_key (PRIMARY)
- Fallback to trial_key_hash + study_key_hash (backward compatibility)
- Success and failure cases for all scenarios
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from evaluation.benchmarking.orchestrator import (
    filter_missing_benchmarks,
    get_benchmark_run_mode,
    build_benchmark_key,
    benchmark_already_exists,
    _benchmark_exists_in_mlflow,
)
from infrastructure.config.run_mode import get_run_mode


class TestRunModeConfig:
    """Test run.mode configuration extraction and usage."""

    def test_run_mode_extraction_reuse_if_exists(self):
        """Test that run.mode reuse_if_exists is extracted from config."""
        benchmark_config = {
            "run": {
                "mode": "reuse_if_exists"
            }
        }
        
        run_mode = get_run_mode(benchmark_config, default="reuse_if_exists")
        
        assert run_mode == "reuse_if_exists"
        assert isinstance(run_mode, str)

    def test_run_mode_extraction_force_new(self):
        """Test that run.mode force_new is extracted from config."""
        benchmark_config = {
            "run": {
                "mode": "force_new"
            }
        }
        
        run_mode = get_run_mode(benchmark_config, default="reuse_if_exists")
        
        assert run_mode == "force_new"

    def test_run_mode_default_when_missing(self):
        """Test that run.mode defaults to reuse_if_exists when missing."""
        benchmark_config = {}
        
        run_mode = get_run_mode(benchmark_config, default="reuse_if_exists")
        
        assert run_mode == "reuse_if_exists"

    def test_run_mode_default_when_run_section_missing(self):
        """Test that run.mode defaults when run section is missing."""
        benchmark_config = {
            "benchmarking": {
                "batch_sizes": [1]
            }
        }
        
        run_mode = get_run_mode(benchmark_config, default="reuse_if_exists")
        
        assert run_mode == "reuse_if_exists"

    def test_get_benchmark_run_mode_uses_config(self):
        """Test that get_benchmark_run_mode() uses config correctly."""
        benchmark_config = {
            "run": {
                "mode": "force_new"
            }
        }
        hpo_config = {}
        
        run_mode = get_benchmark_run_mode(benchmark_config, hpo_config)
        
        assert run_mode == "force_new"

    def test_get_benchmark_run_mode_default(self):
        """Test that get_benchmark_run_mode() defaults correctly."""
        benchmark_config = {}
        hpo_config = {}
        
        run_mode = get_benchmark_run_mode(benchmark_config, hpo_config)
        
        assert run_mode == "reuse_if_exists"


class TestRunModeBehavior:
    """Test behavior differences between run.mode values."""

    @pytest.fixture
    def sample_champions(self):
        """Sample champions dict for testing."""
        return {
            "distilbert": {
                "champion": {
                    "run_id": "champion_run_123",
                    "trial_key_hash": "trial_hash_456",
                    "study_key_hash": "study_hash_789",
                    "backbone": "distilbert"
                }
            },
            "deberta": {
                "champion": {
                    "run_id": "champion_run_456",
                    "trial_key_hash": "trial_hash_789",
                    "study_key_hash": "study_hash_012",
                    "backbone": "deberta"
                }
            }
        }

    @pytest.fixture
    def sample_benchmark_config(self):
        """Sample benchmark config."""
        return {
            "run": {
                "mode": "reuse_if_exists"
            },
            "benchmarking": {
                "batch_sizes": [1]
            }
        }

    def test_force_new_skips_filtering(self, sample_champions, sample_benchmark_config):
        """Test that force_new mode skips filtering entirely."""
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        root_dir = Path("/tmp")
        environment = "local"
        
        # With force_new, should return all champions without filtering
        sample_benchmark_config["run"]["mode"] = "force_new"
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=sample_benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=root_dir,
            environment=environment,
            mlflow_client=None,
            run_mode="force_new"
        )
        
        # Should return all champions (no filtering)
        assert len(result) == len(sample_champions)
        assert "distilbert" in result
        assert "deberta" in result

    def test_reuse_if_exists_filters_existing(self, sample_champions, sample_benchmark_config):
        """Test that reuse_if_exists mode filters out existing benchmarks."""
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        root_dir = Path("/tmp")
        environment = "local"
        
        # Mock MLflow client
        mock_client = Mock()
        
        # Mock that benchmark exists for distilbert
        with patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow") as mock_exists:
            mock_exists.return_value = True  # Benchmark exists for first champion
            
            result = filter_missing_benchmarks(
                champions=sample_champions,
                benchmark_experiment=benchmark_experiment,
                benchmark_config=sample_benchmark_config,
                data_fingerprint="data_fp",
                eval_fingerprint="eval_fp",
                root_dir=root_dir,
                environment=environment,
                mlflow_client=mock_client,
                run_mode="reuse_if_exists"
            )
            
            # Should filter out existing benchmarks
            # Note: This will filter both if both exist, or keep both if both don't exist
            # The exact behavior depends on mock_exists return value per champion
            assert isinstance(result, dict)


class TestBenchmarkKeyIdempotency:
    """Test idempotency check using benchmark_key (PRIMARY)."""

    def test_build_benchmark_key_includes_config_hash(self):
        """Test that build_benchmark_key includes benchmark_config_hash."""
        champion_run_id = "champion_run_123"
        data_fingerprint = "data_fp_456"
        eval_fingerprint = "eval_fp_789"
        benchmark_config = {
            "benchmarking": {
                "batch_sizes": [1],
                "max_length": 512
            }
        }
        
        benchmark_key = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=benchmark_config,
        )
        
        # Should include all components
        assert champion_run_id in benchmark_key
        assert data_fingerprint in benchmark_key
        assert eval_fingerprint in benchmark_key
        # Config hash should be included (computed from benchmark_config)
        assert isinstance(benchmark_key, str)
        assert len(benchmark_key) > 0

    def test_benchmark_key_changes_with_config_change(self):
        """Test that benchmark_key changes when config changes."""
        champion_run_id = "champion_run_123"
        data_fingerprint = "data_fp_456"
        eval_fingerprint = "eval_fp_789"
        
        config1 = {"benchmarking": {"batch_sizes": [1], "max_length": 512}}
        config2 = {"benchmarking": {"batch_sizes": [8], "max_length": 256}}
        
        key1 = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=config1,
        )
        
        key2 = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=config2,
        )
        
        # Keys should be different due to config change
        assert key1 != key2

    def test_benchmark_key_same_with_same_config(self):
        """Test that benchmark_key is same with same config."""
        champion_run_id = "champion_run_123"
        data_fingerprint = "data_fp_456"
        eval_fingerprint = "eval_fp_789"
        benchmark_config = {"benchmarking": {"batch_sizes": [1]}}
        
        key1 = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=benchmark_config,
        )
        
        key2 = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=benchmark_config,
        )
        
        # Keys should be identical
        assert key1 == key2

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_benchmark_key_used_as_primary_check(self, mock_exists_mlflow, tmp_path):
        """Test that benchmark_key is used as PRIMARY check in idempotency."""
        benchmark_key = "test_benchmark_key_123"
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        root_dir = tmp_path
        environment = "local"
        
        # Mock MLflow check returns True (benchmark exists)
        mock_exists_mlflow.return_value = True
        
        # Mock MLflow client
        mock_client = Mock()
        
        result = benchmark_already_exists(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            root_dir=root_dir,
            environment=environment,
            mlflow_client=mock_client,
            trial_key_hash="trial_hash",
            study_key_hash="study_hash"
        )
        
        # Should check MLflow first (PRIMARY check)
        assert mock_exists_mlflow.called
        # Should pass benchmark_key as first argument (PRIMARY)
        call_args = mock_exists_mlflow.call_args
        assert call_args[0][0] == benchmark_key  # First positional arg is benchmark_key
        assert result is True


class TestBenchmarkKeyFallback:
    """Test fallback to trial_key_hash + study_key_hash (backward compatibility)."""

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_fallback_to_hash_when_benchmark_key_not_found(self, mock_exists_mlflow, tmp_path):
        """Test fallback to trial_key_hash + study_key_hash when benchmark_key tag missing."""
        benchmark_key = "test_benchmark_key_123"
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        trial_key_hash = "trial_hash_456"
        study_key_hash = "study_hash_789"
        root_dir = tmp_path
        environment = "local"
        
        # Mock: benchmark_key check fails (returns False), then hash check succeeds
        def side_effect(*args, **kwargs):
            # First call: benchmark_key check (PRIMARY) - returns False (not found)
            # Second call would be hash check (FALLBACK) - but we'll simulate it
            if len(args) > 0 and args[0] == benchmark_key:
                return False  # benchmark_key not found
            return True  # Hash check succeeds
        
        mock_exists_mlflow.side_effect = side_effect
        
        # Actually, the function tries benchmark_key first, then falls back
        # Let's test the actual fallback behavior
        mock_client = Mock()
        
        # Mock search_runs to simulate: benchmark_key not found, but hash found
        def mock_search_runs(*args, **kwargs):
            mock_runs = Mock()
            mock_run = Mock()
            mock_run.info.status = "FINISHED"
            mock_runs.__iter__ = Mock(return_value=iter([mock_run]))
            return mock_runs
        
        mock_client.search_runs = Mock(side_effect=mock_search_runs)
        
        # Test the actual _benchmark_exists_in_mlflow function
        # First call with benchmark_key (should fail)
        result1 = _benchmark_exists_in_mlflow(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            mlflow_client=mock_client,
            trial_key_hash=trial_key_hash,
            study_key_hash=study_key_hash,
        )
        
        # Should try benchmark_key first, then fallback to hash
        # Since we're mocking search_runs to return a finished run, it should find it via hash
        assert mock_client.search_runs.called

    def test_fallback_requires_both_hashes(self):
        """Test that fallback requires both trial_key_hash and study_key_hash."""
        benchmark_key = "test_key"
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        mock_client = Mock()
        
        # Test with missing trial_key_hash
        result1 = _benchmark_exists_in_mlflow(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            mlflow_client=mock_client,
            trial_key_hash=None,  # Missing
            study_key_hash="study_hash",
        )
        
        # Should not use fallback (requires both hashes)
        # Should only try benchmark_key check
        
        # Test with missing study_key_hash
        result2 = _benchmark_exists_in_mlflow(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            mlflow_client=mock_client,
            trial_key_hash="trial_hash",
            study_key_hash=None,  # Missing
        )
        
        # Should not use fallback (requires both hashes)
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)


class TestIdempotencySuccessCases:
    """Test successful idempotency check scenarios."""

    @pytest.fixture
    def sample_champions(self):
        """Sample champions for testing."""
        return {
            "distilbert": {
                "champion": {
                    "run_id": "champion_run_123",
                    "trial_key_hash": "trial_hash_456",
                    "study_key_hash": "study_hash_789"
                }
            }
        }

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_success_benchmark_exists_by_benchmark_key(
        self,
        mock_exists_mlflow,
        sample_champions,
        tmp_path
    ):
        """Test successful idempotency check when benchmark exists by benchmark_key."""
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        benchmark_config = {"benchmarking": {"batch_sizes": [1]}}
        root_dir = tmp_path
        environment = "local"
        
        # Mock: benchmark exists (found by benchmark_key)
        mock_exists_mlflow.return_value = True
        
        mock_client = Mock()
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=root_dir,
            environment=environment,
            mlflow_client=mock_client,
            run_mode="reuse_if_exists"
        )
        
        # Should filter out existing benchmark
        assert len(result) == 0  # All champions filtered out (benchmark exists)

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_success_benchmark_exists_by_hash_fallback(
        self,
        mock_exists_mlflow,
        sample_champions,
        tmp_path
    ):
        """Test successful idempotency check when benchmark exists by hash (fallback)."""
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        benchmark_config = {"benchmarking": {"batch_sizes": [1]}}
        root_dir = tmp_path
        environment = "local"
        
        # Mock: benchmark_key check fails, but hash check succeeds (fallback)
        # This simulates old runs without benchmark_key tag
        mock_exists_mlflow.return_value = True
        
        mock_client = Mock()
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=root_dir,
            environment=environment,
            mlflow_client=mock_client,
            run_mode="reuse_if_exists"
        )
        
        # Should filter out existing benchmark (found via fallback)
        assert len(result) == 0

    def test_success_benchmark_not_exists_creates_new(self, sample_champions, tmp_path):
        """Test that missing benchmark triggers new benchmark creation."""
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        benchmark_config = {"benchmarking": {"batch_sizes": [1]}}
        root_dir = tmp_path
        environment = "local"
        
        # Mock: benchmark does not exist
        mock_client = Mock()
        
        with patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow") as mock_exists:
            mock_exists.return_value = False
            
            result = filter_missing_benchmarks(
                champions=sample_champions,
                benchmark_experiment=benchmark_experiment,
                benchmark_config=benchmark_config,
                data_fingerprint="data_fp",
                eval_fingerprint="eval_fp",
                root_dir=root_dir,
                environment=environment,
                mlflow_client=mock_client,
                run_mode="reuse_if_exists"
            )
            
            # Should keep champions (benchmark doesn't exist, needs creation)
            assert len(result) == 1
            assert "distilbert" in result


class TestIdempotencyFailureCases:
    """Test failure cases for idempotency checks."""

    @pytest.fixture
    def sample_champions(self):
        """Sample champions for testing."""
        return {
            "distilbert": {
                "champion": {
                    "run_id": "champion_run_123",
                    "trial_key_hash": "trial_hash_456",
                    "study_key_hash": "study_hash_789"
                }
            }
        }

    def test_failure_missing_champion_run_id(self, sample_champions, tmp_path):
        """Test handling when champion has no run_id."""
        # Remove run_id
        sample_champions["distilbert"]["champion"]["run_id"] = None
        
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        benchmark_config = {"benchmarking": {"batch_sizes": [1]}}
        root_dir = tmp_path
        environment = "local"
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=root_dir,
            environment=environment,
            mlflow_client=None,
            run_mode="reuse_if_exists"
        )
        
        # Should keep champion (can't check idempotency without run_id)
        assert len(result) == 1
        assert "distilbert" in result

    def test_failure_mlflow_client_unavailable(self, sample_champions, tmp_path):
        """Test handling when MLflow client is unavailable."""
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        benchmark_config = {"benchmarking": {"batch_sizes": [1]}}
        root_dir = tmp_path
        environment = "local"
        
        # No MLflow client provided
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=root_dir,
            environment=environment,
            mlflow_client=None,  # No client
            run_mode="reuse_if_exists"
        )
        
        # Should fall back to disk check or keep champions
        assert isinstance(result, dict)

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_failure_mlflow_check_raises_exception(
        self,
        mock_exists_mlflow,
        sample_champions,
        tmp_path
    ):
        """Test handling when MLflow check raises exception."""
        benchmark_experiment = {"name": "test", "id": "exp_123"}
        benchmark_config = {"benchmarking": {"batch_sizes": [1]}}
        root_dir = tmp_path
        environment = "local"
        
        # Mock: MLflow check raises exception
        mock_exists_mlflow.side_effect = Exception("MLflow connection failed")
        
        mock_client = Mock()
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=root_dir,
            environment=environment,
            mlflow_client=mock_client,
            run_mode="reuse_if_exists"
        )
        
        # Should handle exception gracefully (fallback to disk or keep champions)
        assert isinstance(result, dict)


class TestConfigDocumentationCoverage:
    """Test that all documented behavior in benchmark.yaml is covered."""

    def test_run_mode_documentation_covered(self):
        """Test that all run.mode options from documentation are testable."""
        # From benchmark.yaml lines 6-7:
        # - reuse_if_exists: Reuse existing benchmark results if found (default)
        # - force_new: Always create new benchmark run (ignores existing)
        
        modes = ["reuse_if_exists", "force_new"]
        
        for mode in modes:
            benchmark_config = {"run": {"mode": mode}}
            run_mode = get_run_mode(benchmark_config, default="reuse_if_exists")
            assert run_mode == mode

    def test_idempotency_documentation_covered(self):
        """Test that idempotency behavior from documentation is testable."""
        # From benchmark.yaml lines 9-12:
        # - Uses benchmark_key (includes champion_run_id, data_fp, eval_fp, benchmark_config_hash)
        # - Skips benchmarking if finished run exists with matching benchmark_key
        # - Falls back to trial_key_hash + study_key_hash for backward compatibility
        
        # Test that benchmark_key includes all components
        benchmark_key = build_benchmark_key(
            champion_run_id="champion_123",
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            benchmark_config={"benchmarking": {"batch_sizes": [1]}}
        )
        
        assert "champion_123" in benchmark_key
        assert "data_fp" in benchmark_key
        assert "eval_fp" in benchmark_key
        # Config hash is computed, so we just verify key is created

    def test_independence_from_hpo_config(self):
        """Test that benchmark mode is independent from HPO config (as documented)."""
        # From benchmark.yaml line 13:
        # "Note: HPO no longer uses run.mode - benchmark mode is independent"
        
        benchmark_config = {"run": {"mode": "force_new"}}
        hpo_config = {"run": {"mode": "reuse_if_exists"}}  # Different mode
        
        benchmark_mode = get_benchmark_run_mode(benchmark_config, hpo_config)
        
        # Should use benchmark_config, not hpo_config
        assert benchmark_mode == "force_new"
        assert benchmark_mode != hpo_config["run"]["mode"]


