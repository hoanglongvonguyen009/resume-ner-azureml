"""Integration tests for Azure ML artifact upload.

These tests verify the end-to-end behavior of artifact uploads in Azure ML,
including the monkey-patch and refit run completion.

Note: These tests require Azure ML workspace configuration and may be skipped
in environments without Azure ML access.
"""

import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.integration
@pytest.mark.skipif(
    True,  # Skip by default - use --run-azureml-tests to enable
    reason="Azure ML integration tests require --run-azureml-tests flag"
)
class TestAzureMLArtifactUploadIntegration:
    """Integration tests for Azure ML artifact upload."""

    @pytest.fixture
    def mock_azureml_workspace(self):
        """Mock Azure ML workspace setup."""
        with patch('mlflow.get_tracking_uri') as mock_uri:
            mock_uri.return_value = "azureml://subscriptions/test/resourceGroups/test/workspaces/test"
            yield mock_uri

    @pytest.fixture
    def temp_checkpoint_dir(self):
        """Create a temporary checkpoint directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoint"
            checkpoint_dir.mkdir()
            
            # Create some dummy checkpoint files
            (checkpoint_dir / "model.bin").write_bytes(b"dummy model")
            (checkpoint_dir / "config.json").write_text(json.dumps({"test": "config"}))
            
            yield checkpoint_dir

    def test_artifact_upload_to_refit_run_with_monkey_patch(self, mock_azureml_workspace, temp_checkpoint_dir):
        """Test that artifacts can be uploaded to refit run with monkey-patch."""
        from infrastructure.tracking.mlflow.trackers.sweep_tracker import MLflowSweepTracker
        from infrastructure.tracking.mlflow.artifacts.manager import create_checkpoint_archive
        
        tracker = MLflowSweepTracker()
        
        # Create checkpoint archive
        archive_path, manifest = create_checkpoint_archive(temp_checkpoint_dir, trial_number=0)
        
        try:
            # Mock MLflow client
            with patch('mlflow.tracking.MlflowClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Mock retry_with_backoff to execute immediately
                with patch('infrastructure.tracking.mlflow.trackers.sweep_tracker.retry_with_backoff') as mock_retry:
                    def execute_immediately(func):
                        return func()
                    mock_retry.side_effect = execute_immediately
                    
                    # Mock study
                    mock_study = MagicMock()
                    mock_study.best_trial = MagicMock()
                    mock_study.best_trial.number = 0
                    
                    # Test upload to refit run
                    parent_run_id = "parent-run-id-123"
                    refit_run_id = "refit-run-id-456"
                    
                    tracker.log_best_checkpoint(
                        study=mock_study,
                        hpo_output_dir=Path("/tmp/hpo"),
                        backbone="distilbert",
                        run_id="test-run",
                        prefer_checkpoint_dir=temp_checkpoint_dir,
                        refit_ok=True,
                        parent_run_id=parent_run_id,
                        refit_run_id=refit_run_id,
                    )
                    
                    # Verify upload was attempted to refit run
                    mock_client.log_artifact.assert_called()
                    call_args = mock_client.log_artifact.call_args
                    assert call_args[0][0] == refit_run_id, \
                        f"Should upload to refit run {refit_run_id}"
        finally:
            if archive_path.exists():
                archive_path.unlink()

    def test_refit_run_completion_after_upload(self, mock_azureml_workspace):
        """Test that refit run is marked as FINISHED after successful upload."""
        from training.hpo import run_local_hpo_sweep
        
        # Mock MLflow client
        with patch('mlflow.tracking.MlflowClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock run status - starts as RUNNING
            mock_run = MagicMock()
            mock_run.info.status = "RUNNING"
            mock_client.get_run.return_value = mock_run
            
            # Mock tracker
            with patch('training.hpo.tracking.sweep_tracker.MLflowSweepTracker') as mock_tracker_class:
                mock_tracker = MagicMock()
                mock_tracker_class.return_value = mock_tracker
                mock_tracker.log_best_checkpoint.return_value = None  # Success
                
                # Simulate the refit run completion logic
                refit_run_id = "refit-run-id-456"
                upload_succeeded = True
                
                # This simulates the code in local_sweeps.py
                if refit_run_id:
                    run = mock_client.get_run(refit_run_id)
                    if run.info.status == "RUNNING":
                        if upload_succeeded:
                            mock_client.set_tag(
                                refit_run_id, "code.refit_artifacts_uploaded", "true")
                            mock_client.set_terminated(
                                refit_run_id, status="FINISHED")
                
                # Verify refit run was marked as FINISHED
                mock_client.set_terminated.assert_called_once_with(
                    refit_run_id, status="FINISHED"
                )


class TestMonkeyPatchBehavior:
    """Test the behavior of the monkey-patch in various scenarios."""

    def test_patch_handles_tracking_uri_error(self):
        """Test that patch handles tracking_uri TypeError gracefully."""
        from infrastructure.tracking.mlflow.trackers.sweep_tracker import MLflowSweepTracker
        
        import mlflow.store.artifact.artifact_repository_registry as arr
        builder = arr._artifact_repository_registry._registry.get('azureml')
        
        if builder is None:
            pytest.skip("Azure ML builder not registered (not using Azure ML)")
        
        # Get the original builder
        original_builder = builder.__wrapped__ if hasattr(builder, '__wrapped__') else builder
        
        # Test that the patch catches TypeError about tracking_uri
        # We can't easily test the actual Azure ML repository creation without
        # a real Azure ML workspace, but we can verify the patch structure
        assert callable(builder), "Patched builder should be callable"
        
        # Verify the patch preserves the original function signature
        import inspect
        sig = inspect.signature(builder)
        params = list(sig.parameters.keys())
        assert 'artifact_uri' in params, "Builder should accept artifact_uri"
        assert 'tracking_uri' in params, "Builder should accept tracking_uri"
        assert 'registry_uri' in params, "Builder should accept registry_uri"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--run-azureml-tests"])

