from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from azure.ai.ml import Input, MLClient, Output, command
from azure.ai.ml.entities import Environment, Job


def get_checkpoint_output_from_training_job(
    training_job: Job, ml_client: Optional[MLClient] = None
) -> Any:
    """Extract checkpoint output reference from a completed training job.

    Azure ML auto-registers job outputs as data assets. We prefer using the
    actual output reference (which may be a data asset URI like
    ``azureml:azureml_<job_name>_output_data_checkpoint:1``) over constructing
    datastore URIs manually, as it's more reliable and handles edge cases.

    Args:
        training_job: Completed training job with checkpoint output.
        ml_client: Optional MLClient to fetch data asset if output URI is not available.

    Returns:
        Checkpoint output reference (URI string, data asset reference, or Job object).

    Raises:
        ValueError: If training job has no checkpoint output or did not complete successfully.
    """
    # Validate that the training job completed successfully
    if training_job.status != "Completed":
        raise ValueError(
            f"Training job {training_job.name} did not complete successfully. "
            f"Status: {training_job.status}. Cannot use checkpoint output from failed job."
        )
    
    # First, try to extract URI/path from the job's outputs (works if job was just created)
    # This is checked first because it doesn't require ml_client
    if hasattr(training_job, "outputs") and training_job.outputs:
        checkpoint_output = training_job.outputs.get("checkpoint")
        if checkpoint_output is not None:
            # Prefer .uri (data asset reference) over .path (legacy)
            if hasattr(checkpoint_output, "uri") and checkpoint_output.uri:
                return checkpoint_output.uri
            elif hasattr(checkpoint_output, "path") and checkpoint_output.path:
                return checkpoint_output.path
            # If output exists but has no URI/path, we'll need ml_client below
    
    # If job outputs don't have URI/path (e.g., when reloading from cache), we need to
    # construct or fetch the auto-registered data asset. Azure ML auto-registers job outputs
    # as data assets with the pattern: azureml_<job_name>_output_data_<output_name>:1
    
    # Construct the expected data asset name
    data_asset_name = f"azureml_{training_job.name}_output_data_checkpoint"
    
    if ml_client is not None:
        # Try to fetch the data asset to verify it exists and get the exact reference
        try:
            data_asset = ml_client.data.get(name=data_asset_name, version="1")
            # Return the data asset reference in the format Azure ML expects
            asset_ref = f"azureml:{data_asset.name}:{data_asset.version}"
            return asset_ref
        except Exception as e:
            # If fetching fails, construct the reference directly (less reliable but works)
            import warnings
            warnings.warn(
                f"Could not fetch data asset '{data_asset_name}' for training job '{training_job.name}': {e}. "
                "Constructing data asset reference directly. This may cause issues if the asset doesn't exist."
            )
            # Fall through to direct construction
    else:
        # ml_client not provided - construct the data asset reference directly
        # This is less reliable but allows the function to work without ml_client
        import warnings
        warnings.warn(
            f"ml_client not provided for training job '{training_job.name}'. "
            "Constructing data asset reference directly. For best results, provide ml_client."
        )
    
    # Construct the data asset reference directly (works if the asset exists)
    # Azure ML auto-registers with version "1" for the first output
    asset_ref = f"azureml:{data_asset_name}:1"
    return asset_ref


def _get_job_output_reference(
    job: Job,
    output_name: str,
    ml_client: Optional[MLClient] = None,
) -> str:
    """Resolve an Azure ML job output to a stable reference usable as an Input/Model path."""
    if hasattr(job, "outputs") and job.outputs and output_name in job.outputs:
        out = job.outputs[output_name]
        uri = getattr(out, "uri", None)
        if uri:
            return str(uri)
        path = getattr(out, "path", None)
        if path:
            return str(path)

    # Prefer the auto-registered data asset reference (stable even across reloads)
    data_asset_name = f"azureml_{job.name}_output_data_{output_name}"
    if ml_client is not None:
        try:
            data_asset = ml_client.data.get(name=data_asset_name, version="1")
            return f"azureml:{data_asset.name}:{data_asset.version}"
        except Exception:
            pass

    return f"azureml:{data_asset_name}:1"


