"""Tests for semantic_suffix behavior in HPO sweep run names.

Verifies that auto-generated study names (study_name: null) result in empty
semantic_suffix to avoid redundancy in run names.
"""

import pytest
from infrastructure.naming import create_naming_context
from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
from pathlib import Path


class TestSemanticSuffixBehavior:
    """Test semantic_suffix extraction and sanitization."""

    def test_auto_generated_study_name_returns_empty_semantic_suffix(self, tmp_path):
        """Test that auto-generated study_name (None) results in empty semantic_suffix."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create naming.yaml with hpo_sweep pattern
        naming_yaml = config_dir / "naming.yaml"
        naming_yaml.write_text("""schema_version: 1
run_names:
  hpo_sweep:
    pattern: "{env}_{model}_hpo_study-{study_hash}{semantic_suffix}{version}"
    components:
      study_hash:
        length: 8
        source: "study_key_hash"
        default: "unknown"
      semantic_suffix:
        enabled: true
        max_length: 30
        source: "study_name"
        default: ""
version:
  format: "{separator}{number}"
  separator: "_"
""")
        
        # Create context with study_name=None (auto-generated default)
        context = create_naming_context(
            process_type="hpo",
            model="distilbert",
            environment="local",
            stage="hpo_sweep",
            study_name=None,  # Auto-generated default
            study_key_hash="584922ce12345678",
        )
        
        run_name = build_mlflow_run_name(context, config_dir, root_dir=tmp_path)
        
        # Should be: local_distilbert_hpo_study-584922ce_1 (no redundant _distilbert)
        assert run_name.startswith("local_distilbert_hpo_study-584922ce")
        assert "_distilbert" not in run_name.split("study-")[1]  # No redundant distilbert after study hash

    def test_custom_study_name_includes_semantic_suffix(self, tmp_path):
        """Test that custom study_name results in semantic_suffix."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create naming.yaml
        naming_yaml = config_dir / "naming.yaml"
        naming_yaml.write_text("""schema_version: 1
run_names:
  hpo_sweep:
    pattern: "{env}_{model}_hpo_study-{study_hash}{semantic_suffix}{version}"
    components:
      study_hash:
        length: 8
        source: "study_key_hash"
        default: "unknown"
      semantic_suffix:
        enabled: true
        max_length: 30
        source: "study_name"
        default: ""
version:
  format: "{separator}{number}"
  separator: "_"
""")
        
        # Create context with custom study_name
        context = create_naming_context(
            process_type="hpo",
            model="distilbert",
            environment="local",
            stage="hpo_sweep",
            study_name="hpo_distilbert_smoke_test",  # Custom study name
            study_key_hash="584922ce12345678",
        )
        
        run_name = build_mlflow_run_name(context, config_dir, root_dir=tmp_path)
        
        # Should include semantic suffix: local_distilbert_hpo_study-584922ce_smoke_test_1
        assert "smoke_test" in run_name
        assert run_name.startswith("local_distilbert_hpo_study-584922ce")

    def test_auto_generated_with_variant_returns_empty_semantic_suffix(self, tmp_path):
        """Test that auto-generated study_name with variant (hpo_distilbert_v2) also returns empty."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        naming_yaml = config_dir / "naming.yaml"
        naming_yaml.write_text("""schema_version: 1
run_names:
  hpo_sweep:
    pattern: "{env}_{model}_hpo_study-{study_hash}{semantic_suffix}{version}"
    components:
      study_hash:
        length: 8
        source: "study_key_hash"
        default: "unknown"
      semantic_suffix:
        enabled: true
        max_length: 30
        source: "study_name"
        default: ""
version:
  format: "{separator}{number}"
  separator: "_"
""")
        
        # Even if study_name is "hpo_distilbert_v2" (variant), it's still auto-generated
        # and should result in empty semantic_suffix
        # Note: setup_hpo_mlflow_run detects this pattern and passes None
        context = create_naming_context(
            process_type="hpo",
            model="distilbert",
            environment="local",
            stage="hpo_sweep",
            study_name=None,  # setup_hpo_mlflow_run converts "hpo_distilbert_v2" to None
            study_key_hash="584922ce12345678",
        )
        
        run_name = build_mlflow_run_name(context, config_dir, root_dir=tmp_path)
        
        # Should be: local_distilbert_hpo_study-584922ce_1 (no redundant suffix)
        assert run_name.startswith("local_distilbert_hpo_study-584922ce")
        assert "_distilbert" not in run_name.split("study-")[1]

