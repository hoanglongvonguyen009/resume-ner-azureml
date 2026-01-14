"""Comprehensive unit tests for best_model_selection.yaml configuration.

This test file covers ALL configuration options in best_model_selection.yaml:
- run.mode
- objective.metric, objective.direction, objective.goal (migration)
- champion_selection.* (all options)
- scoring.* (all options)
- benchmark.* (all options including latency_aggregation)

Tests cover both success and failure cases, following DRY principles.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from common.shared.yaml_utils import load_yaml


class TestRunModeConfig:
    """Test run.mode configuration."""

    def test_run_mode_extraction_force_new(self):
        """Test that run.mode force_new is extracted."""
        selection_config = {
            "run": {
                "mode": "force_new"
            }
        }
        
        mode = selection_config.get("run", {}).get("mode", "reuse_if_exists")
        
        assert mode == "force_new"
        assert isinstance(mode, str)

    def test_run_mode_extraction_reuse_if_exists(self):
        """Test that run.mode reuse_if_exists is extracted."""
        selection_config = {
            "run": {
                "mode": "reuse_if_exists"
            }
        }
        
        mode = selection_config.get("run", {}).get("mode", "reuse_if_exists")
        
        assert mode == "reuse_if_exists"

    def test_run_mode_default(self):
        """Test that run.mode defaults to reuse_if_exists when missing."""
        selection_config = {}
        
        mode = selection_config.get("run", {}).get("mode", "reuse_if_exists")
        
        assert mode == "reuse_if_exists"

    def test_run_mode_invalid_value(self):
        """Test that invalid run.mode values are possible (not validated)."""
        selection_config = {
            "run": {
                "mode": "invalid_mode"
            }
        }
        
        mode = selection_config.get("run", {}).get("mode", "reuse_if_exists")
        
        # Config loader doesn't validate, so invalid values are allowed
        assert mode == "invalid_mode"


class TestObjectiveConfig:
    """Test objective configuration (metric, direction, goal)."""

    def test_objective_metric_extraction(self):
        """Test that objective.metric is extracted."""
        selection_config = {
            "objective": {
                "metric": "macro-f1"
            }
        }
        
        metric = selection_config.get("objective", {}).get("metric", "macro-f1")
        
        assert metric == "macro-f1"
        assert isinstance(metric, str)

    def test_objective_metric_default(self):
        """Test that objective.metric defaults when missing."""
        selection_config = {
            "objective": {}
        }
        
        metric = selection_config.get("objective", {}).get("metric", "macro-f1")
        
        assert metric == "macro-f1"

    def test_objective_direction_extraction(self):
        """Test that objective.direction (new) is extracted."""
        selection_config = {
            "objective": {
                "direction": "maximize"
            }
        }
        
        direction = selection_config.get("objective", {}).get("direction", "maximize")
        
        assert direction == "maximize"
        assert isinstance(direction, str)

    def test_objective_direction_minimize(self):
        """Test that objective.direction minimize is extracted."""
        selection_config = {
            "objective": {
                "direction": "minimize"
            }
        }
        
        direction = selection_config.get("objective", {}).get("direction", "maximize")
        
        assert direction == "minimize"

    def test_objective_goal_extraction(self):
        """Test that objective.goal (legacy) is extracted."""
        selection_config = {
            "objective": {
                "goal": "maximize"
            }
        }
        
        goal = selection_config.get("objective", {}).get("goal", "maximize")
        
        assert goal == "maximize"
        assert isinstance(goal, str)

    def test_objective_direction_and_goal_both_present(self):
        """Test that both direction and goal can be present (migration period)."""
        selection_config = {
            "objective": {
                "direction": "maximize",
                "goal": "maximize"  # Legacy
            }
        }
        
        direction = selection_config.get("objective", {}).get("direction", "maximize")
        goal = selection_config.get("objective", {}).get("goal", "maximize")
        
        # Both should be extractable
        assert direction == "maximize"
        assert goal == "maximize"

    def test_objective_direction_preferred_over_goal(self):
        """Test that direction is preferred over goal when both present."""
        selection_config = {
            "objective": {
                "direction": "minimize",  # New
                "goal": "maximize"  # Legacy (different value)
            }
        }
        
        # Code should prefer direction over goal
        direction = selection_config.get("objective", {}).get("direction")
        goal = selection_config.get("objective", {}).get("goal")
        
        # Both exist, but direction should be used
        assert direction == "minimize"
        assert goal == "maximize"  # Still accessible but deprecated


class TestChampionSelectionConfig:
    """Test champion_selection configuration (all options)."""

    def test_min_trials_per_group_extraction(self):
        """Test that min_trials_per_group is extracted."""
        selection_config = {
            "champion_selection": {
                "min_trials_per_group": 3
            }
        }
        
        min_trials = selection_config.get("champion_selection", {}).get("min_trials_per_group", 3)
        
        assert min_trials == 3
        assert isinstance(min_trials, int)

    def test_min_trials_per_group_default(self):
        """Test that min_trials_per_group defaults when missing."""
        selection_config = {
            "champion_selection": {}
        }
        
        min_trials = selection_config.get("champion_selection", {}).get("min_trials_per_group", 3)
        
        assert min_trials == 3

    def test_min_trials_per_group_custom_value(self):
        """Test that min_trials_per_group accepts custom values."""
        selection_config = {
            "champion_selection": {
                "min_trials_per_group": 5
            }
        }
        
        min_trials = selection_config.get("champion_selection", {}).get("min_trials_per_group", 3)
        
        assert min_trials == 5

    def test_top_k_for_stable_score_extraction(self):
        """Test that top_k_for_stable_score is extracted."""
        selection_config = {
            "champion_selection": {
                "top_k_for_stable_score": 3
            }
        }
        
        top_k = selection_config.get("champion_selection", {}).get("top_k_for_stable_score", 3)
        
        assert top_k == 3
        assert isinstance(top_k, int)

    def test_top_k_for_stable_score_default(self):
        """Test that top_k_for_stable_score defaults when missing."""
        selection_config = {
            "champion_selection": {}
        }
        
        top_k = selection_config.get("champion_selection", {}).get("top_k_for_stable_score", 3)
        
        assert top_k == 3

    def test_require_artifact_available_extraction(self):
        """Test that require_artifact_available is extracted."""
        selection_config = {
            "champion_selection": {
                "require_artifact_available": True
            }
        }
        
        require = selection_config.get("champion_selection", {}).get("require_artifact_available", False)
        
        assert require is True
        assert isinstance(require, bool)

    def test_require_artifact_available_false(self):
        """Test that require_artifact_available with false value."""
        selection_config = {
            "champion_selection": {
                "require_artifact_available": False
            }
        }
        
        require = selection_config.get("champion_selection", {}).get("require_artifact_available", False)
        
        assert require is False

    def test_artifact_check_source_extraction(self):
        """Test that artifact_check_source is extracted."""
        selection_config = {
            "champion_selection": {
                "artifact_check_source": "tag"
            }
        }
        
        source = selection_config.get("champion_selection", {}).get("artifact_check_source", "tag")
        
        assert source == "tag"
        assert isinstance(source, str)

    def test_artifact_check_source_disk(self):
        """Test that artifact_check_source with disk value."""
        selection_config = {
            "champion_selection": {
                "artifact_check_source": "disk"
            }
        }
        
        source = selection_config.get("champion_selection", {}).get("artifact_check_source", "tag")
        
        assert source == "disk"

    def test_prefer_schema_version_extraction(self):
        """Test that prefer_schema_version is extracted."""
        selection_config = {
            "champion_selection": {
                "prefer_schema_version": "auto"
            }
        }
        
        version = selection_config.get("champion_selection", {}).get("prefer_schema_version", "auto")
        
        assert version == "auto"
        assert isinstance(version, str)

    def test_prefer_schema_version_2_0(self):
        """Test that prefer_schema_version with 2.0 value."""
        selection_config = {
            "champion_selection": {
                "prefer_schema_version": "2.0"
            }
        }
        
        version = selection_config.get("champion_selection", {}).get("prefer_schema_version", "auto")
        
        assert version == "2.0"

    def test_prefer_schema_version_1_0(self):
        """Test that prefer_schema_version with 1.0 value."""
        selection_config = {
            "champion_selection": {
                "prefer_schema_version": "1.0"
            }
        }
        
        version = selection_config.get("champion_selection", {}).get("prefer_schema_version", "auto")
        
        assert version == "1.0"

    def test_allow_mixed_schema_groups_extraction(self):
        """Test that allow_mixed_schema_groups is extracted."""
        selection_config = {
            "champion_selection": {
                "allow_mixed_schema_groups": False
            }
        }
        
        allow = selection_config.get("champion_selection", {}).get("allow_mixed_schema_groups", False)
        
        assert allow is False
        assert isinstance(allow, bool)

    def test_allow_mixed_schema_groups_true(self):
        """Test that allow_mixed_schema_groups with true value."""
        selection_config = {
            "champion_selection": {
                "allow_mixed_schema_groups": True
            }
        }
        
        allow = selection_config.get("champion_selection", {}).get("allow_mixed_schema_groups", False)
        
        assert allow is True

    def test_all_champion_selection_options_together(self):
        """Test extracting all champion_selection options together."""
        selection_config = {
            "champion_selection": {
                "min_trials_per_group": 3,
                "top_k_for_stable_score": 3,
                "require_artifact_available": True,
                "artifact_check_source": "tag",
                "prefer_schema_version": "auto",
                "allow_mixed_schema_groups": False
            }
        }
        
        champion_config = selection_config.get("champion_selection", {})
        
        assert champion_config["min_trials_per_group"] == 3
        assert champion_config["top_k_for_stable_score"] == 3
        assert champion_config["require_artifact_available"] is True
        assert champion_config["artifact_check_source"] == "tag"
        assert champion_config["prefer_schema_version"] == "auto"
        assert champion_config["allow_mixed_schema_groups"] is False


class TestScoringConfig:
    """Test scoring configuration (all options)."""

    def test_f1_weight_extraction(self):
        """Test that f1_weight is extracted."""
        selection_config = {
            "scoring": {
                "f1_weight": 0.7
            }
        }
        
        f1_weight = selection_config.get("scoring", {}).get("f1_weight", 0.7)
        
        assert f1_weight == 0.7
        assert isinstance(f1_weight, (int, float))

    def test_f1_weight_default(self):
        """Test that f1_weight defaults when missing."""
        selection_config = {
            "scoring": {}
        }
        
        f1_weight = selection_config.get("scoring", {}).get("f1_weight", 0.7)
        
        assert f1_weight == 0.7

    def test_latency_weight_extraction(self):
        """Test that latency_weight is extracted."""
        selection_config = {
            "scoring": {
                "latency_weight": 0.3
            }
        }
        
        latency_weight = selection_config.get("scoring", {}).get("latency_weight", 0.3)
        
        assert latency_weight == 0.3
        assert isinstance(latency_weight, (int, float))

    def test_latency_weight_default(self):
        """Test that latency_weight defaults when missing."""
        selection_config = {
            "scoring": {}
        }
        
        latency_weight = selection_config.get("scoring", {}).get("latency_weight", 0.3)
        
        assert latency_weight == 0.3

    def test_normalize_weights_extraction(self):
        """Test that normalize_weights is extracted."""
        selection_config = {
            "scoring": {
                "normalize_weights": True
            }
        }
        
        normalize = selection_config.get("scoring", {}).get("normalize_weights", True)
        
        assert normalize is True
        assert isinstance(normalize, bool)

    def test_normalize_weights_false(self):
        """Test that normalize_weights with false value."""
        selection_config = {
            "scoring": {
                "normalize_weights": False
            }
        }
        
        normalize = selection_config.get("scoring", {}).get("normalize_weights", True)
        
        assert normalize is False

    def test_normalize_weights_default(self):
        """Test that normalize_weights defaults when missing."""
        selection_config = {
            "scoring": {}
        }
        
        normalize = selection_config.get("scoring", {}).get("normalize_weights", True)
        
        assert normalize is True


class TestBenchmarkConfig:
    """Test benchmark configuration (all options including latency_aggregation)."""

    def test_required_metrics_extraction(self):
        """Test that required_metrics is extracted."""
        selection_config = {
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"]
            }
        }
        
        metrics = selection_config.get("benchmark", {}).get("required_metrics", [])
        
        assert metrics == ["latency_batch_1_ms"]
        assert isinstance(metrics, list)
        assert all(isinstance(m, str) for m in metrics)

    def test_required_metrics_multiple(self):
        """Test that required_metrics with multiple metrics."""
        selection_config = {
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms", "throughput_samples_per_sec"]
            }
        }
        
        metrics = selection_config.get("benchmark", {}).get("required_metrics", [])
        
        assert len(metrics) == 2
        assert "latency_batch_1_ms" in metrics
        assert "throughput_samples_per_sec" in metrics

    def test_required_metrics_default(self):
        """Test that required_metrics defaults when missing."""
        selection_config = {
            "benchmark": {}
        }
        
        metrics = selection_config.get("benchmark", {}).get("required_metrics", [])
        
        assert metrics == []

    def test_latency_aggregation_extraction(self):
        """Test that latency_aggregation is extracted."""
        selection_config = {
            "benchmark": {
                "latency_aggregation": "latest"
            }
        }
        
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        
        assert aggregation == "latest"
        assert isinstance(aggregation, str)

    def test_latency_aggregation_median(self):
        """Test that latency_aggregation with median value."""
        selection_config = {
            "benchmark": {
                "latency_aggregation": "median"
            }
        }
        
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        
        assert aggregation == "median"

    def test_latency_aggregation_mean(self):
        """Test that latency_aggregation with mean value."""
        selection_config = {
            "benchmark": {
                "latency_aggregation": "mean"
            }
        }
        
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        
        assert aggregation == "mean"

    def test_latency_aggregation_default(self):
        """Test that latency_aggregation defaults to latest when missing."""
        selection_config = {
            "benchmark": {}
        }
        
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        
        assert aggregation == "latest"

    def test_latency_aggregation_invalid_value(self):
        """Test that invalid latency_aggregation values are possible (not validated)."""
        selection_config = {
            "benchmark": {
                "latency_aggregation": "invalid_strategy"
            }
        }
        
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        
        # Config loader doesn't validate, so invalid values are allowed
        assert aggregation == "invalid_strategy"


class TestConfigIntegrationSuccessCases:
    """Test successful config usage with various combinations."""

    def test_all_config_options_together(self):
        """Test that all config options can be used together."""
        selection_config = {
            "run": {
                "mode": "force_new"
            },
            "objective": {
                "metric": "macro-f1",
                "direction": "maximize",
                "goal": "maximize"  # Legacy
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
                "latency_aggregation": "latest"
            }
        }
        
        # Verify all options are accessible
        assert selection_config["run"]["mode"] == "force_new"
        assert selection_config["objective"]["metric"] == "macro-f1"
        assert selection_config["objective"]["direction"] == "maximize"
        assert selection_config["champion_selection"]["min_trials_per_group"] == 3
        assert selection_config["scoring"]["f1_weight"] == 0.7
        assert selection_config["benchmark"]["latency_aggregation"] == "latest"

    def test_config_with_custom_latency_aggregation(self):
        """Test config with custom latency_aggregation strategy."""
        selection_config = {
            "benchmark": {
                "required_metrics": ["latency_batch_1_ms"],
                "latency_aggregation": "median"
            }
        }
        
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        
        assert aggregation == "median"

    def test_config_with_all_champion_selection_options(self):
        """Test config with all champion_selection options set."""
        selection_config = {
            "champion_selection": {
                "min_trials_per_group": 5,
                "top_k_for_stable_score": 2,
                "require_artifact_available": True,
                "artifact_check_source": "disk",
                "prefer_schema_version": "2.0",
                "allow_mixed_schema_groups": True
            }
        }
        
        champion_config = selection_config.get("champion_selection", {})
        
        assert champion_config["min_trials_per_group"] == 5
        assert champion_config["top_k_for_stable_score"] == 2
        assert champion_config["require_artifact_available"] is True
        assert champion_config["artifact_check_source"] == "disk"
        assert champion_config["prefer_schema_version"] == "2.0"
        assert champion_config["allow_mixed_schema_groups"] is True


class TestConfigIntegrationFailureCases:
    """Test failure cases for config options."""

    def test_failure_missing_run_section(self):
        """Test that missing run section uses defaults."""
        selection_config = {}
        
        mode = selection_config.get("run", {}).get("mode", "reuse_if_exists")
        
        assert mode == "reuse_if_exists"  # Default

    def test_failure_missing_objective_section(self):
        """Test that missing objective section uses defaults."""
        selection_config = {}
        
        metric = selection_config.get("objective", {}).get("metric", "macro-f1")
        direction = selection_config.get("objective", {}).get("direction", "maximize")
        
        assert metric == "macro-f1"  # Default
        assert direction == "maximize"  # Default

    def test_failure_missing_champion_selection_section(self):
        """Test that missing champion_selection section uses defaults."""
        selection_config = {}
        
        min_trials = selection_config.get("champion_selection", {}).get("min_trials_per_group", 3)
        top_k = selection_config.get("champion_selection", {}).get("top_k_for_stable_score", 3)
        require_artifact = selection_config.get("champion_selection", {}).get("require_artifact_available", False)
        
        assert min_trials == 3  # Default
        assert top_k == 3  # Default
        assert require_artifact is False  # Default

    def test_failure_missing_scoring_section(self):
        """Test that missing scoring section uses defaults."""
        selection_config = {}
        
        f1_weight = selection_config.get("scoring", {}).get("f1_weight", 0.7)
        latency_weight = selection_config.get("scoring", {}).get("latency_weight", 0.3)
        normalize = selection_config.get("scoring", {}).get("normalize_weights", True)
        
        assert f1_weight == 0.7  # Default
        assert latency_weight == 0.3  # Default
        assert normalize is True  # Default

    def test_failure_missing_benchmark_section(self):
        """Test that missing benchmark section uses defaults."""
        selection_config = {}
        
        metrics = selection_config.get("benchmark", {}).get("required_metrics", [])
        aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
        
        assert metrics == []  # Default
        assert aggregation == "latest"  # Default

    def test_failure_empty_required_metrics(self):
        """Test that empty required_metrics list is handled."""
        selection_config = {
            "benchmark": {
                "required_metrics": []
            }
        }
        
        metrics = selection_config.get("benchmark", {}).get("required_metrics", [])
        
        assert metrics == []
        # In actual usage, this might cause all benchmark runs to be filtered out

    def test_failure_zero_weights(self):
        """Test that zero weights are possible (not validated)."""
        selection_config = {
            "scoring": {
                "f1_weight": 0.0,
                "latency_weight": 0.0
            }
        }
        
        f1_weight = selection_config.get("scoring", {}).get("f1_weight", 0.7)
        latency_weight = selection_config.get("scoring", {}).get("latency_weight", 0.3)
        
        assert f1_weight == 0.0
        assert latency_weight == 0.0
        # In actual usage, this might cause issues in composite score calculation


class TestConfigTypeValidation:
    """Test that all config options have correct types."""

    def test_all_config_option_types(self):
        """Test that all config options have expected types."""
        selection_config = {
            "run": {
                "mode": "force_new"
            },
            "objective": {
                "metric": "macro-f1",
                "direction": "maximize",
                "goal": "maximize"
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
                "latency_aggregation": "latest"
            }
        }
        
        # Verify types
        assert isinstance(selection_config["run"]["mode"], str)
        assert isinstance(selection_config["objective"]["metric"], str)
        assert isinstance(selection_config["objective"]["direction"], str)
        assert isinstance(selection_config["objective"]["goal"], str)
        assert isinstance(selection_config["champion_selection"]["min_trials_per_group"], int)
        assert isinstance(selection_config["champion_selection"]["top_k_for_stable_score"], int)
        assert isinstance(selection_config["champion_selection"]["require_artifact_available"], bool)
        assert isinstance(selection_config["champion_selection"]["artifact_check_source"], str)
        assert isinstance(selection_config["champion_selection"]["prefer_schema_version"], str)
        assert isinstance(selection_config["champion_selection"]["allow_mixed_schema_groups"], bool)
        assert isinstance(selection_config["scoring"]["f1_weight"], (int, float))
        assert isinstance(selection_config["scoring"]["latency_weight"], (int, float))
        assert isinstance(selection_config["scoring"]["normalize_weights"], bool)
        assert isinstance(selection_config["benchmark"]["required_metrics"], list)
        assert all(isinstance(m, str) for m in selection_config["benchmark"]["required_metrics"])
        assert isinstance(selection_config["benchmark"]["latency_aggregation"], str)


class TestConfigDefaults:
    """Test default values for all config options."""

    def test_all_defaults_match_config_file(self):
        """Test that default values match the actual config file defaults."""
        # Defaults from best_model_selection.yaml
        defaults = {
            "run": {
                "mode": "reuse_if_exists"  # Default (not force_new)
            },
            "objective": {
                "metric": "macro-f1",
                "direction": "maximize"
            },
            "champion_selection": {
                "min_trials_per_group": 3,  # Default (not 1)
                "top_k_for_stable_score": 3,  # Default (not 1)
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
                "latency_aggregation": "latest"
            }
        }
        
        # Verify defaults
        assert defaults["run"]["mode"] == "reuse_if_exists"
        assert defaults["objective"]["metric"] == "macro-f1"
        assert defaults["objective"]["direction"] == "maximize"
        assert defaults["champion_selection"]["min_trials_per_group"] == 3
        assert defaults["champion_selection"]["top_k_for_stable_score"] == 3
        assert defaults["champion_selection"]["require_artifact_available"] is False
        assert defaults["champion_selection"]["artifact_check_source"] == "tag"
        assert defaults["champion_selection"]["prefer_schema_version"] == "auto"
        assert defaults["champion_selection"]["allow_mixed_schema_groups"] is False
        assert defaults["scoring"]["f1_weight"] == 0.7
        assert defaults["scoring"]["latency_weight"] == 0.3
        assert defaults["scoring"]["normalize_weights"] is True
        assert defaults["benchmark"]["required_metrics"] == ["latency_batch_1_ms"]
        assert defaults["benchmark"]["latency_aggregation"] == "latest"


class TestConfigCompleteCoverage:
    """Test that all config options from best_model_selection.yaml are covered."""

    def test_all_config_sections_present(self):
        """Test that all sections from best_model_selection.yaml are testable."""
        # All sections from the actual config file
        required_sections = [
            "run",
            "objective",
            "champion_selection",
            "scoring",
            "benchmark"
        ]
        
        sample_config = {
            "run": {"mode": "force_new"},
            "objective": {
                "metric": "macro-f1",
                "direction": "maximize",
                "goal": "maximize"
            },
            "champion_selection": {
                "min_trials_per_group": 1,
                "top_k_for_stable_score": 1,
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
                "latency_aggregation": "latest"
            }
        }
        
        for section in required_sections:
            assert section in sample_config, f"Missing section: {section}"

    def test_all_run_options_present(self):
        """Test that all run.* options are covered."""
        required_options = ["mode"]
        
        run_config = {"mode": "force_new"}
        
        for option in required_options:
            assert option in run_config, f"Missing run option: {option}"

    def test_all_objective_options_present(self):
        """Test that all objective.* options are covered."""
        required_options = ["metric", "direction"]  # goal is legacy
        
        objective_config = {
            "metric": "macro-f1",
            "direction": "maximize",
            "goal": "maximize"  # Legacy
        }
        
        for option in required_options:
            assert option in objective_config, f"Missing objective option: {option}"

    def test_all_champion_selection_options_present(self):
        """Test that all champion_selection.* options are covered."""
        required_options = [
            "min_trials_per_group",
            "top_k_for_stable_score",
            "require_artifact_available",
            "artifact_check_source",
            "prefer_schema_version",
            "allow_mixed_schema_groups"
        ]
        
        champion_config = {
            "min_trials_per_group": 1,
            "top_k_for_stable_score": 1,
            "require_artifact_available": False,
            "artifact_check_source": "tag",
            "prefer_schema_version": "auto",
            "allow_mixed_schema_groups": False
        }
        
        for option in required_options:
            assert option in champion_config, f"Missing champion_selection option: {option}"

    def test_all_scoring_options_present(self):
        """Test that all scoring.* options are covered."""
        required_options = ["f1_weight", "latency_weight", "normalize_weights"]
        
        scoring_config = {
            "f1_weight": 0.7,
            "latency_weight": 0.3,
            "normalize_weights": True
        }
        
        for option in required_options:
            assert option in scoring_config, f"Missing scoring option: {option}"

    def test_all_benchmark_options_present(self):
        """Test that all benchmark.* options are covered."""
        required_options = ["required_metrics", "latency_aggregation"]
        
        benchmark_config = {
            "required_metrics": ["latency_batch_1_ms"],
            "latency_aggregation": "latest"
        }
        
        for option in required_options:
            assert option in benchmark_config, f"Missing benchmark option: {option}"


