from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from azure.ai.ml import Input, command, MLClient
from azure.ai.ml.entities import Environment, Data, Job
from azure.ai.ml.sweep import (
    SweepJob,
    Objective,
    SweepJobLimits,
    Choice,
    Uniform,
    LogUniform,
)


def create_search_space(hpo_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate a config-defined search space into Azure ML sweep primitives.

    The input is expected to follow the standard HPO YAML structure used in
    this project, where each parameter entry specifies a ``type`` and
    associated bounds or values.

    Args:
        hpo_config: Configuration dictionary containing a ``search_space`` key.

    Returns:
        Dictionary mapping parameter names to Azure ML search distributions.
    """
    search_space: Dict[str, Any] = {}
    for name, spec in hpo_config["search_space"].items():
        p_type = spec["type"]
        if p_type == "choice":
            search_space[name] = Choice(values=spec["values"])
        elif p_type == "uniform":
            search_space[name] = Uniform(
                min_value=float(spec["min"]),
                max_value=float(spec["max"]),
            )
        elif p_type == "loguniform":
            search_space[name] = LogUniform(
                min_value=float(spec["min"]),
                max_value=float(spec["max"]),
            )
    return search_space


def _build_data_input_from_asset(data_asset: Data) -> Input:
    """
    Build a standard Azure ML ``Input`` for a ``uri_folder`` data asset.

    Args:
        data_asset: Registered Azure ML data asset.

    Returns:
        Input pointing at the asset, mounted as a folder.
    """
    return Input(
        type="uri_folder",
        path=f"azureml:{data_asset.name}:{data_asset.version}",
        mode="mount",
    )


def create_dry_run_sweep_job_for_backbone(
    script_path: Path,
    data_asset: Data,
    environment: Environment,
    compute_cluster: str,
    backbone: str,
    smoke_hpo_config: Dict[str, Any],
    configs: Dict[str, Any],
    config_metadata: Dict[str, str],
    aml_experiment_name: str,
    stage: str,
) -> SweepJob:
    """
    Build a small HPO sweep job used as a smoke test for a backbone.

    The dry run uses a reduced search space (no backbone dimension and
    fewer trials) to validate that data access, training, and metrics
    wiring all function correctly before launching the full HPO sweep.

    Args:
        script_path: Path to the training script within the repo.
        data_asset: Registered data asset providing training data.
        environment: Azure ML environment to run the sweep in.
        compute_cluster: Name of the compute cluster to target.
        backbone: Backbone identifier (e.g. ``distilbert``).
        smoke_hpo_config: Parsed smoke HPO configuration.
        configs: Global configuration mapping (for context only).
        config_metadata: Precomputed configuration metadata for tagging.
        aml_experiment_name: AML experiment name for this stage/backbone.
        stage: Logical experiment stage (e.g. ``smoke``).

    Returns:
        Configured :class:`SweepJob` ready for submission.

    Raises:
        FileNotFoundError: If the training script is missing.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Training script not found: {script_path}")

    reduced = {
        "search_space": {
            k: v for k, v in smoke_hpo_config["search_space"].items() if k != "backbone"
        }
    }
    search_space = create_search_space(reduced)

    trials = max(2, smoke_hpo_config["sampling"]["max_trials"] // 2)

    cmd_args = (
        f"--data-asset ${{{{inputs.data}}}} "
        f"--config-dir config "
        f"--backbone {backbone} "
        f"--learning-rate ${{{{search_space.learning_rate}}}} "
        f"--batch-size ${{{{search_space.batch_size}}}} "
        f"--dropout ${{{{search_space.dropout}}}} "
        f"--weight-decay ${{{{search_space.weight_decay}}}}"
    )

    data_input = _build_data_input_from_asset(data_asset)

    trial_job = command(
        code="..",
        command=f"python src/{script_path.name} {cmd_args}",
        inputs={"data": data_input},
        environment=environment,
        compute=compute_cluster,
    )

    objective = Objective(
        goal=smoke_hpo_config["objective"]["goal"],
        primary_metric=smoke_hpo_config["objective"]["metric"],
    )
    timeout_seconds = smoke_hpo_config["sampling"]["timeout_minutes"] * 60
    limits = SweepJobLimits(max_total_trials=trials, timeout=timeout_seconds)

    return SweepJob(
        trial=trial_job,
        search_space=search_space,
        sampling_algorithm=smoke_hpo_config["sampling"]["algorithm"],
        objective=objective,
        limits=limits,
        inputs={"data": data_input},
        experiment_name=aml_experiment_name,
        tags={
            **config_metadata,
            "job_type": "dry_run_sweep",
            "backbone": backbone,
            "stage": stage,
        },
        display_name=f"dry-run-sweep-{backbone}",
        description=f"Dry run sweep for {backbone}",
    )


def create_hpo_sweep_job_for_backbone(
    script_path: Path,
    data_asset: Data,
    environment: Environment,
    compute_cluster: str,
    hpo_config: Dict[str, Any],
    backbone: str,
    configs: Dict[str, Any],
    config_metadata: Dict[str, str],
    aml_experiment_name: str,
    stage: str,
) -> SweepJob:
    """
    Build a production HPO sweep job for a specific backbone model.

    The production sweep typically uses a richer search space and more
    trials than the dry run, and is the primary source for selecting the
    best configuration.

    Args:
        script_path: Path to the training script within the repo.
        data_asset: Registered data asset providing training data.
        environment: Azure ML environment to run the sweep in.
        compute_cluster: Name of the compute cluster to target.
        hpo_config: Parsed HPO configuration.
        backbone: Backbone identifier (e.g. ``distilbert``).
        configs: Global configuration mapping (for context only).
        config_metadata: Precomputed configuration metadata for tagging.
        aml_experiment_name: AML experiment name for this stage/backbone.
        stage: Logical experiment stage (e.g. ``hpo``).

    Returns:
        Configured :class:`SweepJob` ready for submission.

    Raises:
        FileNotFoundError: If the training script is missing.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Training script not found: {script_path}")

    reduced = {
        "search_space": {
            k: v for k, v in hpo_config["search_space"].items() if k != "backbone"
        }
    }
    search_space = create_search_space(reduced)

    cmd_args = (
        f"--data-asset ${{{{inputs.data}}}} "
        f"--config-dir config "
        f"--backbone {backbone} "
        f"--learning-rate ${{{{search_space.learning_rate}}}} "
        f"--batch-size ${{{{search_space.batch_size}}}} "
        f"--dropout ${{{{search_space.dropout}}}} "
        f"--weight-decay ${{{{search_space.weight_decay}}}}"
    )

    data_input = _build_data_input_from_asset(data_asset)
    trial_job = command(
        code="..",
        command=f"python src/{script_path.name} {cmd_args}",
        inputs={"data": data_input},
        environment=environment,
        compute=compute_cluster,
    )

    objective = Objective(
        goal=hpo_config["objective"]["goal"],
        primary_metric=hpo_config["objective"]["metric"],
    )
    timeout_seconds = hpo_config["sampling"]["timeout_minutes"] * 60
    limits = SweepJobLimits(
        max_total_trials=hpo_config["sampling"]["max_trials"],
        timeout=timeout_seconds,
    )

    early_termination = None
    if "early_termination" in hpo_config:
        from azure.ai.ml.sweep import BanditPolicy

        et_cfg = hpo_config["early_termination"]
        if et_cfg.get("policy") == "bandit":
            early_termination = BanditPolicy(
                evaluation_interval=et_cfg["evaluation_interval"],
                slack_factor=et_cfg["slack_factor"],
                delay_evaluation=et_cfg["delay_evaluation"],
            )

    return SweepJob(
        trial=trial_job,
        search_space=search_space,
        sampling_algorithm=hpo_config["sampling"]["algorithm"],
        objective=objective,
        limits=limits,
        early_termination=early_termination,
        compute=compute_cluster,
        inputs={"data": data_input},
        experiment_name=aml_experiment_name,
        tags={
            **config_metadata,
            "job_type": "hpo_sweep",
            "backbone": backbone,
            "stage": stage,
        },
        display_name=f"hpo-sweep-{backbone}",
        description=f"Production HPO sweep for {backbone}",
    )


def validate_dry_run_sweep_job(ml_client: MLClient, job: Job, backbone: str) -> None:
    """
    Validate dry run sweep job completed successfully.
    Falls back to counting child runs if trial_count is missing/zero.
    
    Args:
        ml_client: Azure ML client used for job operations.
        job: Completed sweep job instance
        backbone: Backbone model name for error messages
        
    Raises:
        ValueError: If validation fails
    """
    if job.status != "Completed":
        raise ValueError(f"Dry run sweep job for {backbone} failed with status: {job.status}")

    child_count = None
    try:
        children = list(ml_client.jobs.list(parent_job_name=job.name))
        child_count = len(children)
    except Exception:
        child_count = None

    if hasattr(job, "trial_count") and job.trial_count and job.trial_count > 0:
        return
    if child_count is not None and child_count > 0:
        return

    raise ValueError(
        f"Dry run sweep job for {backbone} produced no trials (parent run: {job.name}). "
        f"Check sweep logs and child runs in portal."
    )


def validate_hpo_sweep_job(job: Job, backbone: str, min_expected_trials: int = 5) -> None:
    """
    Validate HPO sweep job completed successfully with sufficient trials.
    
    Args:
        job: Completed sweep job instance
        backbone: Backbone model name for error messages
        min_expected_trials: Minimum number of trials expected (default: 5)
        
    Raises:
        ValueError: If validation fails
    """
    if job.status != "Completed":
        raise ValueError(f"HPO sweep job for {backbone} failed with status: {job.status}")
    
    if not hasattr(job, "trial_count") or job.trial_count == 0:
        raise ValueError(f"HPO sweep job for {backbone} produced no trials")
    
    if job.trial_count < min_expected_trials:
        raise ValueError(
            f"HPO sweep job for {backbone} only produced {job.trial_count} trial(s), "
            f"expected at least {min_expected_trials}"
        )


