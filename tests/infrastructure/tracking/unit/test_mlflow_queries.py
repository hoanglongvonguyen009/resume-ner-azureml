"""Unit tests for MLflow query patterns (queries.py).

Tests reusable MLflow query functions:
- query_runs_by_tags()
- find_best_run_by_metric()
- group_runs_by_variant()
"""

import pytest
from unittest.mock import Mock, MagicMock
from infrastructure.tracking.mlflow.queries import (
    query_runs_by_tags,
    find_best_run_by_metric,
    group_runs_by_variant,
)


class TestQueryRunsByTags:
    """Test query_runs_by_tags() function."""

    def test_filters_finished_runs(self):
        """Test that only FINISHED runs are returned."""
        # Create mock runs
        run1 = Mock()
        run1.info.status = "FINISHED"
        run1.data.tags = {"tag1": "value1"}
        
        run2 = Mock()
        run2.info.status = "RUNNING"
        run2.data.tags = {"tag1": "value1"}
        
        run3 = Mock()
        run3.info.status = "FINISHED"
        run3.data.tags = {"tag1": "value1"}
        
        # Mock client
        client = Mock()
        client.search_runs.return_value = [run1, run2, run3]
        
        result = query_runs_by_tags(
            client=client,
            experiment_ids=["exp1"],
            required_tags={"tag1": "value1"},
        )
        
        # Should only return finished runs
        assert len(result) == 2
        assert run1 in result
        assert run3 in result
        assert run2 not in result

    def test_filters_by_required_tags(self):
        """Test that runs are filtered by required tags."""
        run1 = Mock()
        run1.info.status = "FINISHED"
        run1.data.tags = {"tag1": "value1", "tag2": "value2"}
        
        run2 = Mock()
        run2.info.status = "FINISHED"
        run2.data.tags = {"tag1": "value1", "tag2": "wrong"}
        
        run3 = Mock()
        run3.info.status = "FINISHED"
        run3.data.tags = {"tag1": "value1", "tag2": "value2"}
        
        client = Mock()
        client.search_runs.return_value = [run1, run2, run3]
        
        result = query_runs_by_tags(
            client=client,
            experiment_ids=["exp1"],
            required_tags={"tag1": "value1", "tag2": "value2"},
        )
        
        assert len(result) == 2
        assert run1 in result
        assert run3 in result
        assert run2 not in result

    def test_handles_missing_tags(self):
        """Test that runs with missing tags are filtered out."""
        run1 = Mock()
        run1.info.status = "FINISHED"
        run1.data.tags = {"tag1": "value1"}
        
        run2 = Mock()
        run2.info.status = "FINISHED"
        run2.data.tags = {}  # Missing tag1
        
        client = Mock()
        client.search_runs.return_value = [run1, run2]
        
        result = query_runs_by_tags(
            client=client,
            experiment_ids=["exp1"],
            required_tags={"tag1": "value1"},
        )
        
        assert len(result) == 1
        assert run1 in result
        assert run2 not in result

    def test_passes_filter_string(self):
        """Test that filter_string is passed to search_runs."""
        client = Mock()
        client.search_runs.return_value = []
        
        query_runs_by_tags(
            client=client,
            experiment_ids=["exp1"],
            required_tags={},
            filter_string="metrics.accuracy > 0.8",
        )
        
        client.search_runs.assert_called_once()
        call_args = client.search_runs.call_args
        assert call_args[1]["filter_string"] == "metrics.accuracy > 0.8"

    def test_passes_max_results(self):
        """Test that max_results is passed to search_runs."""
        client = Mock()
        client.search_runs.return_value = []
        
        query_runs_by_tags(
            client=client,
            experiment_ids=["exp1"],
            required_tags={},
            max_results=500,
        )
        
        client.search_runs.assert_called_once()
        call_args = client.search_runs.call_args
        assert call_args[1]["max_results"] == 500

    def test_empty_result(self):
        """Test with no matching runs."""
        client = Mock()
        client.search_runs.return_value = []
        
        result = query_runs_by_tags(
            client=client,
            experiment_ids=["exp1"],
            required_tags={"tag1": "value1"},
        )
        
        assert result == []