def create_conversion_job(
    script_path: Path,
    checkpoint_output: Any,
    environment: Environment,
    compute_cluster: str,
    configs: Dict[str, Any],
    config_metadata: Dict[str, str],
    best_config: Dict[str, Any],
    final_training_job: Job,
    ml_client: Optional[MLClient] = None,
) -> Any:
    """Create Azure ML Command Job for model conversion to ONNX with int8 quantization.

    The conversion step reuses the training environment and consumes the
    checkpoint artefact produced by the final training job.

    Args:
        script_path: Path to conversion script.
        checkpoint_output: Checkpoint output from training job.
        environment: Azure ML environment to run the job in.
        compute_cluster: CPU compute cluster name.
        configs: Global configuration mapping (for context only).
        config_metadata: Precomputed configuration metadata for tagging.
        best_config: Best configuration from HPO selection.
        final_training_job: Completed final training job (for tagging).
        ml_client: Optional MLClient for fetching data assets if needed.

    Returns:
        Configured command job ready for submission.

    Raises:
        FileNotFoundError: If conversion script does not exist.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Conversion script not found: {script_path}")

    # Normalise checkpoint output into an Input the command job can consume.
    #
    # Azure ML auto-registers job outputs as data assets (e.g.,
    # ``azureml:azureml_<job_name>_output_data_checkpoint:1``). We prefer using
    # the actual output reference when available, as it's more reliable than
    # constructing datastore URIs manually.
    #
    # The training script saves checkpoints to `AZURE_ML_OUTPUT_checkpoint/checkpoint/`,
    # so the actual checkpoint files are at the root of the mounted data asset
    # under a `checkpoint/` subdirectory. The conversion script will search
    # for files in both the root and nested `checkpoint/` subdirectory.
    if isinstance(checkpoint_output, (str, Path)):
        # Direct URI/path string (e.g., data asset reference like "azureml:...")
        checkpoint_path = str(checkpoint_output)
        # Ensure it's a valid data asset reference format
        if checkpoint_path.startswith("azureml:"):
            # This is a data asset reference - use it directly
            pass
        elif checkpoint_path.startswith("azureml://"):
            # This is a datastore URI - use it directly
            pass
        else:
            # If it's not a recognized format, try to construct a data asset reference
            # This shouldn't happen if get_checkpoint_output_from_training_job works correctly
            raise ValueError(
                f"Unexpected checkpoint path format: {checkpoint_path}. "
                "Expected a data asset reference (azureml:...) or datastore URI (azureml://...)."
            )
    elif isinstance(checkpoint_output, Job):
        # Fallback: construct datastore URI from job name
        # This is used when the job output doesn't expose a URI/path
        storage_cfg = configs.get("env", {}).get("storage", {})
        datastore = (
            storage_cfg.get("output_datastore")
            or storage_cfg.get("workspace_datastore")
            or "workspaceblobstore"
        )
        checkpoint_path = (
            f"azureml://datastores/{datastore}/paths/"
            f"azureml/ExperimentRun/dcid.{checkpoint_output.name}/outputs/checkpoint"
        )
    else:
        raise ValueError(
            f"Unsupported checkpoint_output type: {type(checkpoint_output)}. "
            "Expected a URI/path string (e.g., data asset reference) or the completed training Job object."
        )

    # Validate that we're using the correct checkpoint path from the training job
    if isinstance(checkpoint_output, str) and checkpoint_output.startswith("azureml:"):
        # Verify the data asset reference matches the training job name
        expected_asset_name = f"azureml_{final_training_job.name}_output_data_checkpoint"
        if expected_asset_name not in checkpoint_path:
            import warnings
            warnings.warn(
                f"Checkpoint path '{checkpoint_path}' does not match expected pattern "
                f"for training job '{final_training_job.name}'. "
                f"Expected asset name to contain '{expected_asset_name}'."
            )
    
    checkpoint_input = Input(type="uri_folder", path=checkpoint_path)

    command_args = (
        f"--checkpoint-path ${{{{inputs.checkpoint}}}} "
        f"--config-dir config "
        f"--backbone {best_config['backbone']} "
        f"--output-dir ${{{{outputs.onnx_model}}}} "
        f"--quantize-int8 "
        f"--run-smoke-test"
    )

    # Use project root as code snapshot so both `src/` and `config/` are included.
    return command(
        code="..",
        command=f"python src/{script_path.name} {command_args}",
        inputs={
            "checkpoint": checkpoint_input,
        },
        outputs={
            "onnx_model": Output(type="uri_folder"),
        },
        environment=environment,
        compute=compute_cluster,
        experiment_name=configs["env"]["logging"]["experiment_name"],
        tags={
            **config_metadata,
            "job_type": "model_conversion",
            "backbone": best_config["backbone"],
            "source_training_job": final_training_job.name,
            "quantization": "int8",
        },
        display_name="model-conversion",
        description="Convert PyTorch checkpoint to optimized ONNX model (int8 quantized)",
    )


def validate_conversion_job(job: Job, ml_client: Optional[MLClient] = None) -> None:
    """Validate conversion job completed successfully with required ONNX model output.

    Args:
        job: Completed job instance
        ml_client: Optional MLClient to resolve the output reference when SDK doesn't populate it.

    Raises:
        ValueError: If validation fails
    """
    if job.status != "Completed":
        raise ValueError(f"Conversion job failed with status: {job.status}")

    if not hasattr(job, "outputs") or not job.outputs:
        raise ValueError("Conversion job produced no outputs")

    if "onnx_model" not in job.outputs:
        raise ValueError("Conversion job missing required output: onnx_model")

    onnx_ref = _get_job_output_reference(job, "onnx_model", ml_client=ml_client)
    if not onnx_ref or not (onnx_ref.startswith("azureml:") or onnx_ref.startswith("azureml://")):
        raise ValueError(f"Invalid ONNX model output reference: {onnx_ref}")


