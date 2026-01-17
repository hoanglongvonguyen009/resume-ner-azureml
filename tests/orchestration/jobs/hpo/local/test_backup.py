"""Unit tests for HPO backup to Drive functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

from orchestration.jobs.hpo.local.backup import (
    backup_hpo_study_to_drive,
    create_incremental_backup_callback,
    create_study_db_backup_callback,
    immediate_backup_if_needed,
    _should_skip_backup,
)


class TestBackupHpoStudyToDrive:
    """Test backup_hpo_study_to_drive function."""

    def test_backup_v2_study_folder_found_locally(self, tmp_path):
        """Test that v2 study folder is found and study.db is backed up."""
        # Setup: Create v2 study folder structure
        backbone_output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = backbone_output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        study_db = study_folder / "study.db"
        study_db.write_text("test database content")
        
        # Create trial folder to make it a valid v2 study folder
        trial_folder = study_folder / "trial-abc123"
        trial_folder.mkdir()
        (trial_folder / "trial_meta.json").write_text('{"trial_number": 0}')

        checkpoint_config = {"enabled": True, "study_name": "hpo_distilbert_test_v3"}
        hpo_config = {}
        backup_to_drive_mock = MagicMock(return_value=True)

        # Mock is_drive_path to return False for local paths
        with patch("common.shared.platform_detection.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False
            
            # Execute
            backup_hpo_study_to_drive(
                backbone="distilbert",
                backbone_output_dir=backbone_output_dir,
                checkpoint_config=checkpoint_config,
                hpo_config=hpo_config,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
            )

        # Verify: study.db should be backed up (file backup)
        assert backup_to_drive_mock.called
        calls = backup_to_drive_mock.call_args_list
        
        # Should have at least one call for study.db (is_directory=False)
        # Check both positional args and keyword args
        file_backup_calls = [
            c for c in calls 
            if (len(c[0]) >= 2 and c[0][1] is False) or 
               (c.kwargs.get('is_directory') is False) or
               (len(c[0]) == 1 and 'is_directory' in c.kwargs and c.kwargs['is_directory'] is False)
        ]
        assert len(file_backup_calls) > 0, f"study.db file backup not called. Calls: {calls}"
        
        # Verify study.db path was backed up
        study_db_backed_up = any(
            (len(call[0]) > 0 and (call[0][0] == study_db or str(call[0][0]) == str(study_db))) or
            (call.kwargs.get('path') == study_db if 'path' in call.kwargs else False)
            for call in file_backup_calls
        )
        assert study_db_backed_up, f"study.db was not backed up. File calls: {file_backup_calls}"
        
        # Should also backup study folder (is_directory=True)
        dir_backup_calls = [
            c for c in calls 
            if (len(c[0]) >= 2 and c[0][1] is True) or 
               (c.kwargs.get('is_directory') is True) or
               (len(c[0]) == 1 and 'is_directory' in c.kwargs and c.kwargs['is_directory'] is True)
        ]
        assert len(dir_backup_calls) > 0, f"study folder backup not called. Calls: {calls}"

    def test_backup_skips_when_already_in_drive(self, tmp_path):
        """Test that backup is skipped when study.db is already in Drive."""
        # Setup: Create v2 study folder in Drive location
        drive_base = tmp_path / "content" / "drive" / "MyDrive" / "resume-ner-azureml"
        backbone_output_dir = drive_base / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = backbone_output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        study_db = study_folder / "study.db"
        study_db.write_text("test database content")
        
        # Create trial folder
        trial_folder = study_folder / "trial-abc123"
        trial_folder.mkdir()
        (trial_folder / "trial_meta.json").write_text('{"trial_number": 0}')

        checkpoint_config = {"enabled": True, "study_name": "hpo_distilbert_test_v3"}
        hpo_config = {}
        backup_to_drive_mock = MagicMock(return_value=True)

        # Mock is_drive_path to return True for Drive paths
        with patch("common.shared.platform_detection.is_drive_path") as mock_is_drive:
            def is_drive_path_side_effect(path):
                path_str = str(path)
                return path_str.startswith(str(drive_base)) or "/content/drive" in path_str
            
            mock_is_drive.side_effect = is_drive_path_side_effect
            
            # Execute
            backup_hpo_study_to_drive(
                backbone="distilbert",
                backbone_output_dir=backbone_output_dir,
                checkpoint_config=checkpoint_config,
                hpo_config=hpo_config,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
            )

        # Verify: Should not backup file or folder (already in Drive)
        calls = backup_to_drive_mock.call_args_list
        file_backup_calls = [c for c in calls if len(c[0]) > 1 and c[0][1] is False]  # is_directory=False
        dir_backup_calls = [c for c in calls if len(c[0]) > 1 and c[0][1] is True]  # is_directory=True
        # Both should be 0 since everything is already in Drive
        assert len(file_backup_calls) == 0, f"File backup should be skipped. Calls: {file_backup_calls}"
        assert len(dir_backup_calls) == 0, f"Directory backup should be skipped. Calls: {dir_backup_calls}"

    def test_backup_uses_v2_folder_only(self, tmp_path):
        """Test that v2 folder is used directly (no resolve_storage_path calls)."""
        # Setup: Create v2 study folder locally
        backbone_output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = backbone_output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        study_db = study_folder / "study.db"
        study_db.write_text("test database content")
        
        # Create trial folder
        trial_folder = study_folder / "trial-abc123"
        trial_folder.mkdir()
        (trial_folder / "trial_meta.json").write_text('{"trial_number": 0}')

        checkpoint_config = {"enabled": True, "study_name": "hpo_distilbert_test_v3"}
        hpo_config = {}
        backup_to_drive_mock = MagicMock(return_value=True)

        # Mock is_drive_path to return False for local paths
        with patch("common.shared.platform_detection.is_drive_path") as mock_is_drive, \
             patch("training.hpo.checkpoint.storage.resolve_storage_path") as mock_resolve:
            mock_is_drive.return_value = False
            
            # Execute
            backup_hpo_study_to_drive(
                backbone="distilbert",
                backbone_output_dir=backbone_output_dir,
                checkpoint_config=checkpoint_config,
                hpo_config=hpo_config,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
            )

            # Verify: resolve_storage_path should NOT be called (simplified logic, no legacy fallback)
            assert not mock_resolve.called
            # But backup should still happen
            assert backup_to_drive_mock.called

    def test_backup_warns_when_study_folder_not_found(self, tmp_path):
        """Test that backup warns when study folder doesn't exist (no legacy fallback)."""
        # Setup: No v2 folder exists
        backbone_output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        backbone_output_dir.mkdir(parents=True)
        # Note: No study folder created

        checkpoint_config = {"enabled": True, "study_name": "hpo_distilbert_test_v3"}
        hpo_config = {}
        backup_to_drive_mock = MagicMock(return_value=True)

        # Execute
        backup_hpo_study_to_drive(
            backbone="distilbert",
            backbone_output_dir=backbone_output_dir,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
        )

        # Verify: Should not call backup (no study folder found)
        assert not backup_to_drive_mock.called

    def test_backup_checks_file_existence_not_just_path(self, tmp_path):
        """Test that backup checks actual file existence, not just path string."""
        # Setup: Create v2 study folder but NO study.db file
        backbone_output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = backbone_output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        # Note: study.db does NOT exist
        
        # Create trial folder
        trial_folder = study_folder / "trial-abc123"
        trial_folder.mkdir()
        (trial_folder / "trial_meta.json").write_text('{"trial_number": 0}')

        checkpoint_config = {"enabled": True, "study_name": "hpo_distilbert_test_v3"}
        hpo_config = {}
        backup_to_drive_mock = MagicMock(return_value=True)

        # Mock is_drive_path to return False for local paths
        with patch("common.shared.platform_detection.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False
            
            # Execute
            backup_hpo_study_to_drive(
                backbone="distilbert",
                backbone_output_dir=backbone_output_dir,
                checkpoint_config=checkpoint_config,
                hpo_config=hpo_config,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
            )

        # Verify: Should not backup study.db (file doesn't exist)
        calls = backup_to_drive_mock.call_args_list
        file_backup_calls = [c for c in calls if len(c[0]) > 1 and c[0][1] is False]  # is_directory=False
        assert len(file_backup_calls) == 0, f"study.db backup should be skipped when file doesn't exist. Calls: {calls}"


    def test_backup_disabled_skips_all_operations(self, tmp_path):
        """Test that backup is skipped when backup_enabled=False."""
        backbone_output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = backbone_output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        study_db = study_folder / "study.db"
        study_db.write_text("test database content")

        checkpoint_config = {"enabled": True}
        hpo_config = {}
        backup_to_drive_mock = MagicMock(return_value=True)

        # Execute
        backup_hpo_study_to_drive(
            backbone="distilbert",
            backbone_output_dir=backbone_output_dir,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=False,  # Disabled
        )

        # Verify: Should not call backup
        assert not backup_to_drive_mock.called


class TestIncrementalBackupCallback:
    """Test incremental backup callback functionality."""

    def test_create_incremental_backup_callback_file(self, tmp_path):
        """Test incremental backup callback for a file."""
        target_file = tmp_path / "study.db"
        target_file.write_text("test content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        # Create callback
        callback = create_incremental_backup_callback(
            target_path=target_file,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
            is_directory=False,
        )
        
        # Mock Optuna study and trial
        optuna_module = MagicMock()
        optuna_module.trial.TrialState.COMPLETE = "COMPLETE"
        
        study = MagicMock()
        trial = MagicMock()
        trial.state = "COMPLETE"
        trial.number = 0
        
        with patch("orchestration.jobs.hpo.local.backup._import_optuna") as mock_import:
            mock_import.return_value = (optuna_module, None, None, None)
            
            # Execute callback
            callback(study, trial)
        
        # Verify: backup should be called
        assert backup_to_drive_mock.called
        call_args = backup_to_drive_mock.call_args
        assert call_args[0][0] == target_file
        assert call_args.kwargs.get('is_directory') is False  # is_directory=False

    def test_create_incremental_backup_callback_directory(self, tmp_path):
        """Test incremental backup callback for a directory."""
        target_dir = tmp_path / "study_folder"
        target_dir.mkdir()
        (target_dir / "file1.txt").write_text("content1")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        # Create callback
        callback = create_incremental_backup_callback(
            target_path=target_dir,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
            is_directory=True,
        )
        
        # Mock Optuna study and trial
        optuna_module = MagicMock()
        optuna_module.trial.TrialState.COMPLETE = "COMPLETE"
        
        study = MagicMock()
        trial = MagicMock()
        trial.state = "COMPLETE"
        trial.number = 1
        
        with patch("orchestration.jobs.hpo.local.backup._import_optuna") as mock_import:
            mock_import.return_value = (optuna_module, None, None, None)
            
            # Execute callback
            callback(study, trial)
        
        # Verify: backup should be called with is_directory=True
        assert backup_to_drive_mock.called
        call_args = backup_to_drive_mock.call_args
        assert call_args[0][0] == target_dir
        assert call_args.kwargs.get('is_directory') is True  # is_directory=True

    def test_incremental_backup_callback_skips_when_disabled(self, tmp_path):
        """Test that callback does nothing when backup_enabled=False."""
        target_file = tmp_path / "study.db"
        target_file.write_text("test content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        callback = create_incremental_backup_callback(
            target_path=target_file,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=False,  # Disabled
            is_directory=False,
        )
        
        study = MagicMock()
        trial = MagicMock()
        trial.state = "COMPLETE"
        trial.number = 0
        
        # Execute callback
        callback(study, trial)
        
        # Verify: backup should NOT be called
        assert not backup_to_drive_mock.called

    def test_incremental_backup_callback_skips_drive_paths(self, tmp_path):
        """Test that callback skips backup when path is already in Drive."""
        # Use tmp_path but mock it as a Drive path
        drive_path = tmp_path / "study.db"
        drive_path.write_text("test content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        callback = create_incremental_backup_callback(
            target_path=drive_path,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
            is_directory=False,
        )
        
        optuna_module = MagicMock()
        optuna_module.trial.TrialState.COMPLETE = "COMPLETE"
        
        study = MagicMock()
        trial = MagicMock()
        trial.state = "COMPLETE"
        trial.number = 0
        
        with patch("orchestration.jobs.hpo.local.backup._import_optuna") as mock_import, \
             patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_import.return_value = (optuna_module, None, None, None)
            # Mock is_drive_path to return True for this specific path
            def is_drive_side_effect(path):
                return path == drive_path
            mock_is_drive.side_effect = is_drive_side_effect
            
            # Execute callback
            callback(study, trial)
        
        # Verify: backup should NOT be called (path is in Drive)
        assert not backup_to_drive_mock.called

    def test_incremental_backup_callback_skips_nonexistent_path(self, tmp_path):
        """Test that callback skips backup when target path doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.db"
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        callback = create_incremental_backup_callback(
            target_path=nonexistent_file,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
            is_directory=False,
        )
        
        optuna_module = MagicMock()
        optuna_module.trial.TrialState.COMPLETE = "COMPLETE"
        
        study = MagicMock()
        trial = MagicMock()
        trial.state = "COMPLETE"
        trial.number = 0
        
        with patch("orchestration.jobs.hpo.local.backup._import_optuna") as mock_import, \
             patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_import.return_value = (optuna_module, None, None, None)
            mock_is_drive.return_value = False  # Not in Drive
            
            # Execute callback
            callback(study, trial)
        
        # Verify: backup should NOT be called (file doesn't exist)
        assert not backup_to_drive_mock.called

    def test_incremental_backup_callback_skips_non_complete_trials(self, tmp_path):
        """Test that callback only backs up on COMPLETE trials."""
        target_file = tmp_path / "study.db"
        target_file.write_text("test content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        callback = create_incremental_backup_callback(
            target_path=target_file,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
            is_directory=False,
        )
        
        optuna_module = MagicMock()
        optuna_module.trial.TrialState.COMPLETE = "COMPLETE"
        optuna_module.trial.TrialState.FAIL = "FAIL"
        
        study = MagicMock()
        trial = MagicMock()
        trial.state = "FAIL"  # Not COMPLETE
        trial.number = 0
        
        with patch("orchestration.jobs.hpo.local.backup._import_optuna") as mock_import, \
             patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_import.return_value = (optuna_module, None, None, None)
            mock_is_drive.return_value = False
            
            # Execute callback
            callback(study, trial)
        
        # Verify: backup should NOT be called (trial not COMPLETE)
        assert not backup_to_drive_mock.called

    def test_incremental_backup_callback_handles_errors_gracefully(self, tmp_path):
        """Test that callback handles backup errors without crashing."""
        target_file = tmp_path / "study.db"
        target_file.write_text("test content")
        
        backup_to_drive_mock = MagicMock(side_effect=Exception("Backup failed"))
        
        callback = create_incremental_backup_callback(
            target_path=target_file,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
            is_directory=False,
        )
        
        optuna_module = MagicMock()
        optuna_module.trial.TrialState.COMPLETE = "COMPLETE"
        
        study = MagicMock()
        trial = MagicMock()
        trial.state = "COMPLETE"
        trial.number = 0
        
        with patch("orchestration.jobs.hpo.local.backup._import_optuna") as mock_import, \
             patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_import.return_value = (optuna_module, None, None, None)
            mock_is_drive.return_value = False
            
            # Execute callback - should not raise exception
            callback(study, trial)
        
        # Verify: backup was attempted (even though it failed)
        assert backup_to_drive_mock.called

    def test_create_study_db_backup_callback(self, tmp_path):
        """Test convenience wrapper for study.db backup callback."""
        target_file = tmp_path / "study.db"
        target_file.write_text("test content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        # Create callback using convenience wrapper
        callback = create_study_db_backup_callback(
            target_path=target_file,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
        )
        
        optuna_module = MagicMock()
        optuna_module.trial.TrialState.COMPLETE = "COMPLETE"
        
        study = MagicMock()
        trial = MagicMock()
        trial.state = "COMPLETE"
        trial.number = 0
        
        with patch("orchestration.jobs.hpo.local.backup._import_optuna") as mock_import, \
             patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_import.return_value = (optuna_module, None, None, None)
            mock_is_drive.return_value = False
            
            # Execute callback
            callback(study, trial)
        
        # Verify: backup should be called with is_directory=False
        assert backup_to_drive_mock.called
        call_args = backup_to_drive_mock.call_args
        assert call_args[0][0] == target_file
        assert call_args.kwargs.get('is_directory') is False  # is_directory=False (default for study.db)


class TestImmediateBackupIfNeeded:
    """Test immediate_backup_if_needed function."""

    def test_immediate_backup_succeeds_with_enabled_backup_local_path(self, tmp_path):
        """Test that immediate backup succeeds when backup is enabled and path is local."""
        target_file = tmp_path / "checkpoint.tar.gz"
        target_file.write_text("test checkpoint content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False  # Local path
            
            result = immediate_backup_if_needed(
                target_path=target_file,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
                is_directory=False,
            )
        
        # Verify: backup should be called and return True
        assert backup_to_drive_mock.called
        call_args = backup_to_drive_mock.call_args
        assert call_args[0][0] == target_file
        assert call_args.kwargs.get('is_directory') is False
        assert result is True

    def test_immediate_backup_succeeds_with_directory(self, tmp_path):
        """Test that immediate backup succeeds for directories."""
        target_dir = tmp_path / "checkpoint_dir"
        target_dir.mkdir()
        (target_dir / "model.bin").write_text("model content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False  # Local path
            
            result = immediate_backup_if_needed(
                target_path=target_dir,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
                is_directory=True,
            )
        
        # Verify: backup should be called with is_directory=True
        assert backup_to_drive_mock.called
        call_args = backup_to_drive_mock.call_args
        assert call_args[0][0] == target_dir
        assert call_args.kwargs.get('is_directory') is True
        assert result is True

    def test_immediate_backup_skips_when_disabled(self, tmp_path):
        """Test that immediate backup is skipped when backup_enabled=False."""
        target_file = tmp_path / "checkpoint.tar.gz"
        target_file.write_text("test checkpoint content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        result = immediate_backup_if_needed(
            target_path=target_file,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=False,  # Disabled
            is_directory=False,
        )
        
        # Verify: backup should NOT be called
        assert not backup_to_drive_mock.called
        assert result is False

    def test_immediate_backup_skips_when_path_is_drive(self, tmp_path):
        """Test that immediate backup is skipped when path is already in Drive."""
        drive_path = tmp_path / "content" / "drive" / "MyDrive" / "checkpoint.tar.gz"
        drive_path.parent.mkdir(parents=True)
        drive_path.write_text("test checkpoint content")
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            def is_drive_side_effect(path):
                path_str = str(path)
                return "/content/drive" in path_str or path == drive_path
            mock_is_drive.side_effect = is_drive_side_effect
            
            result = immediate_backup_if_needed(
                target_path=drive_path,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
                is_directory=False,
            )
        
        # Verify: backup should NOT be called (path is in Drive)
        assert not backup_to_drive_mock.called
        assert result is False

    def test_immediate_backup_skips_when_path_missing(self, tmp_path):
        """Test that immediate backup is skipped when target path doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.tar.gz"
        
        backup_to_drive_mock = MagicMock(return_value=True)
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False  # Not in Drive
            
            result = immediate_backup_if_needed(
                target_path=nonexistent_file,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
                is_directory=False,
            )
        
        # Verify: backup should NOT be called (file doesn't exist)
        assert not backup_to_drive_mock.called
        assert result is False

    def test_immediate_backup_skips_when_backup_to_drive_is_none(self, tmp_path):
        """Test that immediate backup is skipped when backup_to_drive is None."""
        target_file = tmp_path / "checkpoint.tar.gz"
        target_file.write_text("test checkpoint content")
        
        result = immediate_backup_if_needed(
            target_path=target_file,
            backup_to_drive=None,  # None
            backup_enabled=True,
            is_directory=False,
        )
        
        # Verify: should return False without calling anything
        assert result is False

    def test_immediate_backup_handles_backup_failure_gracefully(self, tmp_path):
        """Test that immediate backup handles backup failures gracefully."""
        target_file = tmp_path / "checkpoint.tar.gz"
        target_file.write_text("test checkpoint content")
        
        backup_to_drive_mock = MagicMock(return_value=False)  # Backup fails
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False  # Local path
            
            result = immediate_backup_if_needed(
                target_path=target_file,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
                is_directory=False,
            )
        
        # Verify: backup was attempted but returned False
        assert backup_to_drive_mock.called
        assert result is False

    def test_immediate_backup_handles_exception_gracefully(self, tmp_path):
        """Test that immediate backup handles exceptions gracefully."""
        target_file = tmp_path / "checkpoint.tar.gz"
        target_file.write_text("test checkpoint content")
        
        backup_to_drive_mock = MagicMock(side_effect=Exception("Backup error"))
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False  # Local path
            
            # Should not raise exception
            result = immediate_backup_if_needed(
                target_path=target_file,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
                is_directory=False,
            )
        
        # Verify: backup was attempted but returned False due to exception
        assert backup_to_drive_mock.called
        assert result is False


class TestShouldSkipBackup:
    """Test _should_skip_backup helper function."""

    def test_should_skip_when_backup_disabled(self, tmp_path):
        """Test that skip returns True when backup_enabled=False."""
        target_file = tmp_path / "file.txt"
        target_file.write_text("content")
        
        result = _should_skip_backup(
            target_path=target_file,
            backup_enabled=False,
        )
        
        assert result is True

    def test_should_skip_when_path_is_drive(self, tmp_path):
        """Test that skip returns True when path is in Drive."""
        drive_path = tmp_path / "content" / "drive" / "MyDrive" / "file.txt"
        drive_path.parent.mkdir(parents=True)
        drive_path.write_text("content")
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            def is_drive_side_effect(path):
                path_str = str(path)
                return "/content/drive" in path_str or path == drive_path
            mock_is_drive.side_effect = is_drive_side_effect
            
            result = _should_skip_backup(
                target_path=drive_path,
                backup_enabled=True,
            )
        
        assert result is True

    def test_should_skip_when_path_missing(self, tmp_path):
        """Test that skip returns True when path doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.txt"
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False  # Not in Drive
            
            result = _should_skip_backup(
                target_path=nonexistent_file,
                backup_enabled=True,
            )
        
        assert result is True

    def test_should_not_skip_when_all_conditions_met(self, tmp_path):
        """Test that skip returns False when all conditions are met for backup."""
        target_file = tmp_path / "file.txt"
        target_file.write_text("content")
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False  # Local path
            
            result = _should_skip_backup(
                target_path=target_file,
                backup_enabled=True,
            )
        
        assert result is False

    def test_should_skip_priority_order(self, tmp_path):
        """Test that skip conditions are checked in correct priority order."""
        # Even if path exists and is local, if backup_enabled=False, should skip
        target_file = tmp_path / "file.txt"
        target_file.write_text("content")
        
        with patch("orchestration.jobs.hpo.local.backup.is_drive_path") as mock_is_drive:
            mock_is_drive.return_value = False  # Local path
            
            result = _should_skip_backup(
                target_path=target_file,
                backup_enabled=False,  # Disabled takes priority
            )
        
        assert result is True

