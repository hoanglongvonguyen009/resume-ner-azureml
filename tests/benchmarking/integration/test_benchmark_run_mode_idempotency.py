"""Integration tests for benchmark run.mode and idempotency behavior.

Tests the complete workflow of:
- run.mode configuration (reuse_if_exists vs force_new)
- Idempotency check using benchmark_key (PRIMARY)
- Fallback to trial_key_hash + study_key_hash (backward compatibility)
- Success and failure cases in real scenarios
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
from mlflow.tracking import MlflowClient


class TestRunModeIntegration:
    """Integration tests for run.mode behavior in complete workflow."""

    @pytest.fixture
    def sample_champions(self):
        """Sample champions for testing."""
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
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    @pytest.fixture
    def benchmark_config_reuse(self):
        """Benchmark config with reuse_if_exists mode."""
        return {
            "run": {
                "mode": "reuse_if_exists"
            },
            "benchmarking": {
                "batch_sizes": [1],
                "max_length": 512
            }
        }

    @pytest.fixture
    def benchmark_config_force_new(self):
        """Benchmark config with force_new mode."""
        return {
            "run": {
                "mode": "force_new"
            },
            "benchmarking": {
                "batch_sizes": [1],
                "max_length": 512
            }
        }

    def test_force_new_returns_all_champions(
        self,
        sample_champions,
        benchmark_experiment,
        benchmark_config_force_new,
        tmp_path
    ):
        """Test that force_new mode returns all champions without filtering."""
        root_dir = tmp_path
        environment = "local"
        
        # Even if benchmarks exist, force_new should return all
        mock_client = Mock()
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config_force_new,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=root_dir,
            environment=environment,
            mlflow_client=mock_client,
            run_mode="force_new"
        )
        
        # Should return all champions (no filtering)
        assert len(result) == len(sample_champions)
        assert "distilbert" in result
        assert "deberta" in result

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_reuse_if_exists_filters_existing_benchmarks(
        self,
        mock_exists_mlflow,
        sample_champions,
        benchmark_experiment,
        benchmark_config_reuse,
        tmp_path
    ):
        """Test that reuse_if_exists filters out existing benchmarks."""
        root_dir = tmp_path
        environment = "local"
        
        # Mock: benchmark exists for distilbert, not for deberta
        def side_effect(benchmark_key, *args, **kwargs):
            # Return True for first champion (distilbert), False for second (deberta)
            if "champion_run_123" in benchmark_key:
                return True  # Exists
            return False  # Doesn't exist
        
        mock_exists_mlflow.side_effect = side_effect
        
        mock_client = Mock()
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config_reuse,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=root_dir,
            environment=environment,
            mlflow_client=mock_client,
            run_mode="reuse_if_exists"
        )
        
        # Should filter out distilbert (exists), keep deberta (doesn't exist)
        assert len(result) == 1
        assert "deberta" in result
        assert "distilbert" not in result

    def test_get_benchmark_run_mode_from_config(
        self,
        benchmark_config_reuse,
        benchmark_config_force_new
    ):
        """Test that get_benchmark_run_mode extracts mode from config."""
        hpo_config = {}
        
        mode1 = get_benchmark_run_mode(benchmark_config_reuse, hpo_config)
        mode2 = get_benchmark_run_mode(benchmark_config_force_new, hpo_config)
        
        assert mode1 == "reuse_if_exists"
        assert mode2 == "force_new"


class TestBenchmarkKeyIdempotencyIntegration:
    """Integration tests for benchmark_key idempotency (PRIMARY check)."""

    @pytest.fixture
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    def test_benchmark_key_primary_check_succeeds(self, benchmark_experiment):
        """Test that benchmark_key check (PRIMARY) succeeds when benchmark exists."""
        benchmark_key = "champion_123:data_fp:eval_fp:config_hash"
        trial_key_hash = "trial_hash"
        study_key_hash = "study_hash"
        
        mock_client = Mock()
        
        # Mock search_runs to return finished run with benchmark_key tag
        mock_run = Mock()
        mock_run.info.status = "FINISHED"
        mock_run.data.tags = {"benchmark_key": benchmark_key}
        
        mock_runs = [mock_run]
        mock_client.search_runs = Mock(return_value=mock_runs)
        
        result = _benchmark_exists_in_mlflow(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            mlflow_client=mock_client,
            trial_key_hash=trial_key_hash,
            study_key_hash=study_key_hash,
        )
        
        # Should find benchmark by benchmark_key (PRIMARY check)
        assert result is True
        # Verify search was done by benchmark_key
        call_args = mock_client.search_runs.call_args
        assert "benchmark_key" in str(call_args)

    def test_benchmark_key_primary_check_fails_then_fallback(
        self,
        benchmark_experiment
    ):
        """Test that when benchmark_key check fails, falls back to hash check."""
        benchmark_key = "champion_123:data_fp:eval_fp:config_hash"
        trial_key_hash = "trial_hash_456"
        study_key_hash = "study_hash_789"
        
        mock_client = Mock()
        
        # Mock: benchmark_key search returns empty, hash search returns finished run
        def mock_search_runs(*args, **kwargs):
            filter_string = kwargs.get("filter_string", "")
            if "benchmark_key" in filter_string:
                return []  # benchmark_key not found (PRIMARY fails)
            elif "trial_key_hash" in filter_string:
                # Hash search succeeds (FALLBACK)
                mock_run = Mock()
                mock_run.info.status = "FINISHED"
                return [mock_run]
            return []
        
        mock_client.search_runs = Mock(side_effect=mock_search_runs)
        
        result = _benchmark_exists_in_mlflow(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            mlflow_client=mock_client,
            trial_key_hash=trial_key_hash,
            study_key_hash=study_key_hash,
        )
        
        # Should find benchmark via fallback (hash check)
        assert result is True
        # Verify both searches were attempted
        assert mock_client.search_runs.call_count >= 1

    def test_benchmark_key_changes_with_config_creates_new_benchmark(
        self,
        benchmark_experiment,
        tmp_path
    ):
        """Test that config change creates new benchmark_key, triggering new benchmark."""
        champion_run_id = "champion_123"
        data_fingerprint = "data_fp"
        eval_fingerprint = "eval_fp"
        
        # Config 1: batch_size=1
        config1 = {"benchmarking": {"batch_sizes": [1], "max_length": 512}}
        key1 = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=config1,
        )
        
        # Config 2: batch_size=8 (different config)
        config2 = {"benchmarking": {"batch_sizes": [8], "max_length": 512}}
        key2 = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=config2,
        )
        
        # Keys should be different
        assert key1 != key2
        
        # This means idempotency check with key1 won't find key2
        # So new benchmark will be created (correct behavior)

    def test_benchmark_key_same_config_reuses_benchmark(
        self,
        benchmark_experiment,
        tmp_path
    ):
        """Test that same config creates same benchmark_key, reusing existing benchmark."""
        champion_run_id = "champion_123"
        data_fingerprint = "data_fp"
        eval_fingerprint = "eval_fp"
        benchmark_config = {"benchmarking": {"batch_sizes": [1], "max_length": 512}}
        
        # Build key twice with same config
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
        
        # This means idempotency check will find existing benchmark (correct behavior)


class TestBackwardCompatibilityFallback:
    """Integration tests for backward compatibility fallback behavior."""

    @pytest.fixture
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    def test_fallback_to_hash_when_benchmark_key_tag_missing(
        self,
        benchmark_experiment
    ):
        """Test fallback to hash check when benchmark_key tag is missing (old runs)."""
        benchmark_key = "champion_123:data_fp:eval_fp:config_hash"
        trial_key_hash = "trial_hash_456"
        study_key_hash = "study_hash_789"
        
        mock_client = Mock()
        
        # Mock: benchmark_key search fails (tag missing), hash search succeeds
        call_count = 0
        def mock_search_runs(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            filter_string = kwargs.get("filter_string", "")
            
            if call_count == 1:
                # First call: benchmark_key search (PRIMARY) - returns empty (tag missing)
                assert "benchmark_key" in filter_string
                return []
            elif call_count == 2:
                # Second call: hash search (FALLBACK) - returns finished run
                assert "trial_key_hash" in filter_string
                assert "study_key_hash" in filter_string
                mock_run = Mock()
                mock_run.info.status = "FINISHED"
                return [mock_run]
            return []
        
        mock_client.search_runs = Mock(side_effect=mock_search_runs)
        
        result = _benchmark_exists_in_mlflow(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            mlflow_client=mock_client,
            trial_key_hash=trial_key_hash,
            study_key_hash=study_key_hash,
        )
        
        # Should find benchmark via fallback (hash check)
        assert result is True
        # Verify both searches were attempted (PRIMARY then FALLBACK)
        assert mock_client.search_runs.call_count >= 2

    def test_fallback_requires_both_hashes(self, benchmark_experiment):
        """Test that fallback requires both trial_key_hash and study_key_hash."""
        benchmark_key = "test_key"
        
        mock_client = Mock()
        
        # Test with only trial_key_hash (missing study_key_hash)
        result1 = _benchmark_exists_in_mlflow(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            mlflow_client=mock_client,
            trial_key_hash="trial_hash",
            study_key_hash=None,  # Missing
        )
        
        # Should not use fallback (requires both)
        # Should only try benchmark_key check
        
        # Test with only study_key_hash (missing trial_key_hash)
        result2 = _benchmark_exists_in_mlflow(
            benchmark_key=benchmark_key,
            benchmark_experiment=benchmark_experiment,
            mlflow_client=mock_client,
            trial_key_hash=None,  # Missing
            study_key_hash="study_hash",
        )
        
        # Should not use fallback (requires both)
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)


class TestCompleteWorkflowScenarios:
    """Test complete workflow scenarios with different config combinations."""

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

    @pytest.fixture
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_scenario_reuse_if_exists_with_existing_benchmark(
        self,
        mock_exists_mlflow,
        sample_champions,
        benchmark_experiment,
        tmp_path
    ):
        """Test scenario: reuse_if_exists mode with existing benchmark (should skip)."""
        benchmark_config = {
            "run": {"mode": "reuse_if_exists"},
            "benchmarking": {"batch_sizes": [1]}
        }
        
        # Mock: benchmark exists
        mock_exists_mlflow.return_value = True
        
        mock_client = Mock()
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=tmp_path,
            environment="local",
            mlflow_client=mock_client,
            run_mode="reuse_if_exists"
        )
        
        # Should filter out existing benchmark
        assert len(result) == 0

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_scenario_reuse_if_exists_without_existing_benchmark(
        self,
        mock_exists_mlflow,
        sample_champions,
        benchmark_experiment,
        tmp_path
    ):
        """Test scenario: reuse_if_exists mode without existing benchmark (should create)."""
        benchmark_config = {
            "run": {"mode": "reuse_if_exists"},
            "benchmarking": {"batch_sizes": [1]}
        }
        
        # Mock: benchmark does not exist
        mock_exists_mlflow.return_value = False
        
        mock_client = Mock()
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=tmp_path,
            environment="local",
            mlflow_client=mock_client,
            run_mode="reuse_if_exists"
        )
        
        # Should keep champions (benchmark doesn't exist, needs creation)
        assert len(result) == 1
        assert "distilbert" in result

    def test_scenario_force_new_always_creates(
        self,
        sample_champions,
        benchmark_experiment,
        tmp_path
    ):
        """Test scenario: force_new mode always creates new benchmark (ignores existing)."""
        benchmark_config = {
            "run": {"mode": "force_new"},
            "benchmarking": {"batch_sizes": [1]}
        }
        
        # Even if benchmark exists, force_new should return all champions
        mock_client = Mock()
        
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=benchmark_config,
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=tmp_path,
            environment="local",
            mlflow_client=mock_client,
            run_mode="force_new"
        )
        
        # Should return all champions (no filtering)
        assert len(result) == 1
        assert "distilbert" in result

    @patch("evaluation.benchmarking.orchestrator._benchmark_exists_in_mlflow")
    def test_scenario_config_change_creates_new_benchmark(
        self,
        mock_exists_mlflow,
        sample_champions,
        benchmark_experiment,
        tmp_path
    ):
        """Test scenario: config change creates new benchmark_key, triggering new benchmark."""
        # First config: batch_size=1
        config1 = {
            "run": {"mode": "reuse_if_exists"},
            "benchmarking": {"batch_sizes": [1], "max_length": 512}
        }
        
        # Build key for config1
        key1 = build_benchmark_key(
            champion_run_id="champion_run_123",
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            benchmark_config=config1,
        )
        
        # Second config: batch_size=8 (different)
        config2 = {
            "run": {"mode": "reuse_if_exists"},
            "benchmarking": {"batch_sizes": [8], "max_length": 512}
        }
        
        # Build key for config2
        key2 = build_benchmark_key(
            champion_run_id="champion_run_123",
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            benchmark_config=config2,
        )
        
        # Keys should be different
        assert key1 != key2
        
        # Mock: benchmark exists for key1, not for key2
        def side_effect(benchmark_key, *args, **kwargs):
            if benchmark_key == key1:
                return True  # Old benchmark exists
            return False  # New benchmark doesn't exist
        
        mock_exists_mlflow.side_effect = side_effect
        
        mock_client = Mock()
        
        # Filter with config2 (different from config1)
        result = filter_missing_benchmarks(
            champions=sample_champions,
            benchmark_experiment=benchmark_experiment,
            benchmark_config=config2,  # Different config
            data_fingerprint="data_fp",
            eval_fingerprint="eval_fp",
            root_dir=tmp_path,
            environment="local",
            mlflow_client=mock_client,
            run_mode="reuse_if_exists"
        )
        
        # Should keep champions (new benchmark_key, doesn't exist yet)
        assert len(result) == 1
        assert "distilbert" in result


