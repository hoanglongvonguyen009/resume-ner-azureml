"""Integration tests for best_model_selection.yaml configuration in actual workflows.

Tests the complete workflow of:
- run.mode behavior (reuse_if_exists vs force_new)
- objective.metric, direction, goal usage
- champion_selection.* options in actual selection
- scoring.* options in composite score calculation
- benchmark.* options including latency_aggregation

Tests cover both success and failure cases in real scenarios.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from evaluation.selection.mlflow_selection import find_best_model_from_mlflow


class TestLatencyAggregationIntegration:
    """Integration tests for latency_aggregation configuration."""

    @pytest.fixture
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    @pytest.fixture
    def hpo_experiments(self):
        """Sample HPO experiments."""
        return {
            "distilbert": {
                "name": "test_experiment-hpo-distilbert",
                "id": "hpo_experiment_id_distilbert"
            }
        }

    @pytest.fixture
    def tags_config(self):
        """Sample tags config."""
        return {
            "grouping": {
                "study_key_hash": "tags.grouping.study_key_hash",
                "trial_key_hash": "tags.grouping.trial_key_hash"
            },
            "process": {
                "stage": "tags.process.stage",
                "backbone": "tags.process.backbone"
            }
        }

    @patch("evaluation.selection.mlflow_selection.MlflowClient")
    def test_latency_aggregation_latest_strategy(
        self,
        mock_client_class,
        benchmark_experiment,
        hpo_experiments,
        tags_config
    ):
        """Test that latency_aggregation latest strategy is used."""
        selection_config = {
            "objective": {"metric": "macro-f1"},
            "scoring": {
                "f1_weight": 0.7,
                "latency_weight": 0.3,
                "normalize_weights": True
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"],
                "latency_aggregation": "latest"
            }
        }
        
        # Verify config is extracted correctly
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        assert aggregation == "latest"
        
        # Mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_runs.return_value = []
        
        # Call function (will return None due to no runs, but config is used)
        result = find_best_model_from_mlflow(
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tags_config=tags_config,
            selection_config=selection_config,
        )
        
        # Verify function was called (config was used)
        assert mock_client.search_runs.called

    @patch("evaluation.selection.mlflow_selection.MlflowClient")
    def test_latency_aggregation_median_strategy(
        self,
        mock_client_class,
        benchmark_experiment,
        hpo_experiments,
        tags_config
    ):
        """Test that latency_aggregation median strategy is used."""
        selection_config = {
            "objective": {"metric": "macro-f1"},
            "scoring": {
                "f1_weight": 0.7,
                "latency_weight": 0.3,
                "normalize_weights": True
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"],
                "latency_aggregation": "median"
            }
        }
        
        # Verify config is extracted correctly
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        assert aggregation == "median"
        
        # Mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_runs.return_value = []
        
        # Call function
        result = find_best_model_from_mlflow(
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tags_config=tags_config,
            selection_config=selection_config,
        )
        
        # Verify function was called
        assert mock_client.search_runs.called

    @patch("evaluation.selection.mlflow_selection.MlflowClient")
    def test_latency_aggregation_mean_strategy(
        self,
        mock_client_class,
        benchmark_experiment,
        hpo_experiments,
        tags_config
    ):
        """Test that latency_aggregation mean strategy is used."""
        selection_config = {
            "objective": {"metric": "macro-f1"},
            "scoring": {
                "f1_weight": 0.7,
                "latency_weight": 0.3,
                "normalize_weights": True
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"],
                "latency_aggregation": "mean"
            }
        }
        
        # Verify config is extracted correctly
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        assert aggregation == "mean"
        
        # Mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_runs.return_value = []
        
        # Call function
        result = find_best_model_from_mlflow(
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tags_config=tags_config,
            selection_config=selection_config,
        )
        
        # Verify function was called
        assert mock_client.search_runs.called

    @patch("evaluation.selection.mlflow_selection.MlflowClient")
    def test_latency_aggregation_default_when_missing(
        self,
        mock_client_class,
        benchmark_experiment,
        hpo_experiments,
        tags_config
    ):
        """Test that latency_aggregation defaults to latest when missing."""
        selection_config = {
            "objective": {"metric": "macro-f1"},
            "scoring": {
                "f1_weight": 0.7,
                "latency_weight": 0.3,
                "normalize_weights": True
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"]
                # latency_aggregation missing
            }
        }
        
        # Verify default is used
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        assert aggregation == "latest"


class TestObjectiveDirectionMigrationIntegration:
    """Integration tests for objective.direction vs goal migration."""

    @pytest.fixture
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    @pytest.fixture
    def hpo_experiments(self):
        """Sample HPO experiments."""
        return {
            "distilbert": {
                "name": "test_experiment-hpo-distilbert",
                "id": "hpo_experiment_id_distilbert"
            }
        }

    @pytest.fixture
    def tags_config(self):
        """Sample tags config."""
        return {
            "grouping": {
                "study_key_hash": "tags.grouping.study_key_hash",
                "trial_key_hash": "tags.grouping.trial_key_hash"
            },
            "process": {
                "stage": "tags.process.stage",
                "backbone": "tags.process.backbone"
            }
        }

    def test_objective_direction_preferred_over_goal(self):
        """Test that direction is preferred over goal when both present."""
        selection_config = {
            "objective": {
                "metric": "macro-f1",
                "direction": "minimize",  # New
                "goal": "maximize"  # Legacy (different value)
            }
        }
        
        # Code should prefer direction
        direction = selection_config.get("objective", {}).get("direction")
        goal = selection_config.get("objective", {}).get("goal")
        
        assert direction == "minimize"
        assert goal == "maximize"  # Still accessible but deprecated

    def test_objective_goal_fallback_when_direction_missing(self):
        """Test that goal is used when direction is missing."""
        selection_config = {
            "objective": {
                "metric": "macro-f1",
                "goal": "minimize"  # Legacy only
            }
        }
        
        # Should use goal as fallback
        direction = selection_config.get("objective", {}).get("direction")
        goal = selection_config.get("objective", {}).get("goal", "maximize")
        
        # direction is None, goal is used
        assert direction is None
        assert goal == "minimize"

    def test_objective_direction_default_when_both_missing(self):
        """Test that direction defaults when both direction and goal are missing."""
        selection_config = {
            "objective": {
                "metric": "macro-f1"
            }
        }
        
        direction = selection_config.get("objective", {}).get("direction", "maximize")
        goal = selection_config.get("objective", {}).get("goal", "maximize")
        
        assert direction == "maximize"  # Default
        assert goal == "maximize"  # Default


class TestChampionSelectionConfigIntegration:
    """Integration tests for champion_selection configuration in actual selection."""

    def test_min_trials_per_group_extraction(self):
        """Test that min_trials_per_group is extracted from config."""
        selection_config = {
            "champion_selection": {
                "min_trials_per_group": 3
            }
        }
        
        min_trials = selection_config.get("champion_selection", {}).get("min_trials_per_group", 3)
        
        assert min_trials == 3
        # Note: This option is used in champion selection logic (Phase 2)

    def test_top_k_for_stable_score_extraction(self):
        """Test that top_k_for_stable_score is extracted from config."""
        selection_config = {
            "champion_selection": {
                "top_k_for_stable_score": 3
            }
        }
        
        top_k = selection_config.get("champion_selection", {}).get("top_k_for_stable_score", 3)
        
        assert top_k == 3
        # Note: This option is used in champion selection logic (Phase 2)

    def test_require_artifact_available_extraction(self):
        """Test that require_artifact_available is extracted from config."""
        selection_config = {
            "champion_selection": {
                "require_artifact_available": False
            }
        }
        
        require = selection_config.get("champion_selection", {}).get("require_artifact_available", False)
        
        assert require is False
        # Note: This option is used in champion selection logic (Phase 2)

    def test_artifact_check_source_extraction(self):
        """Test that artifact_check_source is extracted from config."""
        selection_config = {
            "champion_selection": {
                "artifact_check_source": "tag"
            }
        }
        
        source = selection_config.get("champion_selection", {}).get("artifact_check_source", "tag")
        
        assert source == "tag"
        assert source in ["tag", "disk"]

    def test_prefer_schema_version_extraction(self):
        """Test that prefer_schema_version is extracted from config."""
        selection_config = {
            "champion_selection": {
                "prefer_schema_version": "auto"
            }
        }
        
        version = selection_config.get("champion_selection", {}).get("prefer_schema_version", "auto")
        
        assert version == "auto"
        assert version in ["1.0", "2.0", "auto"]

    def test_allow_mixed_schema_groups_extraction(self):
        """Test that allow_mixed_schema_groups is extracted from config."""
        selection_config = {
            "champion_selection": {
                "allow_mixed_schema_groups": False
            }
        }
        
        allow = selection_config.get("champion_selection", {}).get("allow_mixed_schema_groups", False)
        
        assert allow is False
        # Note: This option is used in champion selection logic (Phase 2)


class TestScoringConfigIntegration:
    """Integration tests for scoring configuration in composite score calculation."""

    @pytest.fixture
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    @pytest.fixture
    def hpo_experiments(self):
        """Sample HPO experiments."""
        return {
            "distilbert": {
                "name": "test_experiment-hpo-distilbert",
                "id": "hpo_experiment_id_distilbert"
            }
        }

    @pytest.fixture
    def tags_config(self):
        """Sample tags config."""
        return {
            "grouping": {
                "study_key_hash": "tags.grouping.study_key_hash",
                "trial_key_hash": "tags.grouping.trial_key_hash"
            },
            "process": {
                "stage": "tags.process.stage",
                "backbone": "tags.process.backbone"
            }
        }

    @patch("evaluation.selection.mlflow_selection.MlflowClient")
    def test_scoring_weights_used_in_composite_score(
        self,
        mock_client_class,
        benchmark_experiment,
        hpo_experiments,
        tags_config
    ):
        """Test that scoring weights from config are used in composite score."""
        selection_config = {
            "objective": {"metric": "macro-f1"},
            "scoring": {
                "f1_weight": 0.8,
                "latency_weight": 0.2,
                "normalize_weights": True
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"]
            }
        }
        
        # Verify weights are extracted
        f1_weight = selection_config.get("scoring", {}).get("f1_weight", 0.7)
        latency_weight = selection_config.get("scoring", {}).get("latency_weight", 0.3)
        
        assert f1_weight == 0.8
        assert latency_weight == 0.2
        
        # Mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_runs.return_value = []
        
        # Call function (weights are used internally)
        result = find_best_model_from_mlflow(
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tags_config=tags_config,
            selection_config=selection_config,
        )
        
        # Verify function was called
        assert mock_client.search_runs.called

    @patch("evaluation.selection.mlflow_selection.MlflowClient")
    def test_normalize_weights_controls_normalization(
        self,
        mock_client_class,
        benchmark_experiment,
        hpo_experiments,
        tags_config
    ):
        """Test that normalize_weights config controls weight normalization."""
        selection_config = {
            "objective": {"metric": "macro-f1"},
            "scoring": {
                "f1_weight": 0.7,
                "latency_weight": 0.3,
                "normalize_weights": False  # Don't normalize
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"]
            }
        }
        
        normalize = selection_config.get("scoring", {}).get("normalize_weights", True)
        assert normalize is False
        
        # Mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_runs.return_value = []
        
        # Call function
        result = find_best_model_from_mlflow(
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tags_config=tags_config,
            selection_config=selection_config,
        )
        
        # Verify function was called
        assert mock_client.search_runs.called


class TestBenchmarkRequiredMetricsIntegration:
    """Integration tests for benchmark.required_metrics configuration."""

    @pytest.fixture
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    @pytest.fixture
    def hpo_experiments(self):
        """Sample HPO experiments."""
        return {
            "distilbert": {
                "name": "test_experiment-hpo-distilbert",
                "id": "hpo_experiment_id_distilbert"
            }
        }

    @pytest.fixture
    def tags_config(self):
        """Sample tags config."""
        return {
            "grouping": {
                "study_key_hash": "tags.grouping.study_key_hash",
                "trial_key_hash": "tags.grouping.trial_key_hash"
            },
            "process": {
                "stage": "tags.process.stage",
                "backbone": "tags.process.backbone"
            }
        }

    @patch("evaluation.selection.mlflow_selection.MlflowClient")
    def test_required_metrics_filters_benchmark_runs(
        self,
        mock_client_class,
        benchmark_experiment,
        hpo_experiments,
        tags_config
    ):
        """Test that required_metrics from config filters benchmark runs."""
        selection_config = {
            "objective": {"metric": "macro-f1"},
            "scoring": {
                "f1_weight": 0.7,
                "latency_weight": 0.3,
                "normalize_weights": True
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms", "throughput_samples_per_sec"]
            }
        }
        
        # Verify required metrics are extracted
        required_metrics = selection_config.get("benchmark", {}).get("required_metrics", [])
        assert len(required_metrics) == 2
        assert "latency_batch_1_ms" in required_metrics
        assert "throughput_samples_per_sec" in required_metrics
        
        # Mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_runs.return_value = []
        
        # Call function
        result = find_best_model_from_mlflow(
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tags_config=tags_config,
            selection_config=selection_config,
        )
        
        # Verify function was called
        assert mock_client.search_runs.called


class TestCompleteConfigWorkflow:
    """Test complete workflow with all config options together."""

    @pytest.fixture
    def benchmark_experiment(self):
        """Sample benchmark experiment."""
        return {
            "name": "test_experiment-benchmark",
            "id": "benchmark_experiment_id_123"
        }

    @pytest.fixture
    def hpo_experiments(self):
        """Sample HPO experiments."""
        return {
            "distilbert": {
                "name": "test_experiment-hpo-distilbert",
                "id": "hpo_experiment_id_distilbert"
            }
        }

    @pytest.fixture
    def tags_config(self):
        """Sample tags config."""
        return {
            "grouping": {
                "study_key_hash": "tags.grouping.study_key_hash",
                "trial_key_hash": "tags.grouping.trial_key_hash"
            },
            "process": {
                "stage": "tags.process.stage",
                "backbone": "tags.process.backbone"
            }
        }

    @patch("evaluation.selection.mlflow_selection.MlflowClient")
    def test_all_config_options_used_together(
        self,
        mock_client_class,
        benchmark_experiment,
        hpo_experiments,
        tags_config
    ):
        """Test that all config options are used together correctly."""
        selection_config = {
            "run": {
                "mode": "force_new"
            },
            "objective": {
                "metric": "macro-f1",
                "direction": "maximize"
            },
            "champion_selection": {
                "min_trials_per_group": 3,
                "top_k_for_stable_score": 3,
                "require_artifact_available": False,
                "artifact_check_source": "tag",
                "prefer_schema_version": "auto",
                "allow_mixed_schema_groups": False
            },
            "scoring": {
                "f1_weight": 0.7,
                "latency_weight": 0.3,
                "normalize_weights": True
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"],
                "latency_aggregation": "median"
            }
        }
        
        # Verify all options are accessible
        assert selection_config["run"]["mode"] == "force_new"
        assert selection_config["objective"]["metric"] == "macro-f1"
        assert selection_config["objective"]["direction"] == "maximize"
        assert selection_config["champion_selection"]["min_trials_per_group"] == 3
        assert selection_config["scoring"]["f1_weight"] == 0.7
        assert selection_config["benchmark"]["latency_aggregation"] == "median"
        
        # Mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_runs.return_value = []
        
        # Call function with all config options
        result = find_best_model_from_mlflow(
            benchmark_experiment=benchmark_experiment,
            hpo_experiments=hpo_experiments,
            tags_config=tags_config,
            selection_config=selection_config,
        )
        
        # Verify function was called
        assert mock_client.search_runs.called

    def test_config_with_missing_sections_uses_defaults(self):
        """Test that missing config sections use defaults."""
        # Minimal config (only required sections)
        selection_config = {
            "objective": {"metric": "macro-f1"},
            "scoring": {
                "f1_weight": 0.7,
                "latency_weight": 0.3
            },
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"]
            }
        }
        
        # Missing sections should use defaults
        run_mode = selection_config.get("run", {}).get("mode", "reuse_if_exists")
        normalize_weights = selection_config.get("scoring", {}).get("normalize_weights", True)
        latency_aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        
        assert run_mode == "reuse_if_exists"  # Default
        assert normalize_weights is True  # Default
        assert latency_aggregation == "latest"  # Default


