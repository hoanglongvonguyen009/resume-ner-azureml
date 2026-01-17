"""Tests for config directory inference utility.

Tests for the infer_config_dir utility function to ensure
it correctly finds config directories regardless of path depth.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.paths.utils import infer_config_dir


class TestInferConfigDir:
    """Test config directory inference utility."""

    def test_finds_config_in_parent_chain(self, tmp_path: Path):
        """Test that config_dir is found by searching up parent chain."""
        # Create structure: root/config/ and root/src/ (required for repo root validation)
        root = tmp_path / "workspace"
        root.mkdir()
        config_dir = root / "config"
        config_dir.mkdir()
        (config_dir / "tags.yaml").write_text("schema_version: 1")
        src_dir = root / "src"
        src_dir.mkdir()  # Required for repository root validation
        
        # Create deep output structure
        output_dir = root / "outputs" / "hpo" / "local" / "distilbert" / "study-abc" / "trial-xyz"
        output_dir.mkdir(parents=True)
        
        # Should find config_dir at root/config
        result = infer_config_dir(path=output_dir)
        assert result == config_dir
        assert result.exists()

    def test_finds_config_at_root_level(self, tmp_path: Path):
        """Test that config_dir is found at root level."""
        root = tmp_path / "workspace"
        root.mkdir()
        config_dir = root / "config"
        config_dir.mkdir()
        src_dir = root / "src"
        src_dir.mkdir()  # Required for repository root validation
        
        # Simple output structure
        output_dir = root / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        result = infer_config_dir(path=output_dir)
        assert result == config_dir

    def test_falls_back_to_cwd_when_not_found(self, tmp_path: Path, monkeypatch):
        """Test that falls back to cwd/config when config not found in parent chain."""
        # Create output dir without config in parent chain
        output_dir = tmp_path / "outputs" / "hpo"
        output_dir.mkdir(parents=True)
        
        # Create config in cwd with src/ for repo root validation
        cwd_config = tmp_path / "config"
        cwd_config.mkdir()
        (cwd_config / "tags.yaml").write_text("schema_version: 1")
        src_dir = tmp_path / "src"
        src_dir.mkdir()  # Required for repository root validation
        
        # Change to tmp_path as cwd
        monkeypatch.chdir(tmp_path)
        
        result = infer_config_dir(path=output_dir)
        assert result == cwd_config
        assert result.exists()

    def test_handles_none_path(self, tmp_path: Path, monkeypatch):
        """Test that handles None path by falling back to cwd/config."""
        cwd_config = tmp_path / "config"
        cwd_config.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()  # Required for repository root validation
        
        monkeypatch.chdir(tmp_path)
        
        result = infer_config_dir(path=None)
        assert result == Path.cwd() / "config"

    def test_finds_first_config_in_parent_chain(self, tmp_path: Path):
        """Test that finds the first config directory encountered going up the parent chain."""
        root = tmp_path / "workspace"
        root.mkdir()
        
        # Create config at root level
        root_config = root / "config"
        root_config.mkdir()
        src_dir = root / "src"
        src_dir.mkdir()  # Required for repository root validation
        
        # Output dir
        output_dir = root / "outputs" / "hpo" / "local" / "distilbert"
        output_dir.mkdir(parents=True)
        
        # Should find root/config (first config encountered going up from output_dir)
        result = infer_config_dir(path=output_dir)
        assert result == root_config
        assert result.exists()
        
        # If there's a config deeper, it would find that first (but we don't have nested configs in practice)
        # This test verifies it finds root/config correctly

    def test_not_in_outputs_subdirectory(self, tmp_path: Path):
        """Test that config_dir is NOT incorrectly inferred as outputs/config/."""
        root = tmp_path / "workspace"
        root.mkdir()
        
        # Create root/config (correct location)
        root_config = root / "config"
        root_config.mkdir()
        (root_config / "tags.yaml").write_text("schema_version: 1")
        src_dir = root / "src"
        src_dir.mkdir()  # Required for repository root validation
        
        # Ensure outputs/config/ does NOT exist
        outputs_config = root / "outputs" / "config"
        assert not outputs_config.exists(), "outputs/config should not exist for this test"
        
        # Create output structure
        output_dir = root / "outputs" / "hpo" / "local" / "distilbert"
        output_dir.mkdir(parents=True)
        
        result = infer_config_dir(path=output_dir)
        
        # Should be root/config, NOT outputs/config
        assert result == root_config
        assert result.exists()
        
        # Verify it's not in outputs/
        config_path_parts = result.parts
        outputs_index = None
        for i, part in enumerate(config_path_parts):
            if part == "outputs" and i < len(config_path_parts) - 1:
                if i + 1 < len(config_path_parts) and config_path_parts[i + 1] == "config":
                    outputs_index = i
                    break
        
        assert outputs_index is None, \
            f"Config dir should not be in outputs/config/ subdirectory, got {result}"