class TestFindBestRunByMetric:
    """Test find_best_run_by_metric() function."""

    def test_maximize_metric(self):
        """Test finding best run when maximizing metric."""
        run1 = Mock()
        run1.data.metrics = {"accuracy": 0.9}
        
        run2 = Mock()
        run2.data.metrics = {"accuracy": 0.8}
        
        run3 = Mock()
        run3.data.metrics = {"accuracy": 0.95}
        
        result = find_best_run_by_metric(
            runs=[run1, run2, run3],
            metric_name="accuracy",
            maximize=True,
        )
        
        assert result == run3

    def test_minimize_metric(self):
        """Test finding best run when minimizing metric."""
        run1 = Mock()
        run1.data.metrics = {"loss": 0.5}
        
        run2 = Mock()
        run2.data.metrics = {"loss": 0.3}
        
        run3 = Mock()
        run3.data.metrics = {"loss": 0.7}
        
        result = find_best_run_by_metric(
            runs=[run1, run2, run3],
            metric_name="loss",
            maximize=False,
        )
        
        assert result == run2

    def test_filters_runs_without_metric(self):
        """Test that runs without metric are filtered out."""
        run1 = Mock()
        run1.data.metrics = {"accuracy": 0.9}
        
        run2 = Mock()
        run2.data.metrics = {}  # No accuracy metric
        
        run3 = Mock()
        run3.data.metrics = {"accuracy": 0.8}
        
        result = find_best_run_by_metric(
            runs=[run1, run2, run3],
            metric_name="accuracy",
            maximize=True,
        )
        
        assert result == run1

    def test_returns_none_when_no_runs_have_metric(self):
        """Test that None is returned when no runs have the metric."""
        run1 = Mock()
        run1.data.metrics = {"other_metric": 0.9}
        
        run2 = Mock()
        run2.data.metrics = {}
        
        result = find_best_run_by_metric(
            runs=[run1, run2],
            metric_name="accuracy",
            maximize=True,
        )
        
        assert result is None

    def test_empty_runs_list(self):
        """Test with empty runs list."""
        result = find_best_run_by_metric(
            runs=[],
            metric_name="accuracy",
            maximize=True,
        )
        
        assert result is None

    def test_single_run(self):
        """Test with single run."""
        run1 = Mock()
        run1.data.metrics = {"accuracy": 0.9}
        
        result = find_best_run_by_metric(
            runs=[run1],
            metric_name="accuracy",
            maximize=True,
        )
        
        assert result == run1


class TestGroupRunsByVariant:
    """Test group_runs_by_variant() function."""

    def test_groups_by_variant_tag(self):
        """Test grouping runs by variant tag."""
        run1 = Mock()
        run1.data.tags = {"code.variant": "variant1"}
        
        run2 = Mock()
        run2.data.tags = {"code.variant": "variant2"}
        
        run3 = Mock()
        run3.data.tags = {"code.variant": "variant1"}
        
        result = group_runs_by_variant(
            runs=[run1, run2, run3],
            variant_tag="code.variant",
        )
        
        assert "variant1" in result
        assert "variant2" in result
        assert len(result["variant1"]) == 2
        assert len(result["variant2"]) == 1
        assert run1 in result["variant1"]
        assert run3 in result["variant1"]
        assert run2 in result["variant2"]

    def test_default_variant_for_missing_tag(self):
        """Test that runs without variant tag get 'default' variant."""
        run1 = Mock()
        run1.data.tags = {"code.variant": "variant1"}
        
        run2 = Mock()
        run2.data.tags = {}  # Missing variant tag
        
        result = group_runs_by_variant(
            runs=[run1, run2],
            variant_tag="code.variant",
        )
        
        assert "variant1" in result
        assert "default" in result
        assert run1 in result["variant1"]
        assert run2 in result["default"]

    def test_custom_variant_tag(self):
        """Test with custom variant tag."""
        run1 = Mock()
        run1.data.tags = {"custom.variant": "v1"}
        
        run2 = Mock()
        run2.data.tags = {"custom.variant": "v2"}
        
        result = group_runs_by_variant(
            runs=[run1, run2],
            variant_tag="custom.variant",
        )
        
        assert "v1" in result
        assert "v2" in result

    def test_empty_runs_list(self):
        """Test with empty runs list."""
        result = group_runs_by_variant(
            runs=[],
            variant_tag="code.variant",
        )
        
        assert result == {}

