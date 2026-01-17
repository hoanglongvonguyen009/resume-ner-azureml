"""Unit tests for HPO helper functions."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

from training.hpo.utils.helpers import setup_checkpoint_storage


class TestSetupCheckpointStorage:
    """Test setup_checkpoint_storage function."""

    def test_uses_v2_folder_when_study_key_hash_provided(self, tmp_path):
        """Test that v2 study folder is used when study_key_hash is provided."""
        # Setup: Create v2 study folder
        output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        study_db = study_folder / "study.db"
        study_db.write_text("test database content")
        
        # Create trial folder to make it a valid v2 study folder
        trial_folder = study_folder / "trial-abc123"
        trial_folder.mkdir()

        checkpoint_config = {"enabled": True}
        study_key_hash = "c3659feaead8e1ec1234567890abcdef"

        # Mock resolve_storage_path to verify it's NOT called for v2 paths
        with patch("training.hpo.checkpoint.storage.resolve_storage_path") as mock_resolve:
            storage_path, storage_uri, should_resume = setup_checkpoint_storage(
                output_dir=output_dir,
                checkpoint_config=checkpoint_config,
                backbone="distilbert",
                study_name="hpo_distilbert_test_v3",
                study_key_hash=study_key_hash,
                restore_from_drive=None,
            )

            # Verify: resolve_storage_path should NOT be called when v2 folder exists
            assert not mock_resolve.called
            # Storage path should be from v2 folder
            assert storage_path == study_db
            assert storage_uri == f"sqlite:///{study_db.resolve()}"
            assert should_resume is True  # File exists

    def test_falls_back_to_resolve_storage_path_when_v2_not_found(self, tmp_path):
        """Test that resolve_storage_path is used when v2 folder doesn't exist."""
        # Setup: No v2 folder
        output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        output_dir.mkdir(parents=True)

        checkpoint_config = {
            "enabled": True,
            "storage_path": "{backbone}/hpo_distilbert_test_v3/study.db",
        }
        study_key_hash = "c3659feaead8e1ec1234567890abcdef"

        # Mock resolve_storage_path to return a path
        expected_path = output_dir / "hpo_distilbert_test_v3" / "study.db"
        expected_path.parent.mkdir(parents=True)
        expected_path.write_text("test database content")

        with patch("training.hpo.checkpoint.storage.resolve_storage_path") as mock_resolve:
            mock_resolve.return_value = expected_path
            
            storage_path, storage_uri, should_resume = setup_checkpoint_storage(
                output_dir=output_dir,
                checkpoint_config=checkpoint_config,
                backbone="distilbert",
                study_name="hpo_distilbert_test_v3",
                study_key_hash=study_key_hash,
                restore_from_drive=None,
            )

            # Verify: resolve_storage_path should be called as fallback
            assert mock_resolve.called
            assert storage_path == expected_path

    def test_restore_from_drive_works_with_v2_path(self, tmp_path):
        """Test that restore_from_drive works correctly with v2 folder paths."""
        # Setup: v2 folder exists but study.db doesn't
        output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        # Note: study.db does NOT exist
        
        # Create trial folder
        trial_folder = study_folder / "trial-abc123"
        trial_folder.mkdir()

        checkpoint_config = {"enabled": True}
        study_key_hash = "c3659feaead8e1ec1234567890abcdef"
        
        # Mock restore function
        restore_mock = MagicMock(return_value=True)

        storage_path, storage_uri, should_resume = setup_checkpoint_storage(
            output_dir=output_dir,
            checkpoint_config=checkpoint_config,
            backbone="distilbert",
            study_name="hpo_distilbert_test_v3",
            study_key_hash=study_key_hash,
            restore_from_drive=restore_mock,
        )

        # Verify: restore should be called with local path (v2 folder path)
        assert restore_mock.called
        assert storage_path == study_folder / "study.db"
        # Path should be local (not Drive path)
        assert not str(storage_path).startswith("/content/drive")
        assert should_resume is False  # File doesn't exist yet

    def test_restore_skips_when_path_is_in_drive(self, tmp_path):
        """Test that restore is skipped when path is already in Drive."""
        # Setup: Create path in Drive location
        drive_path = tmp_path / "content" / "drive" / "MyDrive" / "resume-ner-azureml" / "outputs" / "hpo" / "colab" / "distilbert" / "hpo_distilbert_test_v3" / "study.db"
        output_dir = tmp_path / "content" / "drive" / "MyDrive" / "resume-ner-azureml" / "outputs" / "hpo" / "colab" / "distilbert"
        output_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_config = {
            "enabled": True,
            "storage_path": "{backbone}/hpo_distilbert_test_v3/study.db",
        }

        # Mock resolve_storage_path to return Drive path
        drive_path.parent.mkdir(parents=True, exist_ok=True)
        # Note: study.db does NOT exist

        # Mock is_drive_path to return True for this path (since tmp_path doesn't start with /content/drive)
        with patch("training.hpo.checkpoint.storage.resolve_storage_path") as mock_resolve, \
             patch("training.hpo.utils.helpers.is_drive_path") as mock_is_drive:
            mock_resolve.return_value = drive_path
            # Make is_drive_path return True for the drive_path
            def is_drive_side_effect(path):
                return path == drive_path or str(path) == str(drive_path)
            mock_is_drive.side_effect = is_drive_side_effect
            
            restore_mock = MagicMock(return_value=True)
            
            storage_path, storage_uri, should_resume = setup_checkpoint_storage(
                output_dir=output_dir,
                checkpoint_config=checkpoint_config,
                backbone="distilbert",
                study_name="hpo_distilbert_test_v3",
                study_key_hash=None,  # No v2 hash, will use resolve_storage_path
                restore_from_drive=restore_mock,
            )

            # Verify: restore should NOT be called (path is in Drive)
            assert not restore_mock.called
            assert storage_path == drive_path

    def test_should_resume_when_file_exists(self, tmp_path):
        """Test that should_resume is True when study.db exists."""
        # Setup: Create v2 study folder with study.db
        output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        study_db = study_folder / "study.db"
        study_db.write_text("test database content")
        
        # Create trial folder
        trial_folder = study_folder / "trial-abc123"
        trial_folder.mkdir()

        checkpoint_config = {"enabled": True, "auto_resume": True}
        study_key_hash = "c3659feaead8e1ec1234567890abcdef"

        storage_path, storage_uri, should_resume = setup_checkpoint_storage(
            output_dir=output_dir,
            checkpoint_config=checkpoint_config,
            backbone="distilbert",
            study_name="hpo_distilbert_test_v3",
            study_key_hash=study_key_hash,
            restore_from_drive=None,
        )

        # Verify: should_resume should be True
        assert should_resume is True
        assert storage_path == study_db

    def test_should_not_resume_when_file_missing(self, tmp_path):
        """Test that should_resume is False when study.db doesn't exist."""
        # Setup: Create v2 study folder but NO study.db
        output_dir = tmp_path / "outputs" / "hpo" / "colab" / "distilbert"
        study_folder = output_dir / "study-c3659fea"
        study_folder.mkdir(parents=True)
        # Note: study.db does NOT exist
        
        # Create trial folder
        trial_folder = study_folder / "trial-abc123"
        trial_folder.mkdir()

        checkpoint_config = {"enabled": True, "auto_resume": True}
        study_key_hash = "c3659feaead8e1ec1234567890abcdef"

        storage_path, storage_uri, should_resume = setup_checkpoint_storage(
            output_dir=output_dir,
            checkpoint_config=checkpoint_config,
            backbone="distilbert",
            study_name="hpo_distilbert_test_v3",
            study_key_hash=study_key_hash,
            restore_from_drive=None,
        )

        # Verify: should_resume should be False
        assert should_resume is False
        assert storage_path == study_folder / "study.db"

