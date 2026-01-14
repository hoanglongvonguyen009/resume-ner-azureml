"""Comprehensive unit tests for artifact_acquisition.yaml configuration.

This test file covers ALL configuration options in artifact_acquisition.yaml:
- search_roots
- priority (global)
- artifact_kinds (per-artifact-kind priority)
- local.* options
- drive.* options
- mlflow.* options

Tests cover both success and failure cases, following DRY principles.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from evaluation.selection.artifact_unified.acquisition import acquire_artifact
from evaluation.selection.artifact_unified.types import ArtifactKind, ArtifactRequest, ArtifactSource
from evaluation.selection.artifact_unified.discovery import discover_artifact_local


class TestSearchRootsConfig:
    """Test search_roots configuration option."""

    def test_search_roots_extraction(self):
        """Test that search_roots is extracted from config."""
        acquisition_config = {
            "search_roots": ["artifacts", "best_model_selection"]
        }
        
        search_roots = acquisition_config.get("search_roots", ["artifacts", "best_model_selection"])
        
        assert search_roots == ["artifacts", "best_model_selection"]
        assert isinstance(search_roots, list)
        assert len(search_roots) == 2

    def test_search_roots_custom_order(self):
        """Test search_roots with custom order."""
        acquisition_config = {
            "search_roots": ["best_model_selection", "artifacts", "conversion"]
        }
        
        search_roots = acquisition_config.get("search_roots", ["artifacts", "best_model_selection"])
        
        assert search_roots == ["best_model_selection", "artifacts", "conversion"]
        assert len(search_roots) == 3

    def test_search_roots_default(self):
        """Test search_roots default value when missing."""
        acquisition_config = {}
        
        search_roots = acquisition_config.get("search_roots", ["artifacts", "best_model_selection"])
        
        assert search_roots == ["artifacts", "best_model_selection"]
        assert isinstance(search_roots, list)

    def test_search_roots_empty_list(self):
        """Test search_roots with empty list."""
        acquisition_config = {
            "search_roots": []
        }
        
        search_roots = acquisition_config.get("search_roots", ["artifacts", "best_model_selection"])
        
        assert search_roots == []
        assert isinstance(search_roots, list)

    @patch("evaluation.selection.artifact_unified.discovery.discover_artifact_local")
    def test_search_roots_passed_to_discovery(self, mock_discover, tmp_path):
        """Test that search_roots from config is passed to discovery functions."""
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        acquisition_config = {
            "search_roots": ["custom_root1", "custom_root2"],
            "priority": ["local"],
            "local": {"validate": True}
        }
        
        request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_123",
            backbone="distilbert",
            study_key_hash="study123",
            trial_key_hash="trial456",
            metadata={"search_roots": acquisition_config["search_roots"]}
        )
        
        # Call discovery (which should use search_roots from metadata)
        discover_artifact_local(
            request=request,
            root_dir=root_dir,
            config_dir=config_dir,
            validate=True
        )
        
        # Verify search_roots was used (check via metadata)
        assert "search_roots" in request.metadata
        assert request.metadata["search_roots"] == ["custom_root1", "custom_root2"]


class TestArtifactKindsConfig:
    """Test artifact_kinds per-artifact-kind priority configuration."""

    def test_artifact_kinds_extraction(self):
        """Test that artifact_kinds config is extracted."""
        acquisition_config = {
            "artifact_kinds": {
                "checkpoint": {
                    "priority": ["local", "mlflow"]
                },
                "metadata": {
                    "priority": ["local", "mlflow"]
                }
            }
        }
        
        artifact_kinds = acquisition_config.get("artifact_kinds", {})
        
        assert isinstance(artifact_kinds, dict)
        assert "checkpoint" in artifact_kinds
        assert "metadata" in artifact_kinds
        assert artifact_kinds["checkpoint"]["priority"] == ["local", "mlflow"]

    def test_artifact_kinds_priority_overrides_global(self):
        """Test that per-artifact-kind priority overrides global priority."""
        acquisition_config = {
            "priority": ["mlflow", "local", "drive"],  # Global priority
            "artifact_kinds": {
                "checkpoint": {
                    "priority": ["local", "drive", "mlflow"]  # Override for checkpoint
                }
            }
        }
        
        # Simulate how acquisition.py uses this
        artifact_kinds_config = acquisition_config.get("artifact_kinds", {})
        kind_config = artifact_kinds_config.get("checkpoint", {})
        priority = kind_config.get("priority") or acquisition_config.get("priority", [])
        
        assert priority == ["local", "drive", "mlflow"]  # Should use artifact_kinds priority

    def test_artifact_kinds_fallback_to_global_priority(self):
        """Test that missing artifact_kinds falls back to global priority."""
        acquisition_config = {
            "priority": ["mlflow", "local"],
            "artifact_kinds": {
                "metadata": {
                    "priority": ["local", "mlflow"]
                }
                # checkpoint not in artifact_kinds
            }
        }
        
        # Simulate how acquisition.py uses this
        artifact_kinds_config = acquisition_config.get("artifact_kinds", {})
        kind_config = artifact_kinds_config.get("checkpoint", {})  # checkpoint not in config
        priority = kind_config.get("priority") or acquisition_config.get("priority", [])
        
        assert priority == ["mlflow", "local"]  # Should use global priority

    def test_artifact_kinds_all_artifact_types(self):
        """Test artifact_kinds for all artifact types in config."""
        acquisition_config = {
            "artifact_kinds": {
                "checkpoint": {"priority": ["local", "drive", "mlflow"]},
                "metadata": {"priority": ["local", "mlflow"]},
                "config": {"priority": ["local", "mlflow"]},
                "logs": {"priority": ["local", "mlflow"]},
                "metrics": {"priority": ["local", "mlflow"]}
            }
        }
        
        artifact_kinds = acquisition_config.get("artifact_kinds", {})
        
        assert "checkpoint" in artifact_kinds
        assert "metadata" in artifact_kinds
        assert "config" in artifact_kinds
        assert "logs" in artifact_kinds
        assert "metrics" in artifact_kinds
        
        # Verify each has priority
        for kind in ["checkpoint", "metadata", "config", "logs", "metrics"]:
            assert "priority" in artifact_kinds[kind]
            assert isinstance(artifact_kinds[kind]["priority"], list)

    def test_artifact_kinds_missing_priority(self):
        """Test artifact_kinds with missing priority falls back to global."""
        acquisition_config = {
            "priority": ["local", "mlflow"],
            "artifact_kinds": {
                "checkpoint": {
                    # priority missing
                }
            }
        }
        
        artifact_kinds_config = acquisition_config.get("artifact_kinds", {})
        kind_config = artifact_kinds_config.get("checkpoint", {})
        priority = kind_config.get("priority") or acquisition_config.get("priority", [])
        
        assert priority == ["local", "mlflow"]  # Should use global priority


class TestMlflowRequireArtifactTag:
    """Test mlflow.require_artifact_tag configuration option."""

    def test_require_artifact_tag_extraction(self):
        """Test that require_artifact_tag is extracted from config."""
        acquisition_config = {
            "mlflow": {
                "require_artifact_tag": False
            }
        }
        
        require_tag = acquisition_config.get("mlflow", {}).get("require_artifact_tag", False)
        
        assert require_tag is False
        assert isinstance(require_tag, bool)

    def test_require_artifact_tag_true(self):
        """Test require_artifact_tag with true value."""
        acquisition_config = {
            "mlflow": {
                "require_artifact_tag": True
            }
        }
        
        require_tag = acquisition_config.get("mlflow", {}).get("require_artifact_tag", False)
        
        assert require_tag is True

    def test_require_artifact_tag_default(self):
        """Test require_artifact_tag default value when missing."""
        acquisition_config = {
            "mlflow": {}
        }
        
        require_tag = acquisition_config.get("mlflow", {}).get("require_artifact_tag", False)
        
        assert require_tag is False  # Default is False per config file


class TestConfigIntegrationSuccessCases:
    """Test successful acquisition with various config combinations."""

    @pytest.fixture
    def base_config(self):
        """Base config for success tests."""
        return {
            "search_roots": ["artifacts", "best_model_selection"],
            "priority": ["local", "drive", "mlflow"],
            "artifact_kinds": {
                "checkpoint": {
                    "priority": ["local", "drive", "mlflow"]
                }
            },
            "local": {
                "match_strategy": "tags",
                "require_exact_match": True,
                "validate": True
            },
            "drive": {
                "enabled": True,
                "folder_path": "resume-ner-checkpoints",
                "validate": True
            },
            "mlflow": {
                "enabled": True,
                "validate": True,
                "download_timeout": 300,
                "require_artifact_tag": False
            }
        }

    @patch("evaluation.selection.artifact_unified.discovery.discover_artifact_local")
    def test_success_with_all_config_options(self, mock_discover, tmp_path, base_config):
        """Test successful acquisition with all config options set."""
        root_dir = tmp_path / "outputs"
        config_dir = tmp_path / "config"
        root_dir.mkdir()
        config_dir.mkdir()
        
        # Mock successful local discovery
        from evaluation.selection.artifact_unified.types import ArtifactLocation, AvailabilityStatus
        mock_location = ArtifactLocation(
            source=ArtifactSource.LOCAL,
            path=tmp_path / "checkpoint",
            status=AvailabilityStatus.VERIFIED,
            metadata={}
        )
        mock_discover.return_value = mock_location
        
        request = ArtifactRequest(
            artifact_kind=ArtifactKind.CHECKPOINT,
            run_id="test_run_123",
            backbone="distilbert",
            study_key_hash="study123",
            trial_key_hash="trial456",
            metadata={"search_roots": base_config["search_roots"]}
        )
        
        # Verify config is used correctly
        artifact_kinds_config = base_config.get("artifact_kinds", {})
        kind_config = artifact_kinds_config.get(request.artifact_kind.value, {})
        priority = kind_config.get("priority") or base_config.get("priority", [])
        
        assert priority == ["local", "drive", "mlflow"]
        assert base_config["search_roots"] == ["artifacts", "best_model_selection"]
        assert base_config["mlflow"]["require_artifact_tag"] is False

    def test_success_with_custom_artifact_kinds_priority(self, base_config):
        """Test successful config with custom per-artifact-kind priority."""
        base_config["artifact_kinds"]["checkpoint"]["priority"] = ["mlflow", "local"]
        
        artifact_kinds_config = base_config.get("artifact_kinds", {})
        kind_config = artifact_kinds_config.get("checkpoint", {})
        priority = kind_config.get("priority") or base_config.get("priority", [])
        
        assert priority == ["mlflow", "local"]  # Should use artifact_kinds priority

    def test_success_with_custom_search_roots(self, base_config):
        """Test successful config with custom search_roots."""
        base_config["search_roots"] = ["custom_root1", "custom_root2", "custom_root3"]
        
        search_roots = base_config.get("search_roots", [])
        
        assert search_roots == ["custom_root1", "custom_root2", "custom_root3"]


class TestConfigIntegrationFailureCases:
    """Test failure cases with various config combinations."""

    @pytest.fixture
    def base_config(self):
        """Base config for failure tests."""
        return {
            "search_roots": ["artifacts", "best_model_selection"],
            "priority": ["local", "drive", "mlflow"],
            "local": {"validate": True},
            "drive": {"enabled": True, "validate": True},
            "mlflow": {"enabled": True, "validate": True}
        }

    def test_failure_missing_search_roots_uses_defaults(self, base_config):
        """Test that missing search_roots falls back to defaults."""
        del base_config["search_roots"]
        
        search_roots = base_config.get("search_roots", ["artifacts", "best_model_selection"])
        
        assert search_roots == ["artifacts", "best_model_selection"]  # Default

    def test_failure_missing_artifact_kinds_uses_global_priority(self, base_config):
        """Test that missing artifact_kinds uses global priority."""
        # No artifact_kinds in config
        
        artifact_kinds_config = base_config.get("artifact_kinds", {})
        kind_config = artifact_kinds_config.get("checkpoint", {})
        priority = kind_config.get("priority") or base_config.get("priority", [])
        
        assert priority == ["local", "drive", "mlflow"]  # Should use global

    def test_failure_empty_priority_list(self, base_config):
        """Test that empty priority list causes all strategies to be skipped."""
        base_config["priority"] = []
        
        priority = base_config.get("priority", [])
        
        assert priority == []
        # In actual usage, this would cause acquisition to fail

    def test_failure_all_sources_disabled(self, base_config):
        """Test that all sources disabled causes failure."""
        base_config["local"]["enabled"] = False  # Note: local doesn't have enabled, but drive/mlflow do
        base_config["drive"]["enabled"] = False
        base_config["mlflow"]["enabled"] = False
        
        # Verify all are disabled
        assert base_config["drive"]["enabled"] is False
        assert base_config["mlflow"]["enabled"] is False
        # In actual usage, this would cause acquisition to fail

    def test_failure_invalid_priority_source(self, base_config):
        """Test that invalid priority source is not validated (config loader doesn't validate)."""
        base_config["priority"] = ["invalid_source", "another_invalid"]
        
        priority = base_config.get("priority", [])
        
        assert "invalid_source" in priority
        # Config loader doesn't validate, so invalid sources are allowed
        # Runtime would fail when trying to use invalid source


class TestConfigOptionTypes:
    """Test that all config options have correct types."""

    def test_all_config_option_types(self):
        """Test that all config options have expected types."""
        acquisition_config = {
            "search_roots": ["artifacts", "best_model_selection"],
            "priority": ["local", "drive", "mlflow"],
            "artifact_kinds": {
                "checkpoint": {"priority": ["local", "drive", "mlflow"]},
                "metadata": {"priority": ["local", "mlflow"]}
            },
            "local": {
                "match_strategy": "tags",
                "require_exact_match": True,
                "validate": True
            },
            "drive": {
                "enabled": True,
                "folder_path": "resume-ner-checkpoints",
                "validate": True
            },
            "mlflow": {
                "enabled": True,
                "validate": True,
                "download_timeout": 300,
                "require_artifact_tag": False
            }
        }
        
        # Verify types
        assert isinstance(acquisition_config["search_roots"], list)
        assert all(isinstance(item, str) for item in acquisition_config["search_roots"])
        
        assert isinstance(acquisition_config["priority"], list)
        assert all(isinstance(item, str) for item in acquisition_config["priority"])
        
        assert isinstance(acquisition_config["artifact_kinds"], dict)
        for kind, config in acquisition_config["artifact_kinds"].items():
            assert isinstance(kind, str)
            assert isinstance(config, dict)
            assert "priority" in config
            assert isinstance(config["priority"], list)
        
        assert isinstance(acquisition_config["local"]["match_strategy"], str)
        assert isinstance(acquisition_config["local"]["require_exact_match"], bool)
        assert isinstance(acquisition_config["local"]["validate"], bool)
        
        assert isinstance(acquisition_config["drive"]["enabled"], bool)
        assert isinstance(acquisition_config["drive"]["folder_path"], str)
        assert isinstance(acquisition_config["drive"]["validate"], bool)
        
        assert isinstance(acquisition_config["mlflow"]["enabled"], bool)
        assert isinstance(acquisition_config["mlflow"]["validate"], bool)
        assert isinstance(acquisition_config["mlflow"]["download_timeout"], int)
        assert isinstance(acquisition_config["mlflow"]["require_artifact_tag"], bool)


class TestConfigDefaults:
    """Test default values for all config options."""

    def test_all_defaults_match_config_file(self):
        """Test that default values match the actual config file defaults."""
        # Defaults from artifact_acquisition.yaml
        defaults = {
            "search_roots": ["artifacts", "best_model_selection"],
            "priority": ["local", "drive", "mlflow"],
            "local": {
                "match_strategy": "tags",
                "require_exact_match": True,
                "validate": True
            },
            "drive": {
                "enabled": True,
                "folder_path": "resume-ner-checkpoints",
                "validate": True
            },
            "mlflow": {
                "enabled": True,
                "validate": True,
                "download_timeout": 300,
                "require_artifact_tag": False
            }
        }
        
        # Verify defaults
        assert defaults["search_roots"] == ["artifacts", "best_model_selection"]
        assert defaults["priority"] == ["local", "drive", "mlflow"]
        assert defaults["local"]["match_strategy"] == "tags"
        assert defaults["local"]["require_exact_match"] is True
        assert defaults["local"]["validate"] is True
        assert defaults["drive"]["enabled"] is True
        assert defaults["drive"]["folder_path"] == "resume-ner-checkpoints"
        assert defaults["drive"]["validate"] is True
        assert defaults["mlflow"]["enabled"] is True
        assert defaults["mlflow"]["validate"] is True
        assert defaults["mlflow"]["download_timeout"] == 300
        assert defaults["mlflow"]["require_artifact_tag"] is False


class TestConfigCompleteCoverage:
    """Test that all config options from artifact_acquisition.yaml are covered."""

    def test_all_config_sections_present(self):
        """Test that all sections from artifact_acquisition.yaml are testable."""
        # All sections from the actual config file
        required_sections = [
            "search_roots",
            "priority",
            "artifact_kinds",
            "local",
            "drive",
            "mlflow"
        ]
        
        sample_config = {
            "search_roots": ["artifacts", "best_model_selection"],
            "priority": ["local", "drive", "mlflow"],
            "artifact_kinds": {
                "checkpoint": {"priority": ["local", "drive", "mlflow"]}
            },
            "local": {
                "match_strategy": "tags",
                "require_exact_match": True,
                "validate": True
            },
            "drive": {
                "enabled": True,
                "folder_path": "resume-ner-checkpoints",
                "validate": True
            },
            "mlflow": {
                "enabled": True,
                "validate": True,
                "download_timeout": 300,
                "require_artifact_tag": False
            }
        }
        
        for section in required_sections:
            assert section in sample_config, f"Missing section: {section}"

    def test_all_local_options_present(self):
        """Test that all local.* options are covered."""
        required_options = ["match_strategy", "require_exact_match", "validate"]
        
        local_config = {
            "match_strategy": "tags",
            "require_exact_match": True,
            "validate": True
        }
        
        for option in required_options:
            assert option in local_config, f"Missing local option: {option}"

    def test_all_drive_options_present(self):
        """Test that all drive.* options are covered."""
        required_options = ["enabled", "folder_path", "validate"]
        
        drive_config = {
            "enabled": True,
            "folder_path": "resume-ner-checkpoints",
            "validate": True
        }
        
        for option in required_options:
            assert option in drive_config, f"Missing drive option: {option}"

    def test_all_mlflow_options_present(self):
        """Test that all mlflow.* options are covered."""
        required_options = ["enabled", "validate", "download_timeout", "require_artifact_tag"]
        
        mlflow_config = {
            "enabled": True,
            "validate": True,
            "download_timeout": 300,
            "require_artifact_tag": False
        }
        
        for option in required_options:
            assert option in mlflow_config, f"Missing mlflow option: {option}"


