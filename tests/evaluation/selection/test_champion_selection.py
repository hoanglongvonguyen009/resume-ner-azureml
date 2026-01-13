"""Unit and integration tests for champion selection (trial_finder.py).

Tests the select_champion_per_backbone() function with various scenarios:
- Success cases (v1, v2, mixed)
- Failure cases (no runs, insufficient trials, missing metrics)
- Edge cases (NaN metrics, missing artifacts, schema version handling)
"""

import pytest
import math
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from evaluation.selection.trial_finder import select_champion_per_backbone


@pytest.fixture
def mock_mlflow_client():
    """Create a mock MLflow client."""
    client = Mock()
    return client


@pytest.fixture
def mock_hpo_experiment():
    """Create a mock HPO experiment."""
    return {"name": "test_hpo_experiment", "id": "exp123"}


@pytest.fixture
def base_selection_config():
    """Create base selection config."""
    return {
        "objective": {
            "metric": "macro-f1",
            "direction": "maximize",
        },
        "champion_selection": {
            "min_trials_per_group": 3,
            "top_k_for_stable_score": 3,
            "require_artifact_available": True,
            "artifact_check_source": "tag",
            "prefer_schema_version": "auto",
            "allow_mixed_schema_groups": False,
        },
    }


def create_mock_run(run_id, metric_value, study_key_hash, schema_version="1.0", artifact_available=True):
    """Helper to create mock MLflow run."""
    run = Mock()
    run.info.run_id = run_id
    run.info.status = "FINISHED"
    run.data.metrics = {"macro-f1": metric_value}
    run.data.tags = {
        "code.backbone": "distilbert",
        "code.stage": "hpo_trial",
        "code.study_key_hash": study_key_hash,
        "code.study.key_schema_version": schema_version,
        "code.artifact.available": "true" if artifact_available else "false",
    }
    return run


