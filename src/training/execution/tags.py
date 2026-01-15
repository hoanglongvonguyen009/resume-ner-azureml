from __future__ import annotations

"""
@meta
name: tags
type: utility
domain: training
responsibility:
  - Apply lineage tags to final training MLflow runs
  - Link final training runs back to HPO origins
inputs:
  - MLflow experiment name
  - Naming context
  - Lineage dictionary
outputs:
  - Tagged MLflow runs
tags:
  - utility
  - training
  - mlflow
  - tags
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Lineage tag setting utilities for final training."""

from pathlib import Path
from typing import Any, Dict

import mlflow

from infrastructure.tracking.mlflow.finder import find_mlflow_run
from training.execution.tag_helpers import _build_lineage_tags_dict


def apply_lineage_tags(
    experiment_name: str,
    context: Any,
    output_dir: Path,
    root_dir: Path,
    config_dir: Path,
    lineage: Dict[str, Any],
) -> None:
    """
    Apply lineage tags to final training MLflow run.
    
    Sets training-specific and lineage tags on the MLflow run created during
    final training. This links the final training run back to its HPO origins
    using the code.lineage.* namespace (following benchmark_tracker.py pattern).
    
    **Note**: This function uses `infrastructure.tracking.mlflow.finder.find_mlflow_run()`
    (SSOT) for run finding. The finder handles all fallback strategies including
    finding the most recent run (potentially RUNNING) when `strict=False`.
    
    Args:
        experiment_name: MLflow experiment name for the training run.
        context: NamingContext used to find the MLflow run.
        output_dir: Output directory of the training run.
        root_dir: Project root directory.
        config_dir: Config directory.
        lineage: Lineage dictionary from extract_lineage_from_best_model().
                 Expected keys:
                 - hpo_study_key_hash (optional)
                 - hpo_trial_key_hash (optional)
                 - hpo_trial_run_id (optional)
                 - hpo_refit_run_id (optional)
                 - hpo_sweep_run_id (optional)
    
    The function:
    1. Finds the MLflow run using find_mlflow_run() (SSOT) with strict=False to allow fallbacks
    2. Sets code.trained_on_full_data = "true"
    3. Sets code.lineage.source = "hpo_best_selected"
    4. Sets code.lineage.hpo_* tags if available in lineage dict
    
    Errors are caught and logged but do not raise exceptions.
    """
    try:
        # Use SSOT finder (handles all fallback strategies including most recent run)
        report = find_mlflow_run(
            experiment_name=experiment_name,
            context=context,
            output_dir=output_dir,
            strict=False,  # Allow fallbacks including most recent run (priority 7)
            root_dir=root_dir,
            config_dir=config_dir,
        )
        
        if not report.found or not report.run_id:
            print("⚠ Could not find MLflow run to apply lineage tags")
            return
        
        run_id = report.run_id
        
        # Get training-specific tag keys using consolidated helper (SSOT)
        from training.execution.tag_helpers import _get_training_tag_keys
        
        tag_keys = _get_training_tag_keys(config_dir)
        trained_on_full_data_tag = tag_keys["trained_on_full_data"]

        # Build lineage tags using shared helper (SSOT)
        lineage_tags = _build_lineage_tags_dict(lineage, config_dir)

        with mlflow.start_run(run_id=run_id):
            # Set training-specific tags
            mlflow.set_tag(trained_on_full_data_tag, "true")

            # Set lineage tags if any are present
            if lineage_tags:
                mlflow.set_tags(lineage_tags)
                print(f"✓ Set lineage tags in MLflow run {run_id[:12]}...")
                print(f"   Lineage: {list(lineage_tags.keys())}")
            else:
                print(f"✓ Set code.trained_on_full_data tag in MLflow run {run_id[:12]}...")
                    
    except Exception as e:
        print(f"⚠ Could not set MLflow tags: {e}")
        import traceback
        traceback.print_exc()

