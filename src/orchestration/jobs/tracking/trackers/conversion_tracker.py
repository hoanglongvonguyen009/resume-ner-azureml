"""MLflow tracker for conversion stage."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional, List
import time
import tempfile
import json
import sys
import os
import re

import mlflow
from shared.logging_utils import get_logger

from orchestration.jobs.tracking.mlflow_types import RunHandle
from orchestration.jobs.tracking.mlflow_naming import build_mlflow_tags, build_mlflow_run_key, build_mlflow_run_key_hash
from orchestration.jobs.tracking.mlflow_index import update_mlflow_index
from orchestration.jobs.tracking.utils.mlflow_utils import get_mlflow_run_url, retry_with_backoff
from orchestration.jobs.tracking.artifacts.manager import create_checkpoint_archive
from orchestration.jobs.tracking.trackers.base_tracker import BaseTracker

logger = get_logger(__name__)


class MLflowConversionTracker(BaseTracker):
    """Tracks MLflow runs for model conversion stage."""

    def __init__(self, experiment_name: str):
        """
        Initialize tracker.

        Args:
            experiment_name: MLflow experiment name.
        """
        super().__init__(experiment_name)

    @contextmanager
    def start_conversion_run(
        self,
        run_name: str,
        conversion_type: str,
        source_training_run: Optional[str] = None,
        context: Optional[Any] = None,
        output_dir: Optional[Path] = None,
        parent_run_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ):
        """
        Start a MLflow run for model conversion.
        """
        try:
            with mlflow.start_run(run_name=run_name) as conversion_run:
                run_id = conversion_run.info.run_id
                experiment_id = conversion_run.info.experiment_id
                tracking_uri = mlflow.get_tracking_uri()

                # Infer config_dir from output_dir
                config_dir = None
                if output_dir:
                    if output_dir.parent.name == "outputs":
                        root_dir_for_config = output_dir.parent.parent
                    else:
                        root_dir_for_config = output_dir.parent.parent.parent
                    config_dir = root_dir_for_config / "config"

                tags = build_mlflow_tags(
                    context=context,
                    output_dir=output_dir,
                    parent_run_id=parent_run_id or source_training_run,
                    group_id=group_id,
                    config_dir=config_dir,
                )
                tags["conversion_type"] = conversion_type
                tags["mlflow.runType"] = "conversion"
                if source_training_run:
                    tags["source_training_run"] = source_training_run
                mlflow.set_tags(tags)

                run_key = build_mlflow_run_key(context) if context else None
                run_key_hash = (
                    build_mlflow_run_key_hash(run_key) if run_key else None
                )

                handle = RunHandle(
                    run_id=run_id,
                    run_key=run_key or "",
                    run_key_hash=run_key_hash or "",
                    experiment_id=experiment_id,
                    experiment_name=self.experiment_name,
                    tracking_uri=tracking_uri,
                    artifact_uri=conversion_run.info.artifact_uri,
                )

                if run_key_hash:
                    try:
                        root_dir = (
                            output_dir.parent.parent if output_dir else Path.cwd()
                        )
                        update_mlflow_index(
                            root_dir=root_dir,
                            run_key_hash=run_key_hash,
                            run_id=run_id,
                            experiment_id=experiment_id,
                            tracking_uri=tracking_uri,
                            config_dir=config_dir,
                        )
                    except Exception as e:
                        logger.debug(f"Could not update MLflow index: {e}")

                yield handle
        except Exception as e:
            logger.warning(f"MLflow tracking failed: {e}")
            logger.warning("Continuing conversion without MLflow tracking...")
            from contextlib import nullcontext
            with nullcontext():
                yield None

    def log_conversion_parameters(
        self,
        checkpoint_path: str,
        conversion_target: str,
        quantization: str,
        opset_version: int,
        backbone: str,
    ) -> None:
        try:
            mlflow.log_param("conversion_source", checkpoint_path)
            mlflow.log_param("conversion_target", conversion_target)
            mlflow.log_param("quantization", quantization)
            mlflow.log_param("onnx_opset_version", opset_version)
            mlflow.log_param("conversion_backbone", backbone)
        except Exception as e:
            logger.warning(
                f"Could not log conversion parameters to MLflow: {e}"
            )

    def log_conversion_results(
        self,
        conversion_success: bool,
        onnx_model_path: Optional[Path],
        original_checkpoint_size: Optional[float] = None,
        smoke_test_passed: Optional[bool] = None,
        conversion_log_path: Optional[Path] = None,
    ) -> None:
        try:
            mlflow.log_metric(
                "conversion_success",
                1 if conversion_success else 0,
            )

            if onnx_model_path and onnx_model_path.exists():
                model_size_mb = onnx_model_path.stat().st_size / (1024 * 1024)
                mlflow.log_metric("onnx_model_size_mb", model_size_mb)

                if original_checkpoint_size:
                    compression_ratio = (
                        original_checkpoint_size / model_size_mb
                    )
                    mlflow.log_metric(
                        "compression_ratio", compression_ratio
                    )

            if smoke_test_passed is not None:
                mlflow.log_metric(
                    "smoke_test_passed",
                    1 if smoke_test_passed else 0,
                )

            # Use MLflow for artifact upload (works for both Azure ML and non-Azure ML backends)
            if onnx_model_path and onnx_model_path.exists():
                artifact_name = onnx_model_path.name
                max_retries = 3
                retry_delay = 2

                for attempt in range(max_retries):
                    try:
                        mlflow.log_artifact(
                            str(onnx_model_path),
                            artifact_path=artifact_name,
                        )
                        break
                    except Exception as upload_err:
                        if attempt < max_retries - 1:
                            time.sleep(
                                retry_delay * (2 ** attempt)
                            )
                        else:
                            logger.warning(
                                f"Failed to upload {artifact_name} after "
                                f"{max_retries} attempts: {upload_err}"
                            )

            if conversion_log_path and conversion_log_path.exists():
                max_retries = 3
                retry_delay = 2

                for attempt in range(max_retries):
                    try:
                        mlflow.log_artifact(
                            str(conversion_log_path),
                            artifact_path="conversion_log.txt",
                        )
                        break
                    except Exception as upload_err:
                        if attempt < max_retries - 1:
                            time.sleep(
                                retry_delay * (2 ** attempt)
                            )
                        else:
                            logger.warning(
                                "Failed to upload conversion_log.txt after "
                                f"{max_retries} attempts: {upload_err}"
                            )
        except Exception as e:
            logger.warning(
                f"Could not log conversion results to MLflow: {e}"
            )
