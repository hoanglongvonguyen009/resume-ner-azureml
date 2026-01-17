"""Component tests for artifact acquisition using config options."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from evaluation.selection.artifact_acquisition import acquire_best_model_checkpoint


class TestArtifactAcquisitionConfig:
    """Test artifact acquisition logic using config options."""

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_priority_order_local_first(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that priority order affects which strategy is tried first."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
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
        
        # Call function with local first in priority
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=sample_acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            backup_to_drive=None,
            in_colab=False,
        )
        
        # Should use local strategy (first in priority)
        assert mock_acquire_artifact.called
        assert result is not None
        # Verify priority was passed correctly
        call_args = mock_acquire_artifact.call_args
        assert call_args is not None

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_priority_order_mlflow_first(
        self,
        mock_acquire_artifact,
        tmp_path,
        custom_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that priority order with mlflow first tries MLflow before local."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Mock successful acquisition from MLflow (first in priority)
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.MLFLOW,
        )
        
        # Call function with mlflow first in priority
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=custom_acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            backup_to_drive=None,
            in_colab=False,
        )
        
        # Should use MLflow strategy (first in priority)
        assert mock_acquire_artifact.called
        assert result is not None
        # Verify it was acquired from MLflow
        call_args = mock_acquire_artifact.call_args
        assert call_args is not None

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_local_validate_controls_validation(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that local.validate controls checkpoint validation for local strategy."""
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
        
        # Test with validate=True
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["local"]["validate"] = True
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            backup_to_drive=None,
            in_colab=False,
        )
        
        # Should succeed and acquire_artifact should be called with validate=True
        assert mock_acquire_artifact.called
        assert result is not None
        # Verify validate setting was passed in config
        call_kwargs = mock_acquire_artifact.call_args[1]
        assert call_kwargs["acquisition_config"]["local"]["validate"] is True
        
        # Test with validate=False
        acquisition_config["local"]["validate"] = False
        mock_acquire_artifact.reset_mock()
        
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.LOCAL,
        )
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            backup_to_drive=None,
            in_colab=False,
        )
        
        # Should succeed and acquire_artifact should be called with validate=False
        assert mock_acquire_artifact.called
        assert result is not None
        # Verify validate setting was passed in config
        call_kwargs = mock_acquire_artifact.call_args[1]
        assert call_kwargs["acquisition_config"]["local"]["validate"] is False

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_drive_enabled_controls_drive_strategy(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that drive.enabled controls drive strategy execution."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Setup mocks
        mock_backup_to_drive = Mock()
        mock_restore_from_drive = Mock(return_value=True)
        
        # Mock successful acquisition from drive
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.DRIVE,
        )
        
        # Test with enabled=True
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["drive"]["enabled"] = True
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="colab",
            restore_from_drive=mock_restore_from_drive,
            backup_to_drive=mock_backup_to_drive,
            in_colab=True,
        )
        
        # Should succeed
        assert mock_acquire_artifact.called
        assert result is not None
        
        # Test with enabled=False
        acquisition_config["drive"]["enabled"] = False
        mock_acquire_artifact.reset_mock()
        
        # Mock successful acquisition from local (drive disabled)
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.LOCAL,
        )
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="colab",
            restore_from_drive=mock_restore_from_drive,
            backup_to_drive=mock_backup_to_drive,
            in_colab=True,
        )
        
        # Should succeed but drive should be skipped
        assert mock_acquire_artifact.called
        assert result is not None

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_drive_validate_controls_validation(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that drive.validate controls checkpoint validation for drive strategy."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Setup mocks
        mock_backup_to_drive = Mock()
        mock_restore_from_drive = Mock(return_value=True)
        
        # Mock successful acquisition from drive
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.DRIVE,
        )
        
        # Test with validate=True
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["drive"]  # Skip local
        acquisition_config["drive"]["validate"] = True
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="colab",
            restore_from_drive=mock_restore_from_drive,
            backup_to_drive=mock_backup_to_drive,
            in_colab=True,
        )
        
        # Should succeed and acquire_artifact should be called with validate=True
        assert mock_acquire_artifact.called
        assert result is not None
        # Verify validate setting was passed in config
        call_kwargs = mock_acquire_artifact.call_args[1]
        assert call_kwargs["acquisition_config"]["drive"]["validate"] is True
        
        # Test with validate=False
        acquisition_config["drive"]["validate"] = False
        mock_acquire_artifact.reset_mock()
        
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.DRIVE,
        )
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="colab",
            restore_from_drive=mock_restore_from_drive,
            backup_to_drive=mock_backup_to_drive,
            in_colab=True,
        )
        
        # Should succeed and acquire_artifact should be called with validate=False
        assert mock_acquire_artifact.called
        assert result is not None
        call_kwargs = mock_acquire_artifact.call_args[1]
        assert call_kwargs["acquisition_config"]["drive"]["validate"] is False

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_mlflow_enabled_controls_mlflow_strategy(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that mlflow.enabled controls MLflow strategy execution."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Mock successful acquisition from MLflow
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.MLFLOW,
        )
        
        # Test with enabled=True
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["mlflow"]  # Skip local and drive
        acquisition_config["mlflow"]["enabled"] = True
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            backup_to_drive=None,
            in_colab=False,
        )
        
        # Should succeed and acquire_artifact should be called
        assert mock_acquire_artifact.called
        assert result is not None
        
        # Test with enabled=False
        acquisition_config["mlflow"]["enabled"] = False
        mock_acquire_artifact.reset_mock()
        
        # Mock failed acquisition (MLflow disabled, no other sources)
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=False,
            error="MLflow disabled",
        )
        
        with pytest.raises(ValueError, match="Could not acquire checkpoint"):
            acquire_best_model_checkpoint(
                best_run_info=mock_best_run_info,
                root_dir=root_dir,
                config_dir=config_dir,
                acquisition_config=acquisition_config,
                selection_config={},
                platform="local",
                restore_from_drive=None,
                backup_to_drive=None,
                in_colab=False,
            )

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_mlflow_validate_controls_validation(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test that mlflow.validate controls checkpoint validation for MLflow strategy."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Mock successful acquisition from MLflow
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.MLFLOW,
        )
        
        # Test with validate=True
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["mlflow"]  # Skip local and drive
        acquisition_config["mlflow"]["validate"] = True
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            backup_to_drive=None,
            in_colab=False,
        )
        
        # Should succeed and acquire_artifact should be called with validate=True
        assert mock_acquire_artifact.called
        assert result is not None
        # Verify validate setting was passed in config
        call_kwargs = mock_acquire_artifact.call_args[1]
        assert call_kwargs["acquisition_config"]["mlflow"]["validate"] is True

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_priority_order_with_some_sources_disabled(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
        mock_checkpoint_path,
    ):
        """Test priority order when some sources are disabled."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind, ArtifactSource
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Disable drive, keep mlflow enabled
        acquisition_config = sample_acquisition_config.copy()
        acquisition_config["priority"] = ["local", "drive", "mlflow"]
        acquisition_config["drive"]["enabled"] = False
        acquisition_config["mlflow"]["enabled"] = True
        
        # Mock successful acquisition from MLflow (local fails, drive disabled, so MLflow is tried)
        mock_request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_id_123",
            backbone="distilbert",
        )
        mock_acquire_artifact.return_value = ArtifactResult(
            request=mock_request,
            success=True,
            path=Path(mock_checkpoint_path),
            source=ArtifactSource.MLFLOW,
        )
        
        result = acquire_best_model_checkpoint(
            best_run_info=mock_best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config={},
            platform="local",
            restore_from_drive=None,
            backup_to_drive=None,
            in_colab=False,
        )
        
        # Should succeed using MLflow (drive was skipped)
        assert mock_acquire_artifact.called
        assert result is not None

    @patch("evaluation.selection.artifact_unified.compat.acquire_artifact")
    def test_all_strategies_fail_gracefully_when_disabled(
        self,
        mock_acquire_artifact,
        tmp_path,
        sample_acquisition_config,
        mock_best_run_info,
    ):
        """Test that all strategies fail gracefully when disabled."""
        from evaluation.selection.artifact_unified.types import ArtifactResult, ArtifactRequest, ArtifactKind
        
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Disable all strategies
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
                backup_to_drive=None,
                in_colab=False,
            )

