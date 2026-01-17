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

        # Execute
        backup_hpo_study_to_drive(
            backbone="distilbert",
            backbone_output_dir=backbone_output_dir,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
        )

        # Verify: study.db should be backed up
        assert backup_to_drive_mock.called
        # Should be called with study.db file (not directory)
        calls = backup_to_drive_mock.call_args_list
        file_backup_calls = [c for c in calls if c[0][1] is False]  # is_directory=False
        assert len(file_backup_calls) > 0
        assert file_backup_calls[0][0][0] == study_db

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

        # Execute
        backup_hpo_study_to_drive(
            backbone="distilbert",
            backbone_output_dir=backbone_output_dir,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
        )

        # Verify: Should not backup file (already in Drive)
        # Only directory backup might be called, but not file backup
        calls = backup_to_drive_mock.call_args_list
        file_backup_calls = [c for c in calls if c[0][1] is False]  # is_directory=False
        assert len(file_backup_calls) == 0

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

        # Mock resolve_storage_path to verify it's NOT called for v2 paths
        with patch("training.hpo.checkpoint.storage.resolve_storage_path") as mock_resolve:
            # Execute
            backup_hpo_study_to_drive(
                backbone="distilbert",
                backbone_output_dir=backbone_output_dir,
                checkpoint_config=checkpoint_config,
                hpo_config=hpo_config,
                backup_to_drive=backup_to_drive_mock,
                backup_enabled=True,
            )

            # Verify: resolve_storage_path should NOT be called when v2 folder exists
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

        # Execute
        backup_hpo_study_to_drive(
            backbone="distilbert",
            backbone_output_dir=backbone_output_dir,
            checkpoint_config=checkpoint_config,
            hpo_config=hpo_config,
            backup_to_drive=backup_to_drive_mock,
            backup_enabled=True,
        )

        # Verify: Should not backup (file doesn't exist)
        calls = backup_to_drive_mock.call_args_list
        file_backup_calls = [c for c in calls if c[0][1] is False]  # is_directory=False
        assert len(file_backup_calls) == 0

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

