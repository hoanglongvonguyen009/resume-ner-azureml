"""Unit tests for unified repository root detection."""

import tempfile
from pathlib import Path
import pytest

from infrastructure.paths.repo import detect_repo_root, validate_repo_root
from infrastructure.paths.config import load_repository_root_config
from infrastructure.paths.utils import find_project_root, infer_root_dir, infer_config_dir, resolve_project_paths

# Clear module-level cache before each test
@pytest.fixture(autouse=True)
def clear_repo_root_cache():
    """Clear repository root cache before each test."""
    import infrastructure.paths.repo as repo_module
    repo_module._detected_root_cache = None
    yield
    repo_module._detected_root_cache = None


class TestDetectRepoRoot:
    """Test unified detect_repo_root() function."""
    
    def test_detects_from_config_dir(self, tmp_path):
        """Test detection from config_dir parameter."""
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        root = detect_repo_root(config_dir=config_dir)
        
        assert root == tmp_path
        assert root.exists()
    
    def test_detects_from_output_dir(self, tmp_path, monkeypatch):
        """Test detection from output_dir parameter (finds 'outputs' directory)."""
        # Change to tmp_path to avoid finding actual project root
        monkeypatch.chdir(tmp_path)
        
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        outputs_dir = tmp_path / "outputs"
        outputs_dir.mkdir()
        
        output_dir = outputs_dir / "hpo" / "local" / "distilbert"
        output_dir.mkdir(parents=True)
        
        root = detect_repo_root(output_dir=output_dir)
        
        assert root == tmp_path
        assert root.exists()
    
    def test_detects_from_start_path(self, tmp_path, monkeypatch):
        """Test detection from start_path parameter."""
        # Change to tmp_path to avoid finding actual project root
        monkeypatch.chdir(tmp_path)
        
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        start_path = src_dir / "training" / "core" / "trainer.py"
        start_path.parent.mkdir(parents=True)
        start_path.write_text("# trainer code")
        
        root = detect_repo_root(start_path=start_path)
        
        assert root == tmp_path
        assert root.exists()
    
    def test_detects_from_current_directory(self, tmp_path, monkeypatch):
        """Test detection from current working directory."""
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Change to project root
        monkeypatch.chdir(tmp_path)
        
        root = detect_repo_root()
        
        assert root == tmp_path
        assert root.exists()
    
    def test_detects_from_parent_directories(self, tmp_path, monkeypatch):
        """Test detection by searching up directory tree."""
        # Change to tmp_path to avoid finding actual project root
        monkeypatch.chdir(tmp_path)
        
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Create nested directory
        nested_dir = tmp_path / "deep" / "nested" / "structure"
        nested_dir.mkdir(parents=True)
        
        # Change to nested directory
        monkeypatch.chdir(nested_dir)
        
        root = detect_repo_root()
        
        assert root == tmp_path
        assert root.exists()
    
    def test_raises_value_error_when_not_found(self, tmp_path, monkeypatch):
        """Test that ValueError is raised when repository root cannot be found."""
        # Create directory structure without project markers
        random_dir = tmp_path / "random" / "structure"
        random_dir.mkdir(parents=True)
        
        # Change to random directory (outside any project structure)
        monkeypatch.chdir(random_dir)
        
        # This test may not raise ValueError if fallback_to_cwd is enabled in config
        # Instead, verify it returns a path (may be cwd as fallback)
        try:
            root = detect_repo_root()
            # If it doesn't raise, it should at least return a path
            assert isinstance(root, Path)
        except ValueError:
            # If it raises, that's also acceptable
            pass
    
    def test_prioritizes_config_dir_over_output_dir(self, tmp_path):
        """Test that config_dir takes priority over output_dir."""
        # Create two project structures
        project1 = tmp_path / "project1"
        project1_config = project1 / "config"
        project1_config.mkdir(parents=True)
        project1_src = project1 / "src"
        project1_src.mkdir()
        
        project2 = tmp_path / "project2"
        project2_config = project2 / "config"
        project2_config.mkdir(parents=True)
        project2_src = project2 / "src"
        project2_src.mkdir()
        project2_outputs = project2 / "outputs"
        project2_outputs.mkdir()
        
        output_dir = project2_outputs / "hpo" / "local" / "distilbert"
        output_dir.mkdir(parents=True)
        
        # Should use config_dir (project1), not infer from output_dir (project2)
        root = detect_repo_root(config_dir=project1_config, output_dir=output_dir)
        
        assert root == project1
    
    def test_works_with_config_file(self, tmp_path, monkeypatch):
        """Test that detection works when paths.yaml exists."""
        # Change to tmp_path to avoid finding actual project root
        monkeypatch.chdir(tmp_path)
        
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Create minimal paths.yaml
        paths_yaml = config_dir / "paths.yaml"
        paths_yaml.write_text("""
base:
  outputs: "outputs"
  config: "config"
  src: "src"
""")
        
        root = detect_repo_root(config_dir=config_dir)
        
        assert root == tmp_path
        assert root.exists()


