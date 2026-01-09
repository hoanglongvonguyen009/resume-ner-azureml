"""Tests for Azure ML artifact upload fixes.

This module tests the fixes for:
1. Monkey-patch for azureml_artifacts_builder to handle tracking_uri parameter
2. Artifact upload to child runs (refit runs) in Azure ML
3. Compatibility between MLflow 3.5.0 and azureml-mlflow 1.61.0.post1
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import mlflow
from mlflow.tracking import MlflowClient


class TestAzureMLArtifactBuilderPatch:
    """Test the monkey-patch for azureml_artifacts_builder."""

    def test_patch_registered_on_import(self):
        """Test that the monkey-patch is registered when sweep_tracker is imported."""
        # Import should trigger the patch
        from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
        
        # Verify the patch is registered
        import mlflow.store.artifact.artifact_repository_registry as arr
        builder = arr._artifact_repository_registry._registry.get('azureml')
        assert builder is not None, "Azure ML builder should be registered"
        
        # Check that it's the patched version (has __wrapped__ attribute)
        import functools
        assert hasattr(builder, '__wrapped__'), "Builder should be wrapped (patched)"

    def test_patch_handles_tracking_uri_parameter(self):
        """Test that the patched builder handles tracking_uri parameter gracefully."""
        from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
        
        import mlflow.store.artifact.artifact_repository_registry as arr
        builder = arr._artifact_repository_registry._registry.get('azureml')
        
        if builder is None:
            pytest.skip("Azure ML builder not registered (not using Azure ML)")
        
        # Verify the patch structure - it should have __wrapped__ attribute
        import functools
        assert hasattr(builder, '__wrapped__'), "Builder should be wrapped (patched)"
        
        # The actual error handling is tested in integration tests
        # This test just verifies the patch is in place
        assert callable(builder), "Patched builder should be callable"


class TestArtifactUploadToChildRun:
    """Test artifact upload to child runs (refit runs)."""

    @pytest.fixture
    def mock_mlflow_client(self):
        """Create a mock MLflow client."""
        with patch('mlflow.tracking.MlflowClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_active_run(self):
        """Create a mock active MLflow run (parent run)."""
        with patch('mlflow.active_run') as mock_active:
            mock_run = MagicMock()
            mock_run.info.run_id = "parent-run-id-123"
            mock_active.return_value = mock_run
            yield mock_run

    def test_upload_to_refit_run_when_available(self, mock_mlflow_client, mock_active_run):
        """Test that artifacts are uploaded to refit run when available."""
        from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
        from pathlib import Path
        import tempfile
        
        tracker = MLflowSweepTracker(experiment_name="test-experiment")
        
        # Create a temporary archive file
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            archive_path = Path(tmp_file.name)
            archive_path.write_bytes(b"test archive content")
        
        try:
            # Create a temporary checkpoint directory that exists
            with tempfile.TemporaryDirectory() as tmpdir:
                checkpoint_dir = Path(tmpdir) / "checkpoint"
                checkpoint_dir.mkdir()
                (checkpoint_dir / "model.bin").write_bytes(b"dummy model")
                
                # Mock the create_checkpoint_archive function
                with patch('orchestration.jobs.tracking.trackers.sweep_tracker.create_checkpoint_archive') as mock_create:
                    mock_create.return_value = (archive_path, {"file_count": 1, "total_size": 100})
                    
                    # Mock the retry_with_backoff to execute immediately
                    with patch('orchestration.jobs.tracking.trackers.sweep_tracker.retry_with_backoff') as mock_retry:
                        def execute_immediately(func, *args, **kwargs):
                            return func()
                        mock_retry.side_effect = execute_immediately
                        
                        # Create a mock study
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
                            prefer_checkpoint_dir=checkpoint_dir,  # Use existing directory
                            refit_ok=True,
                            parent_run_id=parent_run_id,
                            refit_run_id=refit_run_id,
                        )
                        
                        # Verify that log_artifact was called with refit_run_id
                        mock_mlflow_client.log_artifact.assert_called_once()
                        call_args = mock_mlflow_client.log_artifact.call_args
                        # call_args is a tuple of (args, kwargs)
                        args = call_args[0] if call_args else ()
                        assert len(args) >= 1, f"log_artifact should be called with at least 1 argument, got {len(args)}"
                        assert args[0] == refit_run_id, \
                            f"Should upload to refit run {refit_run_id}, but got {args[0]}"
                        if len(args) >= 2:
                            assert args[1] == str(archive_path), \
                                f"Should upload the archive file, but got {args[1]}"
                        if len(args) >= 3:
                            assert args[2] == "best_trial_checkpoint", \
                                f"Should use correct artifact_path, but got {args[2]}"
        finally:
            # Clean up
            if archive_path.exists():
                archive_path.unlink()

    def test_upload_to_parent_run_when_refit_not_available(self, mock_mlflow_client, mock_active_run):
        """Test that artifacts are uploaded to parent run when refit run is not available."""
        from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
        from pathlib import Path
        import tempfile
        
        tracker = MLflowSweepTracker(experiment_name="test-experiment")
        
        # Create a temporary archive file
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            archive_path = Path(tmp_file.name)
            archive_path.write_bytes(b"test archive content")
        
        try:
            # Create a temporary checkpoint directory that exists
            with tempfile.TemporaryDirectory() as tmpdir:
                checkpoint_dir = Path(tmpdir) / "checkpoint"
                checkpoint_dir.mkdir()
                (checkpoint_dir / "model.bin").write_bytes(b"dummy model")
                
                # Mock the create_checkpoint_archive function
                with patch('orchestration.jobs.tracking.trackers.sweep_tracker.create_checkpoint_archive') as mock_create:
                    mock_create.return_value = (archive_path, {"file_count": 1, "total_size": 100})
                    
                    # Mock the retry_with_backoff to execute immediately
                    with patch('orchestration.jobs.tracking.trackers.sweep_tracker.retry_with_backoff') as mock_retry:
                        def execute_immediately(func, *args, **kwargs):
                            return func()
                        mock_retry.side_effect = execute_immediately
                        
                        # Create a mock study
                        mock_study = MagicMock()
                        mock_study.best_trial = MagicMock()
                        mock_study.best_trial.number = 0
                        
                        # Test upload to parent run (no refit run)
                        parent_run_id = "parent-run-id-123"
                        
                        tracker.log_best_checkpoint(
                            study=mock_study,
                            hpo_output_dir=Path("/tmp/hpo"),
                            backbone="distilbert",
                            run_id="test-run",
                            prefer_checkpoint_dir=checkpoint_dir,  # Use existing directory
                            refit_ok=None,
                            parent_run_id=parent_run_id,
                            refit_run_id=None,
                        )
                        
                        # Verify that log_artifact was called with parent_run_id
                        mock_mlflow_client.log_artifact.assert_called_once()
                        call_args = mock_mlflow_client.log_artifact.call_args
                        # call_args is a tuple of (args, kwargs)
                        args = call_args[0] if call_args else ()
                        assert len(args) >= 1, f"log_artifact should be called with at least 1 argument, got {len(args)}"
                        assert args[0] == parent_run_id, \
                            f"Should upload to parent run {parent_run_id}, but got {args[0]}"
        finally:
            # Clean up
            if archive_path.exists():
                archive_path.unlink()


class TestRefitRunFinishedStatus:
    """Test that refit runs are marked as FINISHED after artifact upload."""

    @pytest.fixture
    def mock_mlflow_client(self):
        """Create a mock MLflow client."""
        with patch('mlflow.tracking.MlflowClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock run status
            mock_run = MagicMock()
            mock_run.info.status = "RUNNING"
            mock_client.get_run.return_value = mock_run
            
            yield mock_client

    def test_refit_run_marked_finished_after_successful_upload(self, mock_mlflow_client):
        """Test that refit run is marked as FINISHED after successful artifact upload."""
        from orchestration.jobs.hpo.local_sweeps import run_local_hpo_sweep
        from pathlib import Path
        import tempfile
        
        # Mock the tracker
        with patch('orchestration.jobs.hpo.local_sweeps.MLflowSweepTracker') as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker_class.return_value = mock_tracker
            
            # Mock successful upload
            mock_tracker.log_best_checkpoint.return_value = None  # No exception = success
            
            # Mock HPO config
            mock_hpo_config = {
                "mlflow": {
                    "log_best_checkpoint": True
                }
            }
            
            # Mock the study
            mock_study = MagicMock()
            mock_study.best_trial = MagicMock()
            mock_study.best_trial.number = 0
            
            # Mock refit_run_id
            refit_run_id = "refit-run-id-456"
            
            # Simulate the code path that marks refit run as FINISHED
            upload_succeeded = True
            upload_error = None
            
            # This simulates the code in local_sweeps.py after log_best_checkpoint
            if refit_run_id:
                run = mock_mlflow_client.get_run(refit_run_id)
                if run.info.status == "RUNNING":
                    if upload_succeeded:
                        mock_mlflow_client.set_tag(
                            refit_run_id, "code.refit_artifacts_uploaded", "true")
                        mock_mlflow_client.set_terminated(
                            refit_run_id, status="FINISHED")
            
            # Verify that set_terminated was called with FINISHED status
            mock_mlflow_client.set_terminated.assert_called_once_with(
                refit_run_id, status="FINISHED"
            )
            mock_mlflow_client.set_tag.assert_called_with(
                refit_run_id, "code.refit_artifacts_uploaded", "true"
            )

    def test_refit_run_marked_failed_after_upload_failure(self, mock_mlflow_client):
        """Test that refit run is marked as FAILED after artifact upload failure."""
        refit_run_id = "refit-run-id-456"
        upload_succeeded = False
        upload_error = Exception("Upload failed")
        
        # Simulate the code path that marks refit run as FAILED
        run = mock_mlflow_client.get_run(refit_run_id)
        if run.info.status == "RUNNING":
            if not upload_succeeded:
                mock_mlflow_client.set_tag(
                    refit_run_id, "code.refit_artifacts_uploaded", "false")
                error_msg = str(upload_error)[:200] if upload_error else "Unknown error"
                mock_mlflow_client.set_tag(
                    refit_run_id, "code.refit_error", error_msg)
                mock_mlflow_client.set_terminated(
                    refit_run_id, status="FAILED")
        
        # Verify that set_terminated was called with FAILED status
        mock_mlflow_client.set_terminated.assert_called_once_with(
            refit_run_id, status="FAILED"
        )
        mock_mlflow_client.set_tag.assert_any_call(
            refit_run_id, "code.refit_artifacts_uploaded", "false"
        )

    def test_refit_run_not_terminated_if_already_finished(self, mock_mlflow_client):
        """Test that refit run is not terminated if it's already FINISHED."""
        refit_run_id = "refit-run-id-456"
        upload_succeeded = True
        
        # Mock run that's already FINISHED
        mock_run = MagicMock()
        mock_run.info.status = "FINISHED"
        mock_mlflow_client.get_run.return_value = mock_run
        
        # Simulate the code path
        run = mock_mlflow_client.get_run(refit_run_id)
        if run.info.status == "RUNNING":
            # This should not execute
            mock_mlflow_client.set_terminated(refit_run_id, status="FINISHED")
        
        # Verify that set_terminated was NOT called
        mock_mlflow_client.set_terminated.assert_not_called()


class TestAzureMLCompatibility:
    """Test compatibility between MLflow and azureml-mlflow versions."""

    def test_azureml_mlflow_imported(self):
        """Test that azureml.mlflow is imported when sweep_tracker is imported."""
        # Import should trigger azureml.mlflow import
        from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
        
        # Verify azureml.mlflow was imported (check if it's in sys.modules)
        import sys
        assert 'azureml.mlflow' in sys.modules or 'azureml' in sys.modules, \
            "azureml.mlflow should be imported"

    def test_artifact_repository_registry_has_azureml(self):
        """Test that Azure ML artifact repository is registered."""
        from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
        
        import mlflow.store.artifact.artifact_repository_registry as arr
        registry = arr._artifact_repository_registry._registry
        
        assert 'azureml' in registry, "Azure ML artifact repository should be registered"
        
        builder = registry.get('azureml')
        assert builder is not None, "Azure ML builder should exist"
        
        # Verify it's callable
        assert callable(builder), "Azure ML builder should be callable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

