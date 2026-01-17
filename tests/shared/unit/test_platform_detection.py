"""Unit tests for platform detection utilities."""

from pathlib import Path

import pytest

from common.shared.platform_detection import is_drive_path


class TestIsDrivePath:
    """Test is_drive_path() function."""

    def test_drive_path_string(self):
        """Test Drive path detection with string input."""
        assert is_drive_path("/content/drive/MyDrive/resume-ner-azureml/outputs/hpo/study.db") is True
        assert is_drive_path("/content/drive/MyDrive/test") is True
        assert is_drive_path("/content/drive/") is True

    def test_drive_path_path_object(self):
        """Test Drive path detection with Path object input."""
        assert is_drive_path(Path("/content/drive/MyDrive/resume-ner-azureml/outputs/hpo/study.db")) is True
        assert is_drive_path(Path("/content/drive/MyDrive/test")) is True

    def test_local_path_string(self):
        """Test local path detection with string input."""
        assert is_drive_path("/content/resume-ner-azureml/outputs/hpo/study.db") is False
        assert is_drive_path("/content/test") is False
        assert is_drive_path("/tmp/test") is False

    def test_local_path_path_object(self):
        """Test local path detection with Path object input."""
        assert is_drive_path(Path("/content/resume-ner-azureml/outputs/hpo/study.db")) is False
        assert is_drive_path(Path("/content/test")) is False
        assert is_drive_path(Path("/tmp/test")) is False

    def test_relative_path(self):
        """Test relative path detection (should return False)."""
        assert is_drive_path("outputs/hpo/study.db") is False
        assert is_drive_path(Path("outputs/hpo/study.db")) is False
        assert is_drive_path("./test") is False
        assert is_drive_path("../test") is False

    def test_none_input(self):
        """Test None input raises TypeError."""
        with pytest.raises(TypeError, match="path cannot be None"):
            is_drive_path(None)