class TestSelectChampionPerBackbone:
    """Test select_champion_per_backbone() function."""

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_successful_selection_v2(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test successful champion selection with v2 runs."""
        # Create mock runs with v2 schema
        runs = [
            create_mock_run("run1", 0.85, "hash1", schema_version="2.0"),
            create_mock_run("run2", 0.87, "hash1", schema_version="2.0"),
            create_mock_run("run3", 0.86, "hash1", schema_version="2.0"),
        ]
        mock_query.return_value = runs
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        assert result is not None
        assert result["backbone"] == "distilbert"
        assert "champion" in result
        assert result["champion"]["run_id"] == "run2"  # Highest metric
        assert result["champion"]["metric"] == 0.87
        assert result["champion"]["schema_version"] == "2.0"

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_successful_selection_v1(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test successful champion selection with v1 runs."""
        runs = [
            create_mock_run("run1", 0.85, "hash1", schema_version="1.0"),
            create_mock_run("run2", 0.87, "hash1", schema_version="1.0"),
            create_mock_run("run3", 0.86, "hash1", schema_version="1.0"),
        ]
        mock_query.return_value = runs
        
        # Prefer v1 explicitly
        base_selection_config["champion_selection"]["prefer_schema_version"] = "1.0"
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        assert result is not None
        assert result["champion"]["schema_version"] == "1.0"

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_no_runs_returns_none(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that None is returned when no runs found."""
        mock_query.return_value = []
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        assert result is None

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_insufficient_trials_returns_none(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that None is returned when insufficient trials per group."""
        # Only 2 runs, but min_trials_per_group is 3
        runs = [
            create_mock_run("run1", 0.85, "hash1"),
            create_mock_run("run2", 0.87, "hash1"),
        ]
        mock_query.return_value = runs
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        assert result is None

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_missing_metrics_filtered(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that runs with missing metrics are filtered out."""
        run1 = create_mock_run("run1", 0.85, "hash1")
        run2 = create_mock_run("run2", 0.87, "hash1")
        run3 = create_mock_run("run3", 0.86, "hash1")
        run3.data.metrics = {}  # Missing metric
        
        runs = [run1, run2, run3]
        mock_query.return_value = runs
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        # Should still work with 2 valid runs, but might fail min_trials check
        # Actually, with 2 valid runs and min_trials=3, should return None
        assert result is None

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_nan_metrics_filtered(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that runs with NaN metrics are filtered out."""
        run1 = create_mock_run("run1", 0.85, "hash1")
        run2 = create_mock_run("run2", 0.87, "hash1")
        run3 = create_mock_run("run3", float("nan"), "hash1")
        
        runs = [run1, run2, run3]
        mock_query.return_value = runs
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        # Should still work with 2 valid runs, but might fail min_trials check
        assert result is None

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_artifact_availability_filter(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that runs without artifacts are filtered when required."""
        runs = [
            create_mock_run("run1", 0.85, "hash1", artifact_available=True),
            create_mock_run("run2", 0.87, "hash1", artifact_available=False),
            create_mock_run("run3", 0.86, "hash1", artifact_available=True),
        ]
        mock_query.return_value = runs
        
        base_selection_config["champion_selection"]["require_artifact_available"] = True
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        # Should only use runs with artifacts (run1, run3)
        # But with only 2 runs and min_trials=3, should return None
        assert result is None

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_no_artifact_requirement(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that artifact requirement can be disabled."""
        runs = [
            create_mock_run("run1", 0.85, "hash1", artifact_available=False),
            create_mock_run("run2", 0.87, "hash1", artifact_available=False),
            create_mock_run("run3", 0.86, "hash1", artifact_available=False),
        ]
        mock_query.return_value = runs
        
        base_selection_config["champion_selection"]["require_artifact_available"] = False
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        assert result is not None
        assert result["champion"]["run_id"] == "run2"

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_never_mix_v1_v2_when_disabled(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that v1 and v2 runs are never mixed when allow_mixed_schema_groups is False."""
        runs = [
            create_mock_run("run1", 0.85, "hash1", schema_version="1.0"),
            create_mock_run("run2", 0.87, "hash1", schema_version="1.0"),
            create_mock_run("run3", 0.90, "hash1", schema_version="2.0"),  # v2 run
            create_mock_run("run4", 0.88, "hash1", schema_version="2.0"),  # v2 run
        ]
        mock_query.return_value = runs
        
        base_selection_config["champion_selection"]["allow_mixed_schema_groups"] = False
        base_selection_config["champion_selection"]["prefer_schema_version"] = "auto"
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        # Should prefer v2 (auto mode with v2 present)
        assert result is not None
        assert result["champion"]["schema_version"] == "2.0"
        assert result["champion"]["run_id"] == "run3"  # Best v2 run

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_minimize_objective(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test champion selection with minimize objective."""
        runs = [
            create_mock_run("run1", 0.85, "hash1"),
            create_mock_run("run2", 0.87, "hash1"),  # Highest (worst for minimize)
            create_mock_run("run3", 0.80, "hash1"),  # Lowest (best for minimize)
        ]
        mock_query.return_value = runs
        
        base_selection_config["objective"]["direction"] = "minimize"
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        assert result is not None
        assert result["champion"]["run_id"] == "run3"  # Lowest metric value

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_legacy_goal_key_migration(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that legacy 'goal' key is migrated to 'direction'."""
        runs = [
            create_mock_run("run1", 0.85, "hash1"),
            create_mock_run("run2", 0.87, "hash1"),
            create_mock_run("run3", 0.86, "hash1"),
        ]
        mock_query.return_value = runs
        
        # Use legacy 'goal' key
        base_selection_config["objective"] = {
            "metric": "macro-f1",
            "goal": "maximize",  # Legacy key
        }
        
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = select_champion_per_backbone(
                backbone="distilbert",
                hpo_experiment=mock_hpo_experiment,
                selection_config=base_selection_config,
                mlflow_client=mock_mlflow_client,
            )
            
            # Should work and warn about deprecated key
            assert result is not None
            assert len(w) > 0

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_multiple_groups_selects_best(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that best group is selected when multiple groups exist."""
        # Group 1: lower average score
        runs = [
            create_mock_run("run1", 0.80, "hash1"),
            create_mock_run("run2", 0.81, "hash1"),
            create_mock_run("run3", 0.82, "hash1"),
        ]
        # Group 2: higher average score
        runs.extend([
            create_mock_run("run4", 0.90, "hash2"),
            create_mock_run("run5", 0.91, "hash2"),
            create_mock_run("run6", 0.92, "hash2"),
        ])
        mock_query.return_value = runs
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        assert result is not None
        # Should select from group 2 (higher stable score)
        assert result["champion"]["study_key_hash"] == "hash2"
        assert result["champion"]["run_id"] == "run6"  # Best in group 2

    @patch("evaluation.selection.trial_finder.query_runs_by_tags")
    def test_stable_score_computation(self, mock_query, mock_mlflow_client, mock_hpo_experiment, base_selection_config):
        """Test that stable score is computed correctly (median of top_k)."""
        # Create runs with known metrics for stable score calculation
        runs = [
            create_mock_run("run1", 0.80, "hash1"),
            create_mock_run("run2", 0.85, "hash1"),
            create_mock_run("run3", 0.90, "hash1"),  # Top score
            create_mock_run("run4", 0.82, "hash1"),
            create_mock_run("run5", 0.88, "hash1"),  # Second best
        ]
        mock_query.return_value = runs
        
        base_selection_config["champion_selection"]["top_k_for_stable_score"] = 3
        
        result = select_champion_per_backbone(
            backbone="distilbert",
            hpo_experiment=mock_hpo_experiment,
            selection_config=base_selection_config,
            mlflow_client=mock_mlflow_client,
        )
        
        assert result is not None
        # Stable score should be median of top 3: [0.90, 0.88, 0.85] = 0.88
        assert result["champion"]["stable_score"] == 0.88

