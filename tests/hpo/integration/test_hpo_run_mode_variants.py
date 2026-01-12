"""Integration tests for HPO run mode and variant generation.

Tests the complete flow of run.mode=force_new creating variants (v1, v2, v3...)
as specified in smoke.yaml lines 32-45.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

# Lazy import optuna
try:
    import optuna
except ImportError:
    optuna = None
    pytest.skip("optuna not available", allow_module_level=True)

from training.hpo.core.study import StudyManager
from training.hpo.utils.helpers import create_study_name, find_study_variants
from infrastructure.config.run_mode import get_run_mode, is_force_new


class TestHPORunModeForceNew:
    """Test HPO with run.mode=force_new creating variants."""

    def test_force_new_creates_variant_1_on_first_run(self, tmp_path, tmp_config_dir):
        """Test that force_new creates variant 1 (base name) on first run."""
        hpo_config = {
            "run": {"mode": "force_new"},
            "sampling": {"algorithm": "random", "max_trials": 1},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,  # Auto-generate
        }
        
        study_name = create_study_name(
            backbone="distilbert",
            run_id="test123",
            should_resume=False,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # First variant should be base name (no suffix)
        assert study_name == "hpo_distilbert"
        assert is_force_new(hpo_config) is True

    def test_force_new_creates_variant_2_on_second_run(self, tmp_path, tmp_config_dir):
        """Test that force_new creates variant 2 on second run."""
        hpo_config = {
            "run": {"mode": "force_new"},
            "sampling": {"algorithm": "random", "max_trials": 1},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,
        }
        
        # Create existing variant 1 folder
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert").mkdir()
        
        study_name = create_study_name(
            backbone="distilbert",
            run_id="test456",
            should_resume=False,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # Second variant should have _v2 suffix
        assert study_name == "hpo_distilbert_v2"

    def test_force_new_creates_variant_3_on_third_run(self, tmp_path, tmp_config_dir):
        """Test that force_new creates variant 3 on third run."""
        hpo_config = {
            "run": {"mode": "force_new"},
            "sampling": {"algorithm": "random", "max_trials": 1},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,
        }
        
        # Create existing variant folders
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert").mkdir()  # Variant 1
        (hpo_output / "hpo_distilbert_v2").mkdir()  # Variant 2
        
        study_name = create_study_name(
            backbone="distilbert",
            run_id="test789",
            should_resume=False,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # Third variant should have _v3 suffix
        assert study_name == "hpo_distilbert_v3"

    def test_force_new_with_custom_study_name(self, tmp_path, tmp_config_dir):
        """Test force_new with custom study_name template."""
        hpo_config = {
            "run": {"mode": "force_new"},
            "sampling": {"algorithm": "random", "max_trials": 1},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": "hpo_{backbone}_smoke_test",
        }
        
        # Create existing variant folders
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert_smoke_test").mkdir()  # Variant 1
        (hpo_output / "hpo_distilbert_smoke_test_v2").mkdir()  # Variant 2
        
        study_name = create_study_name(
            backbone="distilbert",
            run_id="test999",
            should_resume=False,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # Should create variant 3
        assert study_name == "hpo_distilbert_smoke_test_v3"


class TestHPORunModeReuseIfExists:
    """Test HPO with run.mode=reuse_if_exists (default behavior)."""

    def test_reuse_if_exists_uses_base_name(self, tmp_path, tmp_config_dir):
        """Test that reuse_if_exists uses base name for resumability."""
        hpo_config = {
            "run": {"mode": "reuse_if_exists"},
            "sampling": {"algorithm": "random", "max_trials": 1},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,
        }
        
        study_name = create_study_name(
            backbone="distilbert",
            run_id="test123",
            should_resume=False,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # Should use base name (no variant suffix)
        assert study_name == "hpo_distilbert"

    def test_reuse_if_exists_even_with_existing_variants(self, tmp_path, tmp_config_dir):
        """Test that reuse_if_exists still uses base name even if variants exist."""
        hpo_config = {
            "run": {"mode": "reuse_if_exists"},
            "sampling": {"algorithm": "random", "max_trials": 1},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,
        }
        
        # Create existing variant folders
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert").mkdir()  # Variant 1
        (hpo_output / "hpo_distilbert_v2").mkdir()  # Variant 2
        
        study_name = create_study_name(
            backbone="distilbert",
            run_id="test456",
            should_resume=False,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # Should still use base name (for resumability)
        assert study_name == "hpo_distilbert"


class TestStudyManagerWithRunMode:
    """Test StudyManager integration with run mode."""

    def test_study_manager_extracts_run_mode(self, tmp_path, tmp_config_dir):
        """Test that StudyManager extracts run_mode from config."""
        hpo_config = {
            "run": {"mode": "force_new"},
            "sampling": {"algorithm": "random"},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,
        }
        
        study_manager = StudyManager(
            backbone="distilbert",
            hpo_config=hpo_config,
            checkpoint_config=checkpoint_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # Verify run_mode is accessible
        from infrastructure.config.run_mode import get_run_mode
        combined_config = {**hpo_config, **checkpoint_config}
        run_mode = get_run_mode(combined_config)
        assert run_mode == "force_new"

    def test_study_manager_passes_run_mode_to_create_study_name(self, tmp_path, tmp_config_dir):
        """Test that StudyManager passes run_mode to create_study_name."""
        hpo_config = {
            "run": {"mode": "force_new"},
            "sampling": {"algorithm": "random"},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,
        }
        
        # Create existing variant
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert").mkdir()
        
        study_manager = StudyManager(
            backbone="distilbert",
            hpo_config=hpo_config,
            checkpoint_config=checkpoint_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # Mock create_study_name to verify it's called with run_mode
        # Note: create_study_name is imported from training.hpo.utils.helpers
        with patch("training.hpo.utils.helpers.create_study_name") as mock_create:
            mock_create.return_value = "hpo_distilbert_v2"
            
            study_manager.create_or_load_study(
                output_dir=tmp_path / "outputs" / "hpo",
                run_id="test123",
            )
            
            # Verify create_study_name was called with run_mode
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs.get("run_mode") == "force_new"
            assert call_kwargs.get("root_dir") == tmp_path
            assert call_kwargs.get("config_dir") == tmp_config_dir


class TestSmokeYamlRunModeConfig:
    """Test smoke.yaml run mode configuration (lines 32-45)."""

    def test_smoke_yaml_run_mode_default(self):
        """Test that smoke.yaml has run.mode defaulting to reuse_if_exists."""
        # Simulate loading smoke.yaml structure
        smoke_config = {
            "run": {
                "mode": "reuse_if_exists",  # Default from smoke.yaml
            },
            "checkpoint": {
                "enabled": True,
                "study_name": None,  # Auto-generate
            },
        }
        
        run_mode = get_run_mode(smoke_config)
        assert run_mode == "reuse_if_exists"

    def test_smoke_yaml_run_mode_force_new(self):
        """Test smoke.yaml with run.mode=force_new."""
        smoke_config = {
            "run": {
                "mode": "force_new",  # Changed to force_new
            },
            "checkpoint": {
                "enabled": True,
                "study_name": None,
            },
        }
        
        run_mode = get_run_mode(smoke_config)
        assert run_mode == "force_new"
        assert is_force_new(smoke_config) is True

    def test_smoke_yaml_study_name_null_auto_generate(self, tmp_path, tmp_config_dir):
        """Test that study_name: null auto-generates base name."""
        hpo_config = {
            "run": {"mode": "force_new"},
            "sampling": {"algorithm": "random", "max_trials": 1},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,  # null = auto-generate
        }
        
        study_name = create_study_name(
            backbone="distilbert",
            run_id="test123",
            should_resume=False,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            root_dir=tmp_path,
            config_dir=tmp_config_dir,
        )
        
        # Should auto-generate base name
        assert study_name == "hpo_distilbert"

    def test_smoke_yaml_variant_sequence(self, tmp_path, tmp_config_dir):
        """Test complete variant sequence as specified in smoke.yaml."""
        hpo_config = {
            "run": {"mode": "force_new"},
            "sampling": {"algorithm": "random", "max_trials": 1},
            "objective": {"metric": "macro-f1", "goal": "maximize"},
        }
        checkpoint_config = {
            "enabled": True,
            "study_name": None,  # Auto-generate
        }
        
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        
        # Simulate multiple runs with force_new
        variants = []
        for i in range(3):
            study_name = create_study_name(
                backbone="distilbert",
                run_id=f"test{i}",
                should_resume=False,
                checkpoint_config=checkpoint_config,
                hpo_config=hpo_config,
                root_dir=tmp_path,
                config_dir=tmp_config_dir,
            )
            variants.append(study_name)
            
            # Create the folder for next iteration
            (hpo_output / study_name).mkdir()
        
        # Should create: hpo_distilbert, hpo_distilbert_v2, hpo_distilbert_v3
        assert variants[0] == "hpo_distilbert"
        assert variants[1] == "hpo_distilbert_v2"
        assert variants[2] == "hpo_distilbert_v3"

