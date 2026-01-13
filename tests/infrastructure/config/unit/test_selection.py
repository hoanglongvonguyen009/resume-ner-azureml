"""Unit tests for selection config utilities (selection.py).

Tests the centralized selection config utilities including:
- get_objective_direction() with migration support
- get_champion_selection_config() with validation
"""

import pytest
import warnings
from infrastructure.config.selection import (
    get_objective_direction,
    get_champion_selection_config,
)


class TestGetObjectiveDirection:
    """Test get_objective_direction() function."""

    def test_direction_key_maximize(self):
        """Test using new 'direction' key with maximize."""
        config = {"objective": {"direction": "maximize"}}
        assert get_objective_direction(config) == "maximize"

    def test_direction_key_minimize(self):
        """Test using new 'direction' key with minimize."""
        config = {"objective": {"direction": "minimize"}}
        assert get_objective_direction(config) == "minimize"

    def test_goal_key_maximize_legacy(self):
        """Test using legacy 'goal' key with maximize (should warn)."""
        config = {"objective": {"goal": "maximize"}}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = get_objective_direction(config)
            assert result == "maximize"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    def test_goal_key_minimize_legacy(self):
        """Test using legacy 'goal' key with minimize (should warn)."""
        config = {"objective": {"goal": "minimize"}}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = get_objective_direction(config)
            assert result == "minimize"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_goal_key_max_legacy(self):
        """Test using legacy 'goal' key with 'max' (should map to maximize)."""
        config = {"objective": {"goal": "max"}}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = get_objective_direction(config)
            assert result == "maximize"

    def test_goal_key_min_legacy(self):
        """Test using legacy 'goal' key with 'min' (should map to minimize)."""
        config = {"objective": {"goal": "min"}}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = get_objective_direction(config)
            assert result == "minimize"

    def test_goal_key_case_insensitive(self):
        """Test that goal key mapping is case-insensitive."""
        config = {"objective": {"goal": "MAX"}}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = get_objective_direction(config)
            assert result == "maximize"

        config = {"objective": {"goal": "MIN"}}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = get_objective_direction(config)
            assert result == "minimize"

    def test_direction_takes_precedence_over_goal(self):
        """Test that 'direction' key takes precedence over 'goal' key."""
        config = {"objective": {"direction": "maximize", "goal": "minimize"}}
        # Should not warn since direction is present
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = get_objective_direction(config)
            assert result == "maximize"
            assert len(w) == 0  # No warning since direction is used

    def test_default_when_missing(self):
        """Test default value when objective section is missing."""
        config = {}
        assert get_objective_direction(config) == "maximize"

    def test_default_when_objective_empty(self):
        """Test default value when objective section is empty."""
        config = {"objective": {}}
        assert get_objective_direction(config) == "maximize"

    def test_goal_passthrough_when_already_correct_format(self):
        """Test that goal value is passed through if already correct format."""
        config = {"objective": {"goal": "maximize"}}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = get_objective_direction(config)
            assert result == "maximize"


class TestGetChampionSelectionConfig:
    """Test get_champion_selection_config() function."""

    def test_default_values(self):
        """Test default values when champion_selection section is missing."""
        config = {}
        result = get_champion_selection_config(config)
        
        assert result["min_trials_per_group"] == 3
        assert result["top_k_for_stable_score"] == 3
        assert result["require_artifact_available"] is True
        assert result["artifact_check_source"] == "tag"
        assert result["prefer_schema_version"] == "auto"
        assert result["allow_mixed_schema_groups"] is False

    def test_custom_values(self):
        """Test custom values from config."""
        config = {
            "champion_selection": {
                "min_trials_per_group": 5,
                "top_k_for_stable_score": 3,
                "require_artifact_available": False,
                "artifact_check_source": "disk",
                "prefer_schema_version": "2.0",
                "allow_mixed_schema_groups": True,
            }
        }
        result = get_champion_selection_config(config)
        
        assert result["min_trials_per_group"] == 5
        assert result["top_k_for_stable_score"] == 3
        assert result["require_artifact_available"] is False
        assert result["artifact_check_source"] == "disk"
        assert result["prefer_schema_version"] == "2.0"
        assert result["allow_mixed_schema_groups"] is True

    def test_top_k_clamping_when_greater_than_min_trials(self):
        """Test that top_k is clamped when greater than min_trials."""
        config = {
            "champion_selection": {
                "min_trials_per_group": 3,
                "top_k_for_stable_score": 5,  # Should be clamped to 3
            }
        }
        # Function logs a warning (not raises), so we just verify clamping
        result = get_champion_selection_config(config)
        
        assert result["min_trials_per_group"] == 3
        assert result["top_k_for_stable_score"] == 3  # Clamped

    def test_top_k_equal_to_min_trials(self):
        """Test that top_k equal to min_trials is valid."""
        config = {
            "champion_selection": {
                "min_trials_per_group": 5,
                "top_k_for_stable_score": 5,
            }
        }
        result = get_champion_selection_config(config)
        
        assert result["min_trials_per_group"] == 5
        assert result["top_k_for_stable_score"] == 5

    def test_top_k_less_than_min_trials(self):
        """Test that top_k less than min_trials is valid."""
        config = {
            "champion_selection": {
                "min_trials_per_group": 5,
                "top_k_for_stable_score": 3,
            }
        }
        result = get_champion_selection_config(config)
        
        assert result["min_trials_per_group"] == 5
        assert result["top_k_for_stable_score"] == 3

    def test_require_artifact_available_false(self):
        """Test require_artifact_available set to False."""
        config = {
            "champion_selection": {
                "require_artifact_available": False,
            }
        }
        result = get_champion_selection_config(config)
        assert result["require_artifact_available"] is False

    def test_artifact_check_source_disk(self):
        """Test artifact_check_source set to disk."""
        config = {
            "champion_selection": {
                "artifact_check_source": "disk",
            }
        }
        result = get_champion_selection_config(config)
        assert result["artifact_check_source"] == "disk"

    def test_prefer_schema_version_1_0(self):
        """Test prefer_schema_version set to 1.0."""
        config = {
            "champion_selection": {
                "prefer_schema_version": "1.0",
            }
        }
        result = get_champion_selection_config(config)
        assert result["prefer_schema_version"] == "1.0"

    def test_prefer_schema_version_2_0(self):
        """Test prefer_schema_version set to 2.0."""
        config = {
            "champion_selection": {
                "prefer_schema_version": "2.0",
            }
        }
        result = get_champion_selection_config(config)
        assert result["prefer_schema_version"] == "2.0"

    def test_allow_mixed_schema_groups_true(self):
        """Test allow_mixed_schema_groups set to True."""
        config = {
            "champion_selection": {
                "allow_mixed_schema_groups": True,
            }
        }
        result = get_champion_selection_config(config)
        assert result["allow_mixed_schema_groups"] is True

    def test_complete_config(self):
        """Test complete champion selection config."""
        config = {
            "champion_selection": {
                "min_trials_per_group": 10,
                "top_k_for_stable_score": 5,
                "require_artifact_available": True,
                "artifact_check_source": "tag",
                "prefer_schema_version": "2.0",
                "allow_mixed_schema_groups": False,
            }
        }
        result = get_champion_selection_config(config)
        
        assert result["min_trials_per_group"] == 10
        assert result["top_k_for_stable_score"] == 5
        assert result["require_artifact_available"] is True
        assert result["artifact_check_source"] == "tag"
        assert result["prefer_schema_version"] == "2.0"
        assert result["allow_mixed_schema_groups"] is False

