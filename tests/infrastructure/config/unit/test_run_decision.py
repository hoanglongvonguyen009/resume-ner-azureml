"""Tests for unified run decision logic.

Tests the should_reuse_existing() and get_load_if_exists_flag() functions
that provide single source of truth for reuse vs. create new decisions.
"""

import pytest
from infrastructure.config.run_decision import (
    should_reuse_existing,
    get_load_if_exists_flag,
    ProcessType,
)


class TestShouldReuseExisting:
    """Test should_reuse_existing() decision logic."""

    # force_new mode tests
    def test_force_new_with_exists_returns_false(self):
        """force_new mode always returns False, even if exists."""
        config = {"run": {"mode": "force_new"}}
        assert should_reuse_existing(config, exists=True) is False

    def test_force_new_without_exists_returns_false(self):
        """force_new mode always returns False, even if not exists."""
        config = {"run": {"mode": "force_new"}}
        assert should_reuse_existing(config, exists=False) is False

    def test_force_new_with_exists_and_complete_returns_false(self):
        """force_new mode always returns False, even if complete."""
        config = {"run": {"mode": "force_new"}}
        assert should_reuse_existing(config, exists=True, is_complete=True) is False

    def test_force_new_with_exists_and_incomplete_returns_false(self):
        """force_new mode always returns False, even if incomplete."""
        config = {"run": {"mode": "force_new"}}
        assert should_reuse_existing(config, exists=True, is_complete=False) is False

    # reuse_if_exists mode tests (HPO)
    def test_reuse_if_exists_hpo_with_exists_returns_true(self):
        """reuse_if_exists mode returns True if exists (HPO)."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert should_reuse_existing(config, exists=True, process_type="hpo") is True

    def test_reuse_if_exists_hpo_without_exists_returns_false(self):
        """reuse_if_exists mode returns False if not exists (HPO)."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert should_reuse_existing(config, exists=False, process_type="hpo") is False

    # reuse_if_exists mode tests (Final Training)
    def test_reuse_if_exists_final_training_with_exists_and_complete_returns_true(self):
        """reuse_if_exists mode returns True if exists and complete (Final Training)."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert (
            should_reuse_existing(
                config, exists=True, is_complete=True, process_type="final_training"
            )
            is True
        )

    def test_reuse_if_exists_final_training_with_exists_and_incomplete_returns_false(self):
        """reuse_if_exists mode returns False if exists but incomplete (Final Training)."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert (
            should_reuse_existing(
                config, exists=True, is_complete=False, process_type="final_training"
            )
            is False
        )

    def test_reuse_if_exists_final_training_without_exists_returns_false(self):
        """reuse_if_exists mode returns False if not exists (Final Training)."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert (
            should_reuse_existing(
                config, exists=False, process_type="final_training"
            )
            is False
        )

    # resume_if_incomplete mode tests
    def test_resume_if_incomplete_with_exists_and_incomplete_returns_true(self):
        """resume_if_incomplete mode returns True if exists and incomplete."""
        config = {"run": {"mode": "resume_if_incomplete"}}
        assert (
            should_reuse_existing(config, exists=True, is_complete=False) is True
        )

    def test_resume_if_incomplete_with_exists_and_complete_returns_false(self):
        """resume_if_incomplete mode returns False if exists and complete."""
        config = {"run": {"mode": "resume_if_incomplete"}}
        assert (
            should_reuse_existing(config, exists=True, is_complete=True) is False
        )

    def test_resume_if_incomplete_without_exists_returns_false(self):
        """resume_if_incomplete mode returns False if not exists."""
        config = {"run": {"mode": "resume_if_incomplete"}}
        assert should_reuse_existing(config, exists=False) is False

    def test_resume_if_incomplete_hpo_treats_as_reuse_if_exists(self):
        """resume_if_incomplete mode in HPO (no completeness) treats as reuse_if_exists."""
        config = {"run": {"mode": "resume_if_incomplete"}}
        # HPO doesn't have completeness check, so treats as reuse_if_exists
        assert should_reuse_existing(config, exists=True, process_type="hpo") is True

    # Default behavior tests
    def test_default_with_exists_returns_true(self):
        """Default behavior (no run.mode) returns True if exists (reuse_if_exists)."""
        config = {}
        assert should_reuse_existing(config, exists=True) is True

    def test_default_without_exists_returns_false(self):
        """Default behavior (no run.mode) returns False if not exists."""
        config = {}
        assert should_reuse_existing(config, exists=False) is False

    # Edge cases
    def test_not_exists_always_returns_false_regardless_of_mode(self):
        """If not exists, always returns False regardless of mode."""
        configs = [
            {"run": {"mode": "force_new"}},
            {"run": {"mode": "reuse_if_exists"}},
            {"run": {"mode": "resume_if_incomplete"}},
            {},
        ]
        for config in configs:
            assert should_reuse_existing(config, exists=False) is False


class TestGetLoadIfExistsFlag:
    """Test get_load_if_exists_flag() for Optuna/other libraries."""

    def test_force_new_with_checkpoint_enabled_returns_false(self):
        """force_new mode always returns False, even with checkpointing enabled."""
        config = {"run": {"mode": "force_new"}}
        assert get_load_if_exists_flag(config, checkpoint_enabled=True) is False

    def test_force_new_with_checkpoint_disabled_returns_false(self):
        """force_new mode always returns False, even with checkpointing disabled."""
        config = {"run": {"mode": "force_new"}}
        assert get_load_if_exists_flag(config, checkpoint_enabled=False) is False

    def test_reuse_if_exists_with_checkpoint_enabled_returns_true(self):
        """reuse_if_exists mode returns True if checkpointing enabled."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert get_load_if_exists_flag(config, checkpoint_enabled=True) is True

    def test_reuse_if_exists_with_checkpoint_disabled_returns_false(self):
        """reuse_if_exists mode returns False if checkpointing disabled."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert get_load_if_exists_flag(config, checkpoint_enabled=False) is False

    def test_default_with_checkpoint_enabled_returns_true(self):
        """Default behavior (no run.mode) returns True if checkpointing enabled."""
        config = {}
        assert get_load_if_exists_flag(config, checkpoint_enabled=True) is True

    def test_default_with_checkpoint_disabled_returns_false(self):
        """Default behavior (no run.mode) returns False if checkpointing disabled."""
        config = {}
        assert get_load_if_exists_flag(config, checkpoint_enabled=False) is False

    def test_resume_if_incomplete_with_checkpoint_enabled_returns_true(self):
        """resume_if_incomplete mode returns True if checkpointing enabled."""
        config = {"run": {"mode": "resume_if_incomplete"}}
        assert get_load_if_exists_flag(config, checkpoint_enabled=True) is True

    def test_resume_if_incomplete_with_checkpoint_disabled_returns_false(self):
        """resume_if_incomplete mode returns False if checkpointing disabled."""
        config = {"run": {"mode": "resume_if_incomplete"}}
        assert get_load_if_exists_flag(config, checkpoint_enabled=False) is False

    def test_checkpoint_disabled_always_returns_false(self):
        """If checkpointing disabled, always returns False regardless of mode."""
        configs = [
            {"run": {"mode": "force_new"}},
            {"run": {"mode": "reuse_if_exists"}},
            {"run": {"mode": "resume_if_incomplete"}},
            {},
        ]
        for config in configs:
            assert get_load_if_exists_flag(config, checkpoint_enabled=False) is False


class TestProcessTypeIntegration:
    """Test that process_type parameter works correctly."""

    def test_hpo_process_type_ignores_completeness(self):
        """HPO process type ignores is_complete parameter."""
        config = {"run": {"mode": "reuse_if_exists"}}
        # HPO should reuse if exists, regardless of completeness
        assert (
            should_reuse_existing(
                config, exists=True, is_complete=True, process_type="hpo"
            )
            is True
        )
        assert (
            should_reuse_existing(
                config, exists=True, is_complete=False, process_type="hpo"
            )
            is True
        )

    def test_final_training_process_type_checks_completeness(self):
        """Final training process type checks is_complete parameter."""
        config = {"run": {"mode": "reuse_if_exists"}}
        # Final training should only reuse if complete
        assert (
            should_reuse_existing(
                config, exists=True, is_complete=True, process_type="final_training"
            )
            is True
        )
        assert (
            should_reuse_existing(
                config, exists=True, is_complete=False, process_type="final_training"
            )
            is False
        )

    def test_selection_process_type_ignores_completeness(self):
        """Selection process type ignores is_complete parameter."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert (
            should_reuse_existing(
                config, exists=True, is_complete=True, process_type="selection"
            )
            is True
        )

    def test_benchmarking_process_type_ignores_completeness(self):
        """Benchmarking process type ignores is_complete parameter."""
        config = {"run": {"mode": "reuse_if_exists"}}
        assert (
            should_reuse_existing(
                config, exists=True, is_complete=True, process_type="benchmarking"
            )
            is True
        )


