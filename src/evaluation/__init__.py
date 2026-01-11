"""Model evaluation module.

This module provides functionality for evaluating models, including:
- Benchmarking: Running inference benchmarks on model checkpoints
- Selection: Selecting the best configuration from HPO results
"""

from .benchmarking import (
    benchmark_best_trials,
    benchmark_model,
    compare_models,
    compute_grouping_tags,
    format_results_table,
    run_benchmarking,
)
from .selection import (
    acquire_best_model_checkpoint,
    compute_selection_cache_key,
    extract_cv_statistics,
    extract_best_config_from_study,
    find_best_model_from_mlflow,
    find_best_trials_for_backbones,
    find_study_folder_in_backbone_dir,
    find_trial_hash_info_for_study,
    format_study_summary_line,
    get_trial_hash_info,
    load_benchmark_speed_score,
    load_best_trial_from_disk,
    load_best_trial,
    load_cached_best_model,
    load_study_from_disk,
    MODEL_SPEED_SCORES,
    print_study_summaries,
    save_best_model_cache,
    select_best_configuration,
    select_best_configuration_across_studies,
    select_production_configuration,
    SelectionLogic,
)

__all__ = [
    # Benchmarking exports
    "benchmark_best_trials",
    "benchmark_model",
    "compare_models",
    "compute_grouping_tags",
    "format_results_table",
    "run_benchmarking",
    # Selection exports
    "acquire_best_model_checkpoint",
    "compute_selection_cache_key",
    "extract_cv_statistics",
    "extract_best_config_from_study",
    "find_best_model_from_mlflow",
    "find_best_trials_for_backbones",
    "find_study_folder_in_backbone_dir",
    "find_trial_hash_info_for_study",
    "format_study_summary_line",
    "get_trial_hash_info",
    "load_benchmark_speed_score",
    "load_best_trial_from_disk",
    "load_best_trial",
    "load_cached_best_model",
    "load_study_from_disk",
    "MODEL_SPEED_SCORES",
    "print_study_summaries",
    "save_best_model_cache",
    "select_best_configuration",
    "select_best_configuration_across_studies",
    "select_production_configuration",  # Alias for select_best_configuration
    "SelectionLogic",
]

