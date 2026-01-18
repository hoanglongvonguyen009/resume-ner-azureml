"""Unit tests for MLflow patches that prevent auto-generated run names.

Tests cover:
1. mlflow.start_run() patch validation - rejects None/empty run_name
2. MlflowClient.create_run() patch validation - rejects None/empty run_name
3. Valid run_names pass through correctly
4. Resuming existing runs (with run_id) doesn't require validation
5. Patch application and idempotency
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Any

# Import before mlflow to ensure patch is applied
from infrastructure.tracking.mlflow.patches import (
    _validate_run_name,
    _patched_start_run,
    _patched_client_create_run,
    apply_patch,
)


class TestValidateRunName:
    """Test _validate_run_name() function."""

    def test_rejects_none(self):
        """Test that None run_name raises ValueError."""
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            _validate_run_name(None, "test_site")

    def test_rejects_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            _validate_run_name("", "test_site")

    def test_rejects_whitespace_only(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            _validate_run_name("   ", "test_site")
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            _validate_run_name("\t\n", "test_site")

    def test_accepts_valid_run_name(self):
        """Test that valid run_name passes validation."""
        # Should not raise
        _validate_run_name("valid_run_name", "test_site")
        _validate_run_name("hpo_study-abc123_trial-1", "test_site")
        _validate_run_name("colab_distilbert_hpo_study-c3659fea_hpo_distilbert_test_v3_1", "test_site")


class TestPatchedStartRun:
    """Test _patched_start_run() function."""

    @patch("infrastructure.tracking.mlflow.patches._original_start_run")
    def test_validates_run_name_when_creating_new_run(self, mock_original):
        """Test that creating a new run validates run_name."""
        mock_original.return_value = Mock()
        
        # Valid run_name should pass
        _patched_start_run(run_name="valid_run_name")
        mock_original.assert_called_once_with(run_name="valid_run_name")

    @patch("infrastructure.tracking.mlflow.patches._original_start_run")
    def test_rejects_none_run_name(self, mock_original):
        """Test that None run_name is rejected."""
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            _patched_start_run(run_name=None)
        mock_original.assert_not_called()

    @patch("infrastructure.tracking.mlflow.patches._original_start_run")
    def test_rejects_empty_run_name(self, mock_original):
        """Test that empty run_name is rejected."""
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            _patched_start_run(run_name="")
        mock_original.assert_not_called()

    @patch("infrastructure.tracking.mlflow.patches._original_start_run")
    def test_allows_resuming_existing_run_with_run_id(self, mock_original):
        """Test that resuming existing run (with run_id) doesn't require run_name."""
        mock_original.return_value = Mock()
        
        # Resuming existing run should not validate run_name
        _patched_start_run(run_id="existing-run-id-123")
        mock_original.assert_called_once_with(run_id="existing-run-id-123")

    @patch("infrastructure.tracking.mlflow.patches._original_start_run")
    def test_falls_back_to_mlflow_module_if_patch_not_applied(self, mock_original):
        """Test fallback when patch hasn't been applied yet."""
        # Temporarily set _original_start_run to None
        import infrastructure.tracking.mlflow.patches as patches_module
        original_value = patches_module._original_start_run
        patches_module._original_start_run = None
        
        try:
            with patch("mlflow.start_run") as mock_mlflow_start:
                mock_mlflow_start.return_value = Mock()
                _patched_start_run(run_name="test_run")
                mock_mlflow_start.assert_called_once_with(run_name="test_run")
        finally:
            patches_module._original_start_run = original_value


class TestPatchedClientCreateRun:
    """Test _patched_client_create_run() function."""

    def test_validates_run_name(self):
        """Test that run_name is validated."""
        mock_self = Mock()
        mock_original = Mock(return_value=Mock())
        
        # Temporarily set _original_client_create_run
        import infrastructure.tracking.mlflow.patches as patches_module
        original_value = patches_module._original_client_create_run
        patches_module._original_client_create_run = mock_original
        
        try:
            # Valid run_name should pass
            _patched_client_create_run(mock_self, experiment_id="exp-123", run_name="valid_run")
            mock_original.assert_called_once_with(mock_self, experiment_id="exp-123", run_name="valid_run")
        finally:
            patches_module._original_client_create_run = original_value

    def test_rejects_none_run_name(self):
        """Test that None run_name is rejected."""
        mock_self = Mock()
        
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            _patched_client_create_run(mock_self, experiment_id="exp-123", run_name=None)

    def test_rejects_empty_run_name(self):
        """Test that empty run_name is rejected."""
        mock_self = Mock()
        
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            _patched_client_create_run(mock_self, experiment_id="exp-123", run_name="")

    def test_raises_error_if_patch_not_initialized(self):
        """Test that error is raised if patch wasn't properly initialized."""
        mock_self = Mock()
        
        # Temporarily set _original_client_create_run to None
        import infrastructure.tracking.mlflow.patches as patches_module
        original_value = patches_module._original_client_create_run
        patches_module._original_client_create_run = None
        
        try:
            with pytest.raises(RuntimeError, match="MlflowClient.create_run\\(\\) patch not properly initialized"):
                _patched_client_create_run(mock_self, experiment_id="exp-123", run_name="test")
        finally:
            patches_module._original_client_create_run = original_value


