"""Lineage tag setting utilities for final training."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import mlflow
from mlflow.tracking import MlflowClient

from orchestration.jobs.tracking.finder.run_finder import find_mlflow_run


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
    1. Finds the MLflow run using find_mlflow_run()
    2. Sets code.trained_on_full_data = "true"
    3. Sets code.lineage.source = "hpo_best_selected"
    4. Sets code.lineage.hpo_* tags if available in lineage dict
    
    Errors are caught and logged but do not raise exceptions.
    """
    run_id: Optional[str] = None
    
    try:
        # First, try the run finder
        report = find_mlflow_run(
            experiment_name=experiment_name,
            context=context,
            output_dir=output_dir,
            strict=False,
            root_dir=root_dir,
            config_dir=config_dir,
        )
        
        if report.found and report.run_id:
            run_id = report.run_id
        else:
            # Fallback: Query MLflow directly for the most recent run in the experiment
            # This is useful when the run was created in a subprocess and metadata isn't available yet
            try:
                client = MlflowClient()
                experiment = client.get_experiment_by_name(experiment_name)
                if experiment:
                    # Search for the most recent run in the experiment
                    runs = client.search_runs(
                        experiment_ids=[experiment.experiment_id],
                        max_results=1,
                        order_by=["start_time DESC"]
                    )
                    if runs:
                        run_id = runs[0].info.run_id
                        print(f"✓ Found MLflow run via direct query: {run_id[:12]}...")
            except Exception as e:
                print(f"⚠ Could not query MLflow for recent run: {e}")
        
        if run_id:
            with mlflow.start_run(run_id=run_id):
                # Set training-specific tags
                mlflow.set_tag("code.trained_on_full_data", "true")
                
                # Set lineage tags (following benchmark tracker pattern)
                lineage_tags = {
                    "code.lineage.source": "hpo_best_selected",
                }
                
                # Add HPO lineage tags if available
                if lineage.get("hpo_study_key_hash"):
                    lineage_tags["code.lineage.hpo_study_key_hash"] = lineage["hpo_study_key_hash"]
                if lineage.get("hpo_trial_key_hash"):
                    lineage_tags["code.lineage.hpo_trial_key_hash"] = lineage["hpo_trial_key_hash"]
                if lineage.get("hpo_trial_run_id"):
                    lineage_tags["code.lineage.hpo_trial_run_id"] = lineage["hpo_trial_run_id"]
                if lineage.get("hpo_refit_run_id"):
                    lineage_tags["code.lineage.hpo_refit_run_id"] = lineage["hpo_refit_run_id"]
                if lineage.get("hpo_sweep_run_id"):
                    lineage_tags["code.lineage.hpo_sweep_run_id"] = lineage["hpo_sweep_run_id"]
                
                # Set all lineage tags at once
                if len(lineage_tags) > 1:  # More than just "source"
                    mlflow.set_tags(lineage_tags)
                    print(f"✓ Set lineage tags in MLflow run {run_id[:12]}...")
                    print(f"   Lineage: {list(lineage_tags.keys())}")
                else:
                    print(f"✓ Set code.trained_on_full_data tag in MLflow run {run_id[:12]}...")
        else:
            print("⚠ Could not find MLflow run to apply lineage tags")
                    
    except Exception as e:
        print(f"⚠ Could not set MLflow tags: {e}")
        import traceback
        traceback.print_exc()

