"""Integration tests for MLflow tracking in benchmarking with trial_id."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from evaluation.benchmarking.orchestrator import benchmark_best_trials
from evaluation.benchmarking.utils import run_benchmarking


class TestBenchmarkMlflowTrackingWithTrialId:
    """Test MLflow tracking works correctly with trial_id extraction."""

    @patch("evaluation.benchmarking.orchestrator_original.run_benchmarking")
    @patch("evaluation.benchmarking.orchestrator_original.create_naming_context")
    @patch("evaluation.benchmarking.orchestrator_original.build_output_path")
    @patch("evaluation.benchmarking.orchestrator_original.resolve_output_path_for_colab")
    @patch("evaluation.benchmarking.orchestrator_original.validate_path_before_mkdir")
    def test_benchmark_passes_trial_id_to_run_benchmarking(
        self,
        mock_validate_path,
        mock_resolve_colab,
        mock_build_path,
        mock_create_context,
        mock_run_benchmarking,
        tmp_path,
        mock_test_data_file,
        mock_data_config,
        mock_hpo_config,
        sample_benchmark_config,
    ):
        """Test that trial_id extracted from trial_info is passed to run_benchmarking."""
        root_dir = tmp_path / "outputs"
        root_dir.mkdir()
        
        # Create mock best_trials with trial_name in new format
        checkpoint_dir = tmp_path / "checkpoint"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        (checkpoint_dir / "config.json").write_text('{"model_type": "distilbert"}')
        
        best_trials = {
            "distilbert": {
                "trial_name": "trial-25d03eeb",
                "trial_id": None,  # Not set, should use trial_name
                "checkpoint_dir": str(checkpoint_dir),
                "study_key_hash": "abc123def456",  # Required for champion format
                "trial_key_hash": "xyz789uvw012",  # Required for champion format
                "hyperparameters": {"learning_rate": 2e-5},
                "metrics": {"macro-f1": 0.75},
            }
        }
        
        # Setup mocks
        mock_validate_path.side_effect = lambda p, **kwargs: p
        mock_resolve_colab.side_effect = lambda p: p
        mock_build_path.return_value = root_dir / "benchmarking" / "test"
        mock_context = Mock()
        mock_context.trial_id = "trial-25d03eeb"
        mock_create_context.return_value = mock_context
        mock_run_benchmarking.return_value = True
        
        # Create benchmark script
        benchmark_script = root_dir / "src" / "evaluation" / "benchmarking" / "cli.py"
        benchmark_script.parent.mkdir(parents=True, exist_ok=True)
        benchmark_script.write_text("# mock script")
        
        # Call benchmark_best_trials
        result = benchmark_best_trials(
            best_trials=best_trials,
            test_data_path=mock_test_data_file,
            root_dir=root_dir,
            environment="local",
            data_config=mock_data_config,
            hpo_config=mock_hpo_config,
            benchmark_config=sample_benchmark_config,
        )
        
        # Verify run_benchmarking was called with trial_id
        assert mock_run_benchmarking.called
        call_kwargs = mock_run_benchmarking.call_args.kwargs
        # Should extract trial_id from trial_name (trial-25d03eeb)
        assert call_kwargs["trial_id"] == "trial-25d03eeb"

    @patch("evaluation.benchmarking.orchestrator_original.run_benchmarking")
    @patch("evaluation.benchmarking.orchestrator_original.create_naming_context")
    @patch("evaluation.benchmarking.orchestrator_original.build_output_path")
    @patch("evaluation.benchmarking.orchestrator_original.resolve_output_path_for_colab")
    @patch("evaluation.benchmarking.orchestrator_original.validate_path_before_mkdir")
    def test_benchmark_passes_trial_id_old_format(
        self,
        mock_validate_path,
        mock_resolve_colab,
        mock_build_path,
        mock_create_context,
        mock_run_benchmarking,
        tmp_path,
        mock_test_data_file,
        mock_data_config,
        mock_hpo_config,
        sample_benchmark_config,
    ):
        """Test that trial_id extracted from trial_info handles old format (trial_1_20251231_161745).
        
        Updated to use champion format (with study_key_hash and trial_key_hash) as legacy format
        is no longer supported per Phase 3 refactoring.
        """
        root_dir = tmp_path / "outputs"
        root_dir.mkdir()
        
        # Create mock best_trials with trial_name in old format but champion data structure
        checkpoint_dir = tmp_path / "checkpoint"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        (checkpoint_dir / "config.json").write_text('{"model_type": "distilbert"}')
        
        best_trials = {
            "distilbert": {
                "trial_name": "trial_1_20251231_161745",
                "trial_id": None,
                "checkpoint_dir": str(checkpoint_dir),
                "study_key_hash": "abc123def456",  # Required for champion format
                "trial_key_hash": "xyz789uvw012",  # Required for champion format
                "hyperparameters": {"learning_rate": 2e-5},
                "metrics": {"macro-f1": 0.75},
            }
        }
        
        # Setup mocks
        mock_validate_path.side_effect = lambda p, **kwargs: p
        mock_resolve_colab.side_effect = lambda p: p
        mock_build_path.return_value = root_dir / "benchmarking" / "test"
        mock_context = Mock()
        mock_context.trial_id = "1_20251231_161745"
        mock_create_context.return_value = mock_context
        mock_run_benchmarking.return_value = True
        
        # Create benchmark script
        benchmark_script = root_dir / "src" / "evaluation" / "benchmarking" / "cli.py"
        benchmark_script.parent.mkdir(parents=True, exist_ok=True)
        benchmark_script.write_text("# mock script")
        
        # Call benchmark_best_trials
        result = benchmark_best_trials(
            best_trials=best_trials,
            test_data_path=mock_test_data_file,
            root_dir=root_dir,
            environment="local",
            data_config=mock_data_config,
            hpo_config=mock_hpo_config,
            benchmark_config=sample_benchmark_config,
        )
        
        # Verify run_benchmarking was called with trial_id (old format: remove "trial_" prefix)
        assert mock_run_benchmarking.called
        call_kwargs = mock_run_benchmarking.call_args.kwargs
        # Old format: should remove "trial_" prefix
        assert call_kwargs["trial_id"] == "1_20251231_161745"

    @patch("evaluation.benchmarking.utils.subprocess.run")
    @patch("infrastructure.naming.mlflow.run_names.build_mlflow_run_name")
    @patch("infrastructure.naming.create_naming_context")
    @patch("common.shared.platform_detection.detect_platform")
    def test_run_benchmarking_mlflow_tracking_with_trial_id(
        self,
        mock_detect_platform,
        mock_create_context,
        mock_build_run_name,
        mock_subprocess,
        tmp_path,
        mock_checkpoint_dir,
        mock_test_data_file,
    ):
        """Test that MLflow tracking works when trial_id is provided."""
        project_root = tmp_path
        output_path = tmp_path / "benchmark.json"
        
        # Mock build_mlflow_run_name to return a simple name (avoids naming policy complexity)
        mock_build_run_name.return_value = "local_distilbert_benchmark_trial-25d03eeb"
        
        # Mock subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Create mock benchmark script
        benchmark_script = project_root / "src" / "evaluation" / "benchmarking" / "cli.py"
        benchmark_script.parent.mkdir(parents=True, exist_ok=True)
        benchmark_script.write_text("# mock script")
        
        # Create mock benchmark output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('{"batch_size_1": {"mean_latency_ms": 5.0}}')
        
        # Mock naming context
        mock_context = Mock()
        mock_context.trial_id = "trial-25d03eeb"
        mock_create_context.return_value = mock_context
        mock_detect_platform.return_value = "local"
        
        # Mock MLflow tracker
        mock_tracker = Mock()
        mock_run = Mock()
        mock_run.run_id = "test_run_id"
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = Mock(return_value=mock_run)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_tracker.start_benchmark_run = Mock(return_value=mock_context_manager)
        
        # Call with trial_id (pass tracker as parameter)
        success = run_benchmarking(
            checkpoint_dir=mock_checkpoint_dir,
            test_data_path=mock_test_data_file,
            output_path=output_path,
            batch_sizes=[1],
            iterations=100,
            warmup_iterations=10,
            max_length=512,
            device=None,
            project_root=project_root,
            trial_id="trial-25d03eeb",
            benchmark_source="hpo_trial",
            study_key_hash="abc123",
            trial_key_hash="def456",
            tracker=mock_tracker,  # Pass tracker as parameter
        )
        
        # Verify MLflow tracker was called
        assert mock_tracker.start_benchmark_run.called
        
        # Verify naming context was created with trial_id
        assert mock_create_context.called
        call_kwargs = mock_create_context.call_args.kwargs
        assert call_kwargs["trial_id"] == "trial-25d03eeb"

    @patch("evaluation.benchmarking.utils.subprocess.run")
    @patch("infrastructure.naming.mlflow.run_names.build_mlflow_run_name")
    @patch("infrastructure.naming.create_naming_context")
    @patch("common.shared.platform_detection.detect_platform")
    def test_run_benchmarking_mlflow_tracking_fallback_to_trial_key_hash(
        self,
        mock_detect_platform,
        mock_create_context,
        mock_build_run_name,
        mock_subprocess,
        tmp_path,
        mock_checkpoint_dir,
        mock_test_data_file,
    ):
        """Test that MLflow tracking works when trial_id is constructed from trial_key_hash."""
        project_root = tmp_path
        output_path = tmp_path / "benchmark.json"
        
        # Mock build_mlflow_run_name to return a simple name (avoids naming policy complexity)
        mock_build_run_name.return_value = "local_distilbert_benchmark_trial-25d03eeb"
        
        # Mock subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Create mock benchmark script
        benchmark_script = project_root / "src" / "evaluation" / "benchmarking" / "cli.py"
        benchmark_script.parent.mkdir(parents=True, exist_ok=True)
        benchmark_script.write_text("# mock script")
        
        # Create mock benchmark output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('{"batch_size_1": {"mean_latency_ms": 5.0}}')
        
        # Mock naming context
        mock_context = Mock()
        mock_context.trial_id = "trial-25d03eeb"
        mock_create_context.return_value = mock_context
        mock_detect_platform.return_value = "local"
        
        # Mock MLflow tracker
        mock_tracker = Mock()
        mock_run = Mock()
        mock_run.run_id = "test_run_id"
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = Mock(return_value=mock_run)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_tracker.start_benchmark_run = Mock(return_value=mock_context_manager)
        
        # Call without trial_id, should fallback to trial_key_hash (pass tracker as parameter)
        trial_key_hash = "25d03eebe00267cc"
        success = run_benchmarking(
            checkpoint_dir=mock_checkpoint_dir,
            test_data_path=mock_test_data_file,
            output_path=output_path,
            batch_sizes=[1],
            iterations=100,
            warmup_iterations=10,
            max_length=512,
            device=None,
            project_root=project_root,
            trial_id=None,  # Not provided
            benchmark_source="hpo_trial",
            study_key_hash="abc123",
            trial_key_hash=trial_key_hash,
            tracker=mock_tracker,  # Pass tracker as parameter
        )
        
        # Verify MLflow tracker was called
        assert mock_tracker.start_benchmark_run.called
        
        # Verify naming context was created with constructed trial_id
        assert mock_create_context.called
        call_kwargs = mock_create_context.call_args.kwargs
        # Should construct as trial-{first_8_chars_of_hash}
        assert call_kwargs["trial_id"] == f"trial-{trial_key_hash[:8]}"

