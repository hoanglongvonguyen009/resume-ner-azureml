"""Unit tests for study summary functionality.

Tests verify that print_study_summaries correctly handles multiple backbones
and prevents the indentation bug where only the last backbone's study was stored.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from evaluation.selection.study_summary import (
    print_study_summaries,
    format_study_summary_line,
    extract_cv_statistics,
)


@pytest.fixture
def mock_study():
    """Create a mock Optuna study with trials."""
    study = Mock()
    study.trials = []
    
    # Create mock trials
    for i in range(2):
        trial = Mock()
        trial.number = i
        trial.value = 0.4 + (i * 0.05)  # 0.4, 0.45
        trial.user_attrs = {
            "cv_mean": 0.4 + (i * 0.05),
            "cv_std": 0.01 + (i * 0.01),  # 0.01, 0.02
        }
        study.trials.append(trial)
    
    # Set best trial
    study.best_trial = study.trials[1]  # Trial 1 with value 0.45
    
    return study


@pytest.fixture
def mock_hpo_studies(mock_study):
    """Create mock hpo_studies dict with multiple backbones."""
    return {
        "distilbert": mock_study,
        "distilroberta": mock_study,
    }


@pytest.fixture
def hpo_config():
    """Sample HPO config."""
    return {
        "objective": {"metric": "macro-f1", "goal": "maximize"},
    }


@pytest.fixture
def tmp_root_dir(tmp_path):
    """Create temporary root directory structure."""
    return tmp_path


class TestStudySummaryMultipleBackbones:
    """Test that study summaries work correctly with multiple backbones."""

    def test_print_study_summaries_with_multiple_backbones(
        self, mock_hpo_studies, hpo_config, tmp_root_dir, capsys
    ):
        """Test that print_study_summaries processes all backbones in hpo_studies."""
        backbone_values = ["distilbert", "distilroberta"]
        
        with patch("evaluation.selection.study_summary.find_trial_hash_info_for_study") as mock_find_hash:
            mock_find_hash.return_value = ("abc12345", "def67890", 0)
            
            print_study_summaries(
                hpo_studies=mock_hpo_studies,
                backbone_values=backbone_values,
                hpo_config=hpo_config,
                root_dir=tmp_root_dir,
                environment="local",
            )
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify both backbones are in output
        assert "distilbert" in output
        assert "distilroberta" in output
        assert output.count("trials") == 2  # Should have 2 study summaries

    def test_print_study_summaries_with_missing_from_dict(
        self, mock_study, hpo_config, tmp_root_dir, capsys
    ):
        """Test that print_study_summaries loads missing backbones from disk."""
        # Only distilbert in hpo_studies, but distilroberta in backbone_values
        hpo_studies = {"distilbert": mock_study}
        backbone_values = ["distilbert", "distilroberta"]
        
        with patch("evaluation.selection.study_summary.find_trial_hash_info_for_study") as mock_find_hash, \
             patch("evaluation.selection.study_summary.load_study_from_disk") as mock_load:
            mock_find_hash.return_value = ("abc12345", "def67890", 0)
            mock_load.return_value = mock_study  # Return study for distilroberta
            
            print_study_summaries(
                hpo_studies=hpo_studies,
                backbone_values=backbone_values,
                hpo_config=hpo_config,
                root_dir=tmp_root_dir,
                environment="local",
            )
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify both backbones are in output
        assert "distilbert" in output
        assert "distilroberta" in output
        # Should have called load_study_from_disk for distilroberta
        mock_load.assert_called_once()

    def test_print_study_summaries_skips_already_printed(
        self, mock_hpo_studies, hpo_config, tmp_root_dir, capsys
    ):
        """Test that print_study_summaries doesn't duplicate already printed backbones."""
        backbone_values = ["distilbert", "distilroberta"]
        
        with patch("evaluation.selection.study_summary.find_trial_hash_info_for_study") as mock_find_hash, \
             patch("evaluation.selection.study_summary.load_study_from_disk") as mock_load:
            mock_find_hash.return_value = ("abc12345", "def67890", 0)
            
            print_study_summaries(
                hpo_studies=mock_hpo_studies,
                backbone_values=backbone_values,
                hpo_config=hpo_config,
                root_dir=tmp_root_dir,
                environment="local",
            )
        
        # Should not call load_study_from_disk since all are in hpo_studies
        mock_load.assert_not_called()
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify each backbone appears only once
        assert output.count("distilbert") == 1  # Only in summary line
        assert output.count("distilroberta") == 1

    def test_format_study_summary_line_with_cv_stats(self):
        """Test format_study_summary_line includes CV statistics when available."""
        line = format_study_summary_line(
            backbone="distilbert",
            num_trials=2,
            best_metric_value=0.4206,
            objective_metric="macro-f1",
            study_key_hash="abc12345",
            trial_key_hash="def67890",
            trial_number=0,
            cv_stats=(0.4206, 0.0054),
        )
        
        assert "distilbert" in line
        assert "2 trials" in line
        assert "macro-f1=0.4206" in line
        assert "study-abc12345" in line
        assert "trial-def67890" in line
        assert "CV: 0.4206" in line
        assert "0.0054" in line

    def test_format_study_summary_line_without_cv_stats(self):
        """Test format_study_summary_line works without CV statistics."""
        line = format_study_summary_line(
            backbone="distilbert",
            num_trials=2,
            best_metric_value=0.4206,
            objective_metric="macro-f1",
            study_key_hash="abc12345",
            trial_key_hash="def67890",
            trial_number=0,
            cv_stats=None,
        )
        
        assert "distilbert" in line
        assert "2 trials" in line
        assert "macro-f1=0.4206" in line
        assert "CV:" not in line  # Should not have CV line

    def test_extract_cv_statistics(self, mock_study):
        """Test extract_cv_statistics extracts CV stats from trial user_attrs."""
        best_trial = mock_study.best_trial
        cv_stats = extract_cv_statistics(best_trial)
        
        assert cv_stats is not None
        assert cv_stats == (0.45, 0.02)  # cv_mean, cv_std from best trial

    def test_extract_cv_statistics_missing(self):
        """Test extract_cv_statistics returns None when CV stats are missing."""
        trial = Mock()
        trial.user_attrs = {}
        
        cv_stats = extract_cv_statistics(trial)
        assert cv_stats is None

