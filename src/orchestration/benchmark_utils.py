"""Benchmarking utility functions for running inference benchmarks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.logging_utils import get_logger

logger = get_logger(__name__)


def run_benchmarking(
    checkpoint_dir: Path,
    test_data_path: Path,
    output_path: Path,
    batch_sizes: List[int],
    iterations: int,
    warmup_iterations: int,
    max_length: int = 512,
    device: Optional[str] = None,
    benchmark_script_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
    tracker: Optional[Any] = None,
    backbone: Optional[str] = None,
    benchmark_source: str = "final_training",
) -> bool:
    """
    Run benchmarking on a model checkpoint.

    Args:
        checkpoint_dir: Path to checkpoint directory.
        test_data_path: Path to test data JSON file.
        output_path: Path to output benchmark.json file.
        batch_sizes: List of batch sizes to test.
        iterations: Number of iterations per batch size.
        warmup_iterations: Number of warmup iterations.
        max_length: Maximum sequence length.
        device: Device to use (None = auto-detect).
        benchmark_script_path: Path to benchmark script. If None, will try to find
            it at benchmarks/benchmark_inference.py relative to project_root.
        project_root: Project root directory. Required if benchmark_script_path is None.
        tracker: Optional MLflowBenchmarkTracker instance for logging results.
        backbone: Optional model backbone name for tracking.
        benchmark_source: Source of benchmark ("hpo_trial" or "final_training").

    Returns:
        True if successful, False otherwise.
    """
    # Determine benchmark script path
    if benchmark_script_path is None:
        if project_root is None:
            raise ValueError(
                "Either benchmark_script_path or project_root must be provided")
        # Benchmarks live at <project_root>/benchmarks, not under src/
        benchmark_script = project_root / "benchmarks" / "benchmark_inference.py"
    else:
        benchmark_script = benchmark_script_path

    if not benchmark_script.exists():
        print(f"Warning: Benchmark script not found: {benchmark_script}")
        return False

    args = [
        sys.executable,
        str(benchmark_script),
        "--checkpoint",
        str(checkpoint_dir),
        "--test-data",
        str(test_data_path),
        "--batch-sizes",
    ] + [str(bs) for bs in batch_sizes] + [
        "--iterations",
        str(iterations),
        "--warmup",
        str(warmup_iterations),
        "--max-length",
        str(max_length),
        "--output",
        str(output_path),
    ]

    if device:
        args.extend(["--device", device])

    cwd = project_root if project_root else checkpoint_dir.parent.parent.parent
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Benchmarking failed: {result.stderr}")
        return False

    # Log results to MLflow if tracker provided
    if tracker and output_path.exists():
        try:
            # Parse benchmark.json
            with open(output_path, 'r') as f:
                benchmark_data = json.load(f)

            # Extract backbone from checkpoint_dir if not provided
            if not backbone:
                backbone = checkpoint_dir.name

            # Create run name
            run_name = f"benchmark_{backbone}_{benchmark_source}"

            # Start benchmark run and log results
            with tracker.start_benchmark_run(
                run_name=run_name,
                backbone=backbone,
                benchmark_source=benchmark_source,
            ):
                tracker.log_benchmark_results(
                    batch_sizes=batch_sizes,
                    iterations=iterations,
                    warmup_iterations=warmup_iterations,
                    max_length=max_length,
                    device=device,
                    benchmark_json_path=output_path,
                    benchmark_data=benchmark_data,
                )
        except Exception as e:
            logger.warning(f"Could not log benchmark results to MLflow: {e}")
            # Don't fail benchmarking if MLflow logging fails

    return True
