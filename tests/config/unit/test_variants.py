"""Unit tests for variants utility (variants.py).

Tests the generalized variant computation for both final_training and hpo.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from infrastructure.config.variants import (
    compute_next_variant,
    find_existing_variants,
)


class TestComputeNextVariant:
    """Test compute_next_variant() function."""

    def test_compute_next_variant_hpo_no_existing(self, tmp_path):
        """Test HPO variant computation when no variants exist."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        variant = compute_next_variant(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert variant == 1

    def test_compute_next_variant_hpo_with_existing(self, tmp_path):
        """Test HPO variant computation when variants exist."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create existing variant folders
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert").mkdir()  # Variant 1 (implicit)
        (hpo_output / "hpo_distilbert_v2").mkdir()  # Variant 2
        
        variant = compute_next_variant(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert variant == 3

    def test_compute_next_variant_hpo_custom_base_name(self, tmp_path):
        """Test HPO variant computation with custom base name."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create existing variant folders
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert_prod").mkdir()  # Variant 1
        (hpo_output / "hpo_distilbert_prod_v2").mkdir()  # Variant 2
        
        variant = compute_next_variant(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert_prod",
        )
        assert variant == 3

    def test_compute_next_variant_final_training_no_existing(self, tmp_path):
        """Test final_training variant computation when no variants exist."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        with patch("infrastructure.config.variants._find_final_training_variants") as mock_find:
            mock_find.return_value = []
            
            variant = compute_next_variant(
                root_dir=tmp_path,
                config_dir=config_dir,
                process_type="final_training",
                model="distilbert",
                spec_fp="spec123",
                exec_fp="exec456",
            )
            assert variant == 1

    def test_compute_next_variant_final_training_with_existing(self, tmp_path):
        """Test final_training variant computation when variants exist."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        with patch("infrastructure.config.variants._find_final_training_variants") as mock_find:
            mock_find.return_value = [1, 2, 3]
            
            variant = compute_next_variant(
                root_dir=tmp_path,
                config_dir=config_dir,
                process_type="final_training",
                model="distilbert",
                spec_fp="spec123",
                exec_fp="exec456",
            )
            assert variant == 4


class TestFindExistingVariants:
    """Test find_existing_variants() function."""

    def test_find_existing_variants_hpo_none(self, tmp_path):
        """Test finding HPO variants when none exist."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        variants = find_existing_variants(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert variants == []

    def test_find_existing_variants_hpo_implicit_variant_1(self, tmp_path):
        """Test finding HPO variants with implicit variant 1."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create HPO output structure
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert").mkdir()  # Variant 1 (implicit)
        
        variants = find_existing_variants(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert variants == [1]

    def test_find_existing_variants_hpo_explicit_variants(self, tmp_path):
        """Test finding HPO variants with explicit variant suffixes."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create HPO output structure
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert").mkdir()  # Variant 1
        (hpo_output / "hpo_distilbert_v2").mkdir()  # Variant 2
        (hpo_output / "hpo_distilbert_v3").mkdir()  # Variant 3
        
        variants = find_existing_variants(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert sorted(variants) == [1, 2, 3]

    def test_find_existing_variants_hpo_mixed_patterns(self, tmp_path):
        """Test finding HPO variants with mixed folder patterns."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create HPO output structure with mixed patterns
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        (hpo_output / "hpo_distilbert").mkdir()  # Variant 1
        (hpo_output / "hpo_distilbert_v2").mkdir()  # Variant 2
        (hpo_output / "study-abc123").mkdir()  # v2 folder (should be ignored)
        (hpo_output / "other_folder").mkdir()  # Unrelated folder
        
        variants = find_existing_variants(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert sorted(variants) == [1, 2]

    def test_find_existing_variants_final_training(self, tmp_path):
        """Test finding final_training variants."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        with patch("infrastructure.config.variants._find_final_training_variants") as mock_find:
            mock_find.return_value = [1, 2]
            
            variants = find_existing_variants(
                root_dir=tmp_path,
                config_dir=config_dir,
                process_type="final_training",
                model="distilbert",
                spec_fp="spec123",
                exec_fp="exec456",
            )
            assert variants == [1, 2]

    def test_find_existing_variants_invalid_process_type(self, tmp_path):
        """Test finding variants for invalid process type."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        variants = find_existing_variants(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="invalid_type",
            model="distilbert",
        )
        assert variants == []


class TestVariantsIntegration:
    """Integration tests for variant computation."""

    def test_hpo_variant_sequence(self, tmp_path):
        """Test HPO variant sequence generation."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        
        # First variant
        variant1 = compute_next_variant(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert variant1 == 1
        
        # Create variant 1 folder
        (hpo_output / "hpo_distilbert").mkdir()
        
        # Second variant
        variant2 = compute_next_variant(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert variant2 == 2
        
        # Create variant 2 folder
        (hpo_output / "hpo_distilbert_v2").mkdir()
        
        # Third variant
        variant3 = compute_next_variant(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name="hpo_distilbert",
        )
        assert variant3 == 3

    def test_hpo_variant_with_custom_study_name(self, tmp_path):
        """Test HPO variant computation with custom study_name template."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        hpo_output = tmp_path / "outputs" / "hpo" / "local" / "distilbert"
        hpo_output.mkdir(parents=True)
        
        base_name = "hpo_distilbert_smoke_test"
        
        # Create existing variants
        (hpo_output / base_name).mkdir()  # Variant 1
        (hpo_output / f"{base_name}_v2").mkdir()  # Variant 2
        
        variant = compute_next_variant(
            root_dir=tmp_path,
            config_dir=config_dir,
            process_type="hpo",
            model="distilbert",
            base_name=base_name,
        )
        assert variant == 3


