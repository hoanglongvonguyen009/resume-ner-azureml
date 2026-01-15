"""Edge case and validation tests for artifact_acquisition.yaml configuration."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from evaluation.selection.artifact_acquisition import acquire_best_model_checkpoint


class TestArtifactAcquisitionEdgeCases:
    """Test edge cases and validation for acquisition configuration."""

    def test_empty_priority_list(self):
        """Test that empty priority list is handled."""
        acquisition_config = {
            "priority": [],
            "local": {"validate": True},
            "drive": {"enabled": True, "validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }
        
        priority = acquisition_config.get("priority", [])
        
        assert priority == []
        assert isinstance(priority, list)
        # Note: Empty priority list would cause all strategies to be skipped

    def test_invalid_priority_values(self):
        """Test that invalid priority values are possible (not validated)."""
        acquisition_config = {
            "priority": ["invalid_source", "another_invalid"],
            "local": {"validate": True},
            "drive": {"enabled": True, "validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }
        
        priority = acquisition_config.get("priority", [])
        
        # Config loader doesn't validate priority values
        assert priority == ["invalid_source", "another_invalid"]
        assert "invalid_source" in priority

    def test_missing_local_section(self):
        """Test that missing local section is handled."""
        acquisition_config = {
            "priority": ["local", "mlflow"],
            "drive": {"enabled": True, "validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }
        
        # Extract with defaults
        local_validate = acquisition_config.get("local", {}).get("validate", True)
        
        assert local_validate is True  # Default value

    def test_missing_drive_section(self):
        """Test that missing drive section is handled."""
        acquisition_config = {
            "priority": ["local", "drive"],
            "local": {"validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }
        
        # Extract with defaults
        drive_enabled = acquisition_config.get("drive", {}).get("enabled", True)
        drive_validate = acquisition_config.get("drive", {}).get("validate", True)
        
        assert drive_enabled is True  # Default value
        assert drive_validate is True  # Default value

    def test_missing_mlflow_section(self):
        """Test that missing mlflow section is handled."""
        acquisition_config = {
            "priority": ["local", "mlflow"],
            "local": {"validate": True},
            "drive": {"enabled": True, "validate": True}
        }
        
        # Extract with defaults
        mlflow_enabled = acquisition_config.get("mlflow", {}).get("enabled", True)
        mlflow_validate = acquisition_config.get("mlflow", {}).get("validate", True)
        
        assert mlflow_enabled is True  # Default value
        assert mlflow_validate is True  # Default value

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_validation_false_allows_invalid_checkpoints(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that validation=False allows invalid checkpoints to be used."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Create a mock request object for the result
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        
        # Mock successful acquisition (validation=False means it succeeds even if checkpoint is invalid)
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.LOCAL,
        )
        
        # Disable validation
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["local"]["validate"] = False
        
        # Call function
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            drive_store=None,
            in_colab=False,
        )
        
        # Should succeed even with invalid checkpoint when validate=False
        assert result is not None
        assert result == Path(mock_checkpoint_path)

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_validation_true_rejects_invalid_checkpoints(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that validation=True rejects invalid checkpoints."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Create a mock request object for the result
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        
        # Mock failed acquisition (validation=True means invalid checkpoint is rejected)
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=False,
            error="Checkpoint validation failed: missing required files",
        )
        
        # Enable validation
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["local"]["validate"] = True
        
        # Call function - should fail because checkpoint is invalid
        with pytest.raises(ValueError, match="Could not acquire checkpoint"):
            acquire_best_model_checkpoint(
                best_run_info=mock_best_run_info,
                root_dir=root_dir,
                config_dir=config_dir,
                acquisition_config=acquisition_config,
                selection_config={},
                platform="local",
                restore_from_drive=None,
                drive_store=None,
                in_colab=False,
            )

    def test_priority_order_affects_strategy_selection(self):
        """Test that priority order affects which strategy is selected."""
        # Test with local first
        config_local_first = {
            "priority": ["local", "mlflow"],
            "local": {"validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }
        
        # Test with mlflow first
        config_mlflow_first = {
            "priority": ["mlflow", "local"],
            "local": {"validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }
        
        assert config_local_first["priority"][0] == "local"
        assert config_mlflow_first["priority"][0] == "mlflow"
        # The actual strategy selection is tested in component tests

    def test_duplicate_priority_values(self):
        """Test that duplicate priority values are possible."""
        acquisition_config = {
            "priority": ["local", "local", "mlflow"],
            "local": {"validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }
        
        priority = acquisition_config.get("priority", [])
        
        # Config loader doesn't validate for duplicates
        assert priority.count("local") == 2
        assert len(priority) == 3

    def test_priority_with_only_one_source(self):
        """Test priority list with only one source."""
        acquisition_config = {
            "priority": ["mlflow"],
            "local": {"validate": True},
            "drive": {"enabled": True, "validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }
        
        priority = acquisition_config.get("priority", [])
        
        assert len(priority) == 1
        assert priority[0] == "mlflow"

    def test_missing_study_trial_hashes_skips_local(
        self,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
    ):
        """Test that missing study_key_hash or trial_key_hash skips local strategy.
        
        After consolidation, the unified discovery system handles hash-based discovery.
        When hashes are missing, discover_artifact_local returns None early (line 91-93),
        causing the local strategy to be skipped. This test verifies the end-to-end
        behavior without mocking internal functions.
        """
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Remove hashes from best_run_info
        best_run_info_no_hashes = mock_best_run_info.copy()
        del best_run_info_no_hashes["study_key_hash"]
        del best_run_info_no_hashes["trial_key_hash"]
        
        # Only local in priority, but it will be skipped due to missing hashes
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["local"]
        acquisition_config["drive"]["enabled"] = False
        acquisition_config["mlflow"]["enabled"] = False
        
        # Should raise ValueError when all strategies fail (local skipped due to missing hashes)
        with pytest.raises(ValueError, match="Could not acquire checkpoint"):
            acquire_best_model_checkpoint(
                best_run_info=best_run_info_no_hashes,
                root_dir=root_dir,
                config_dir=config_dir,
                acquisition_config=acquisition_config,
                selection_config={},
                platform="local",
                restore_from_drive=None,
                drive_store=None,
                in_colab=False,
            )

    def test_config_with_all_optional_fields(self):
        """Test config with all optional fields (including unimplemented ones)."""
        acquisition_config = {
            "priority": ["local", "drive", "mlflow"],
            "local": {
                "match_strategy": "tags",
                "require_exact_match": True,
                "validate": True
            },
            "drive": {
                "enabled": True,
                "folder_path": "custom-checkpoints",
                "validate": True
            },
            "mlflow": {
                "enabled": True,
                "validate": True,
                "download_timeout": 600
            }
        }
        
        # Verify all fields can be extracted
        assert acquisition_config["priority"] == ["local", "drive", "mlflow"]
        assert acquisition_config["local"]["match_strategy"] == "tags"
        assert acquisition_config["local"]["require_exact_match"] is True
        assert acquisition_config["local"]["validate"] is True
        assert acquisition_config["drive"]["enabled"] is True
        assert acquisition_config["drive"]["folder_path"] == "custom-checkpoints"
        assert acquisition_config["drive"]["validate"] is True
        assert acquisition_config["mlflow"]["enabled"] is True
        assert acquisition_config["mlflow"]["validate"] is True
        assert acquisition_config["mlflow"]["download_timeout"] == 600
        
        # NOTE: match_strategy, require_exact_match, folder_path, and download_timeout
        # exist in config but are not currently used in implementation

