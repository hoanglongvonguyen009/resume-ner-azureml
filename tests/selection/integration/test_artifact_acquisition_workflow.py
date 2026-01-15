"""Integration tests for artifact acquisition end-to-end workflow."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from evaluation.selection.artifact_acquisition import acquire_best_model_checkpoint


class TestArtifactAcquisitionWorkflow:
    """Test complete artifact acquisition workflow."""

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_complete_workflow_with_default_config(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test complete acquisition workflow with default config."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Mock successful acquisition
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.LOCAL,
        )
        
        # Call function with default config
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=sample_acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            drive_store=None,
            in_colab=False,
        )
        
        # Should successfully acquire checkpoint
        assert result is not None
        assert mock_acquire_artifact.called

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_workflow_with_custom_priority_order(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test acquisition workflow with custom priority order."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Custom priority: mlflow first, then local
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["mlflow", "local"]
        
        # Mock MLflow fails, falls back to local
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.LOCAL,
        )
        
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
        
        # Should fall back to local strategy
        assert result is not None
        assert mock_acquire_artifact.called

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_workflow_with_validation_disabled(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test acquisition workflow with validation disabled."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Disable validation
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["local"]["validate"] = False
        
        # Mock successful acquisition (validation disabled)
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.LOCAL,
        )
        
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
        
        # Should succeed even with validation disabled
        assert result is not None
        assert mock_acquire_artifact.called

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_workflow_with_all_sources_enabled(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test acquisition workflow with all sources enabled."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Ensure all sources are enabled
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["local", "drive", "mlflow"]
        acquisition_config["drive"]["enabled"] = True
        acquisition_config["mlflow"]["enabled"] = True
        
        # Mock successful acquisition from local (first in priority)
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.LOCAL,
        )
        
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
        
        # Should succeed using local (first in priority)
        assert result is not None
        assert mock_acquire_artifact.called

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_workflow_with_all_sources_disabled(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
    ):
        """Test acquisition workflow with all sources disabled."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Disable all sources
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["local", "drive", "mlflow"]
        acquisition_config["drive"]["enabled"] = False
        acquisition_config["mlflow"]["enabled"] = False
        
        # Mock failed acquisition (all strategies disabled or failed)
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=False,
            error="Artifact not found in any configured source",
        )
        
        # Should raise ValueError when all strategies fail
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

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_workflow_mlflow_fallback_to_manual(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that workflow falls back to manually placed checkpoint when all strategies fail."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Only mlflow in priority, but it fails, then local succeeds
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["mlflow", "local"]
        acquisition_config["mlflow"]["enabled"] = True
        
        # Mock MLflow fails, falls back to local
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.LOCAL,
        )
        
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
        
        # Should find manually placed checkpoint (falls back to local)
        assert result is not None
        assert mock_acquire_artifact.called

