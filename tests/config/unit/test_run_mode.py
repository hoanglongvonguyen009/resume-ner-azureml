"""Unit tests for run mode utility (run_mode.py).

Tests the unified run mode extraction utility that replaces
4+ duplicate extractions throughout the codebase.
"""

import pytest
from infrastructure.config.run_mode import (
    RunMode,
    get_run_mode,
    is_force_new,
    is_reuse_if_exists,
    is_resume_if_incomplete,
)


class TestGetRunMode:
    """Test get_run_mode() function."""

    def test_get_run_mode_explicit_force_new(self):
        """Test extracting force_new mode."""
        config = {"run": {"mode": "force_new"}}
        assert get_run_mode(config) == "force_new"

    def test_get_run_mode_explicit_reuse_if_exists(self):
        """Test extracting reuse_if_exists mode."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert get_run_mode(config) == "reuse_if_exists"

    def test_get_run_mode_explicit_resume_if_incomplete(self):
        """Test extracting resume_if_incomplete mode."""
        config = {"run": {"mode": "resume_if_incomplete"}}
        assert get_run_mode(config) == "resume_if_incomplete"

    def test_get_run_mode_default_when_missing(self):
        """Test default mode when run.mode is not specified."""
        config = {}
        assert get_run_mode(config) == "reuse_if_exists"

    def test_get_run_mode_default_when_run_section_missing(self):
        """Test default mode when run section is missing."""
        config = {"other": "value"}
        assert get_run_mode(config) == "reuse_if_exists"

    def test_get_run_mode_custom_default(self):
        """Test custom default mode."""
        config = {}
        assert get_run_mode(config, default="force_new") == "force_new"

    def test_get_run_mode_nested_config(self):
        """Test extracting from nested config structure."""
        config = {
            "hpo": {"sampling": {"algorithm": "random"}},
            "run": {"mode": "force_new"},
            "checkpoint": {"enabled": True},
        }
        assert get_run_mode(config) == "force_new"

    def test_get_run_mode_combined_config(self):
        """Test extracting from combined config (hpo + checkpoint)."""
        hpo_config = {"sampling": {"algorithm": "random"}}
        checkpoint_config = {"run": {"mode": "force_new"}}
        combined = {**hpo_config, **checkpoint_config}
        assert get_run_mode(combined) == "force_new"


class TestIsForceNew:
    """Test is_force_new() helper function."""

    def test_is_force_new_true(self):
        """Test is_force_new returns True for force_new mode."""
        config = {"run": {"mode": "force_new"}}
        assert is_force_new(config) is True

    def test_is_force_new_false(self):
        """Test is_force_new returns False for other modes."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert is_force_new(config) is False

    def test_is_force_new_default(self):
        """Test is_force_new returns False for default mode."""
        config = {}
        assert is_force_new(config) is False


class TestIsReuseIfExists:
    """Test is_reuse_if_exists() helper function."""

    def test_is_reuse_if_exists_true(self):
        """Test is_reuse_if_exists returns True for reuse_if_exists mode."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert is_reuse_if_exists(config) is True

    def test_is_reuse_if_exists_false(self):
        """Test is_reuse_if_exists returns False for other modes."""
        config = {"run": {"mode": "force_new"}}
        assert is_reuse_if_exists(config) is False

    def test_is_reuse_if_exists_default(self):
        """Test is_reuse_if_exists returns True for default mode."""
        config = {}
        assert is_reuse_if_exists(config) is True


class TestIsResumeIfIncomplete:
    """Test is_resume_if_incomplete() helper function."""

    def test_is_resume_if_incomplete_true(self):
        """Test is_resume_if_incomplete returns True for resume_if_incomplete mode."""
        config = {"run": {"mode": "resume_if_incomplete"}}
        assert is_resume_if_incomplete(config) is True

    def test_is_resume_if_incomplete_false(self):
        """Test is_resume_if_incomplete returns False for other modes."""
        config = {"run": {"mode": "force_new"}}
        assert is_resume_if_incomplete(config) is False

    def test_is_resume_if_incomplete_default(self):
        """Test is_resume_if_incomplete returns False for default mode."""
        config = {}
        assert is_resume_if_incomplete(config) is False


class TestRunModeIntegration:
    """Integration tests for run mode with real config structures."""

    def test_hpo_config_with_run_mode(self):
        """Test run mode extraction from HPO config structure."""
        hpo_config = {
            "search_space": {"backbone": {"type": "choice", "values": ["distilbert"]}},
            "sampling": {"algorithm": "random", "max_trials": 2},
            "run": {"mode": "force_new"},
            "checkpoint": {"enabled": True},
        }
        assert get_run_mode(hpo_config) == "force_new"
        assert is_force_new(hpo_config) is True

    def test_combined_hpo_checkpoint_config(self):
        """Test run mode extraction from combined HPO + checkpoint config."""
        hpo_config = {
            "sampling": {"algorithm": "random"},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "run": {"mode": "reuse_if_exists"},
        }
        combined = {**hpo_config, **checkpoint_config}
        
        # Checkpoint config should take precedence (last dict wins)
        assert get_run_mode(combined) == "reuse_if_exists"
        assert is_reuse_if_exists(combined) is True

    def test_final_training_config_with_run_mode(self):
        """Test run mode extraction from final training config."""
        final_training_config = {
            "run": {"mode": "resume_if_incomplete"},
            "variant": {"number": None},
            "checkpoint": {"load": True},
        }
        assert get_run_mode(final_training_config) == "resume_if_incomplete"
        assert is_resume_if_incomplete(final_training_config) is True