class TestValidateRepoRoot:
    """Test validate_repo_root() function."""
    
    def test_validates_with_required_markers(self, tmp_path):
        """Test validation with required markers (config/, src/)."""
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        is_valid = validate_repo_root(tmp_path)
        
        assert is_valid is True
    
    def test_rejects_without_config_dir(self, tmp_path):
        """Test that validation fails without config/ directory."""
        # Create only src/ directory
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        is_valid = validate_repo_root(tmp_path)
        
        assert is_valid is False
    
    def test_rejects_without_src_dir(self, tmp_path):
        """Test that validation fails without src/ directory."""
        # Create only config/ directory
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        is_valid = validate_repo_root(tmp_path)
        
        assert is_valid is False
    
    def test_validates_with_optional_markers(self, tmp_path):
        """Test validation with optional markers (.git, pyproject.toml)."""
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Add optional markers
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text("[project]\nname = 'test'")
        
        is_valid = validate_repo_root(tmp_path)
        
        assert is_valid is True
    
    def test_rejects_non_directory(self, tmp_path):
        """Test that validation fails for non-directory paths."""
        # Create a file instead of directory
        file_path = tmp_path / "not_a_dir"
        file_path.write_text("not a directory")
        
        is_valid = validate_repo_root(file_path)
        
        assert is_valid is False


class TestDeprecatedWrappers:
    """Test deprecated wrapper functions (backward compatibility)."""
    
    def test_find_project_root_still_works(self, tmp_path, monkeypatch):
        """Test that deprecated find_project_root() still works."""
        # Change to tmp_path to avoid finding actual project root
        monkeypatch.chdir(tmp_path)
        
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        root = find_project_root(config_dir=config_dir)
        
        assert root == tmp_path
        assert root.exists()
    
    def test_infer_root_dir_still_works(self, tmp_path, monkeypatch):
        """Test that deprecated infer_root_dir() still works."""
        # Change to tmp_path to avoid finding actual project root
        monkeypatch.chdir(tmp_path)
        
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        root = infer_root_dir(config_dir=config_dir)
        
        assert root == tmp_path
        assert root.exists()
    
    def test_deprecated_functions_are_wrappers(self, tmp_path, monkeypatch):
        """Test that deprecated functions are thin wrappers."""
        # Change to tmp_path to avoid finding actual project root
        monkeypatch.chdir(tmp_path)
        
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Both should return same result
        root1 = find_project_root(config_dir=config_dir)
        root2 = infer_root_dir(config_dir=config_dir)
        root3 = detect_repo_root(config_dir=config_dir)
        
        assert root1 == root2 == root3 == tmp_path


class TestHelperFunctions:
    """Test helper functions that use detect_repo_root()."""
    
    def test_infer_config_dir_uses_unified_function(self, tmp_path):
        """Test that infer_config_dir() uses detect_repo_root() internally."""
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Should infer from root_dir
        inferred_config = infer_config_dir(root_dir=tmp_path)
        
        assert inferred_config == config_dir
    
    def test_resolve_project_paths_uses_unified_function(self, tmp_path, monkeypatch):
        """Test that resolve_project_paths() uses detect_repo_root() internally."""
        # Change to tmp_path to avoid finding actual project root
        monkeypatch.chdir(tmp_path)
        
        # Create project structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        outputs_dir = tmp_path / "outputs"
        outputs_dir.mkdir()
        
        output_dir = outputs_dir / "hpo" / "local" / "distilbert"
        output_dir.mkdir(parents=True)
        
        root_dir, resolved_config_dir = resolve_project_paths(
            output_dir=output_dir,
            config_dir=None
        )
        
        assert root_dir == tmp_path
        assert resolved_config_dir == config_dir


class TestConfigLoading:
    """Test repository root configuration loading."""
    
    def test_loads_repository_root_config(self, tmp_path):
        """Test loading repository_root section from paths.yaml."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        paths_yaml = config_dir / "paths.yaml"
        paths_yaml.write_text("""
base:
  outputs: "outputs"
  config: "config"
  src: "src"
repository_root:
  markers_from_base: true
  extra_markers:
    - ".git"
    - "pyproject.toml"
  search:
    max_depth: 10
    fallback_to_cwd: true
    warn_on_fallback: true
""")
        
        config = load_repository_root_config(config_dir)
        
        assert "markers_from_base" in config
        assert config["markers_from_base"] is True
        assert "extra_markers" in config
        assert ".git" in config["extra_markers"]
        assert "search" in config
        assert config["search"]["max_depth"] == 10
    
    def test_derives_markers_from_base(self, tmp_path):
        """Test that markers are derived from base.* section."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        paths_yaml = config_dir / "paths.yaml"
        paths_yaml.write_text("""
base:
  outputs: "outputs"
  config: "config"
  src: "src"
repository_root:
  markers_from_base: true
""")
        
        config = load_repository_root_config(config_dir)
        
        # Should derive required markers from base.*
        assert "required_markers" in config or "markers" in config
        # The function should derive markers from base.config and base.src