class TestPatchApplication:
    """Test apply_patch() function."""

    @patch("mlflow.start_run")
    @patch("mlflow.tracking.MlflowClient")
    def test_patch_applies_successfully(self, mock_client_class, mock_start_run):
        """Test that patch applies successfully."""
        # Reset any existing patches
        import mlflow
        if hasattr(mlflow, '_original_start_run_patched'):
            delattr(mlflow, '_original_start_run_patched')
        
        if hasattr(mock_client_class, '_create_run_patched'):
            delattr(mock_client_class, '_create_run_patched')
        
        # Apply patch
        apply_patch()
        
        # Verify patches were applied
        assert hasattr(mlflow, '_original_start_run_patched')
        assert hasattr(mock_client_class, '_create_run_patched')

    @patch("mlflow.start_run")
    @patch("mlflow.tracking.MlflowClient")
    def test_patch_is_idempotent(self, mock_client_class, mock_start_run):
        """Test that applying patch multiple times is safe."""
        import mlflow
        
        # Reset any existing patches
        if hasattr(mlflow, '_original_start_run_patched'):
            delattr(mlflow, '_original_start_run_patched')
        
        if hasattr(mock_client_class, '_create_run_patched'):
            delattr(mock_client_class, '_create_run_patched')
        
        # Apply patch twice
        apply_patch()
        apply_patch()
        
        # Should still work
        assert hasattr(mlflow, '_original_start_run_patched')
        assert hasattr(mock_client_class, '_create_run_patched')

    @patch("mlflow.start_run", side_effect=ImportError("mlflow not available"))
    def test_patch_handles_import_error_gracefully(self, mock_start_run):
        """Test that patch handles import errors gracefully."""
        import mlflow
        
        # Reset any existing patches
        if hasattr(mlflow, '_original_start_run_patched'):
            delattr(mlflow, '_original_start_run_patched')
        
        # Should not raise, just print warning
        try:
            apply_patch()
        except Exception:
            pytest.fail("apply_patch() should handle import errors gracefully")


class TestIntegrationWithMLflow:
    """Integration tests with actual MLflow patching."""

    @patch("mlflow.start_run")
    def test_patched_start_run_integration(self, mock_mlflow_start):
        """Test that patched mlflow.start_run() validates run_name."""
        import mlflow
        
        # Reset patch state
        if hasattr(mlflow, '_original_start_run_patched'):
            delattr(mlflow, '_original_start_run_patched')
        
        # Apply patch
        apply_patch()
        
        # Test that None run_name is rejected
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            mlflow.start_run(run_name=None)
        
        # Test that empty run_name is rejected
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            mlflow.start_run(run_name="")
        
        # Test that valid run_name passes
        mock_mlflow_start.return_value = Mock()
        mlflow.start_run(run_name="valid_run_name")
        mock_mlflow_start.assert_called_with(run_name="valid_run_name")

    @patch("mlflow.tracking.MlflowClient.create_run")
    def test_patched_client_create_run_integration(self, mock_client_create):
        """Test that patched MlflowClient.create_run() validates run_name."""
        from mlflow.tracking import MlflowClient
        
        # Reset patch state
        if hasattr(MlflowClient, '_create_run_patched'):
            delattr(MlflowClient, '_create_run_patched')
        
        # Apply patch
        apply_patch()
        
        client = MlflowClient()
        
        # Test that None run_name is rejected
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            client.create_run(experiment_id="exp-123", run_name=None)
        
        # Test that empty run_name is rejected
        with pytest.raises(ValueError, match="Cannot create MLflow run: run_name is None or empty"):
            client.create_run(experiment_id="exp-123", run_name="")
        
        # Test that valid run_name passes
        mock_client_create.return_value = Mock()
        client.create_run(experiment_id="exp-123", run_name="valid_run_name")
        # Note: assert_called_with includes 'self' as first argument for bound methods
        mock_client_create.assert_called_once()
        call_args = mock_client_create.call_args
        assert call_args[1]["experiment_id"] == "exp-123"
        assert call_args[1]["run_name"] == "valid_run_name"

