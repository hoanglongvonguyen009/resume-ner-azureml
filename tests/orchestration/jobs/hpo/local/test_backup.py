"""Unit tests for HPO backup to Drive functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

from orchestration.jobs.hpo.local.backup import backup_hpo_study_to_drive


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

    def test_backup_uses_v2_folder_not_resolve_storage_path(self, tmp_path):
        """Test that v2 folder is used directly, not resolve_storage_path which maps to Drive."""
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

            # Verify: resolve_storage_path should NOT be called when v2 folder exists locally
            assert not mock_resolve.called
            # But backup should still happen
            assert backup_to_drive_mock.called

    def test_backup_falls_back_to_legacy_when_v2_not_found(self, tmp_path):
        """Test that legacy resolve_storage_path is used when v2 folder doesn't exist."""
        # Setup: No v2 folder, only legacy structure
        backbone_output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        backbone_output_dir.mkdir(parents=True)
        
        # Create legacy study folder
        legacy_study_folder = backbone_output_dir / "hpo_distilbert_test_v3"
        legacy_study_folder.mkdir()
        legacy_study_db = legacy_study_folder / "study.db"
        legacy_study_db.write_text("test database content")

        checkpoint_config = {
            "enabled": True,
            "study_name": "hpo_distilbert_test_v3",
            "storage_path": "{backbone}/{study_name}/study.db",
        }
        hpo_config = {}
        backup_to_drive_mock = MagicMock(return_value=True)

        # Mock resolve_storage_path to return legacy path
        with patch("training.hpo.checkpoint.storage.resolve_storage_path") as mock_resolve:
            mock_resolve.return_value = legacy_study_db
            
            # Execute
            backup_hpo_study_to_drive(
                backbone="distilbert",
                backbone_output_dir=backbone_output_dir,
                checkpoint_config=checkpoint_config,
                hpo_config=hpo_config,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
            )

            # Verify: resolve_storage_path should be called as fallback
            assert mock_resolve.called

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

    def test_backup_prioritizes_local_folder_when_study_db_is_local(self, tmp_path):
        """Test that local study folder is used when study.db is local, even if Drive folder exists."""
        # Setup: Create local study folder with study.db
        local_backbone_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        local_study_folder = local_backbone_dir / "study-c3659fea"
        local_study_folder.mkdir(parents=True)
        local_study_db = local_study_folder / "study.db"
        local_study_db.write_text("test database content")
        
        # Create trial folder
        trial_folder = local_study_folder / "trial-abc123"
        trial_folder.mkdir()
        (trial_folder / "trial_meta.json").write_text('{"trial_number": 0}')
        
        # Create Drive study folder (without study.db to simulate it not being backed up yet)
        drive_base = tmp_path / "content" / "drive" / "MyDrive" / "resume-ner-azureml"
        drive_backbone_dir = drive_base / "outputs" / "hpo" / "colab" / "distilbert"
        drive_study_folder = drive_backbone_dir / "study-c3659fea"
        drive_study_folder.mkdir(parents=True)
        # Note: study.db does NOT exist in Drive

        checkpoint_config = {"enabled": True, "study_name": "hpo_distilbert_test_v3"}
        hpo_config = {}
        backup_to_drive_mock = MagicMock(return_value=True)

        # Mock path resolution functions
        with patch("common.shared.platform_detection.is_drive_path") as mock_is_drive, \
             patch("infrastructure.paths.repo.detect_repo_root") as mock_detect_root, \
             patch("infrastructure.paths.get_drive_backup_path") as mock_get_drive:
            
            def is_drive_path_side_effect(path):
                path_str = str(path)
                return path_str.startswith(str(drive_base)) or "/content/drive" in path_str
            
            mock_is_drive.side_effect = is_drive_path_side_effect
            mock_detect_root.return_value = tmp_path
            mock_get_drive.return_value = drive_backbone_dir
            
            # Execute
            backup_hpo_study_to_drive(
                backbone="distilbert",
                backbone_output_dir=local_backbone_dir,
                checkpoint_config=checkpoint_config,
                hpo_config=hpo_config,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
            )

        # Verify: Should backup local study.db and local study folder
        assert backup_to_drive_mock.called
        calls = backup_to_drive_mock.call_args_list
        
        # Should backup study.db file (is_directory=False)
        # Check both positional args and keyword args
        file_backup_calls = [
            c for c in calls 
            if (len(c[0]) >= 2 and c[0][1] is False) or 
               (c.kwargs.get('is_directory') is False) or
               (len(c[0]) == 1 and 'is_directory' in c.kwargs and c.kwargs['is_directory'] is False)
        ]
        assert len(file_backup_calls) > 0, f"study.db should be backed up. All calls: {calls}"
        
        # Verify local study.db was backed up (not Drive path)
        study_db_backed_up = any(
            (len(call[0]) > 0 and (str(call[0][0]) == str(local_study_db) or str(call[0][0]).endswith("study.db"))) or
            (call.kwargs.get('path') == local_study_db if 'path' in call.kwargs else False)
            for call in file_backup_calls
        )
        assert study_db_backed_up, f"Local study.db should be backed up. File calls: {file_backup_calls}"
        
        # Should backup local study folder (is_directory=True)
        dir_backup_calls = [
            c for c in calls 
            if (len(c[0]) >= 2 and c[0][1] is True) or 
               (c.kwargs.get('is_directory') is True) or
               (len(c[0]) == 1 and 'is_directory' in c.kwargs and c.kwargs['is_directory'] is True)
        ]
        assert len(dir_backup_calls) > 0, f"study folder should be backed up. All calls: {calls}"
        
        # Verify local study folder was backed up
        local_folder_backed_up = any(
            (len(call[0]) > 0 and (str(call[0][0]) == str(local_study_folder) or str(call[0][0]).endswith("study-c3659fea"))) or
            (call.kwargs.get('path') == local_study_folder if 'path' in call.kwargs else False)
            for call in dir_backup_calls
        )
        assert local_folder_backed_up, f"Local study folder should be backed up. Dir calls: {dir_backup_calls}"

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

