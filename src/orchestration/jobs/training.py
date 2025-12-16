from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from azure.ai.ml import Input, command
from azure.ai.ml.entities import Environment


def create_final_training_job(
    script_path: Path,
    data_asset_datastore_path: str,
    environment: Environment,
    compute_cluster: str,
    final_config: Dict[str, Any],
    configs: Dict[str, Any],
    config_metadata: Dict[str, str],
    best_trial_name: str,
    best_value: float,
    aml_experiment_name: str,
    stage: str,
) -> Any:
    """
    Build the final, single-run training job using the best HPO config.

    The resulting command job is responsible for training the production
    model and producing the artefacts (metrics, model files) used for
    deployment or registration.

    Args:
        script_path: Path to the training script within the repo.
        data_asset_datastore_path: Datastore path to the training data.
        environment: Azure ML environment to run the job in.
        compute_cluster: Name of the compute cluster to target.
        final_config: Selected hyperparameter configuration.
        configs: Global configuration mapping (for context only).
        config_metadata: Precomputed configuration metadata for tagging.
        best_trial_name: Identifier of the best sweep trial.
        best_value: Best metric value obtained in the sweep.
        aml_experiment_name: AML experiment name for this stage/backbone.
        stage: Logical experiment stage (e.g. ``training``).

    Returns:
        Configured command job ready for submission.

    Raises:
        FileNotFoundError: If the training script is missing.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Training script not found: {script_path}")

    args = (
        f"--data-asset ${{{{inputs.data}}}} "
        f"--config-dir ../config "
        f"--backbone {final_config['backbone']} "
        f"--learning-rate {final_config['learning_rate']} "
        f"--batch-size {final_config['batch_size']} "
        f"--dropout {final_config['dropout']} "
        f"--weight-decay {final_config['weight_decay']} "
        f"--epochs {final_config['epochs']} "
        f"--random-seed {final_config['random_seed']} "
        f"--early-stopping-enabled {str(final_config['early_stopping_enabled']).lower()} "
        f"--use-combined-data {str(final_config['use_combined_data']).lower()}"
    )

    data_input = Input(type="uri_folder", path=data_asset_datastore_path)

    return command(
        code="../src",
        command=f"python {script_path.name} {args}",
        inputs={"data": data_input},
        environment=environment,
        compute=compute_cluster,
        experiment_name=aml_experiment_name,
        tags={
            **config_metadata,
            "job_type": "final_training",
            "backbone": final_config["backbone"],
            "best_trial": best_trial_name,
            "best_metric_value": str(best_value),
            "stage": stage,
        },
        display_name="final-training",
        description="Final production training with best HPO configuration",
    )


