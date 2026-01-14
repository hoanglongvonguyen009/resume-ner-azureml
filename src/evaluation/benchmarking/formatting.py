"""
@meta
name: benchmarking_formatting
type: utility
domain: benchmarking
responsibility:
  - Format benchmark results as human-readable tables
  - Compare multiple model benchmarks side-by-side
inputs:
  - Benchmark results dictionary
  - List of benchmark JSON files (for comparison)
outputs:
  - Formatted table strings
tags:
  - utility
  - benchmarking
  - formatting
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Result formatting and comparison utilities for benchmarking."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def format_results_table(results: Dict[str, Any]) -> str:
    """
    Format benchmark results as a human-readable table.

    Args:
        results: Dictionary with benchmark results.

    Returns:
        Formatted table string.
    """
    lines = ["Benchmark Results", "=" * 60]
    
    for key, value in results.items():
        if key in ["device", "timestamp"]:
            continue
        
        if isinstance(value, dict) and "mean_ms" in value:
            batch_size = key.replace("batch_", "")
            lines.append(f"\nBatch Size: {batch_size}")
            lines.append(f"  Mean Latency:    {value['mean_ms']:.2f} ms")
            lines.append(f"  Median Latency:  {value['median_ms']:.2f} ms")
            lines.append(f"  P95 Latency:     {value['p95_ms']:.2f} ms")
            lines.append(f"  P99 Latency:     {value['p99_ms']:.2f} ms")
            lines.append(f"  Throughput:      {value['throughput_docs_per_sec']:.2f} docs/sec")
    
    if "device" in results:
        lines.append(f"\nDevice: {results['device']}")
    if "timestamp" in results:
        lines.append(f"Timestamp: {results['timestamp']}")
    
    return "\n".join(lines)


def compare_models(
    benchmark_files: List[Path],
    model_names: Optional[List[str]] = None,
) -> str:
    """
    Compare multiple model benchmarks side-by-side.

    Args:
        benchmark_files: List of paths to benchmark JSON files.
        model_names: Optional list of model names (defaults to file names).

    Returns:
        Formatted comparison table string.

    Raises:
        ValueError: If number of model names doesn't match number of files.
    """
    if model_names is None:
        model_names = [f.name.replace("_benchmark.json", "") for f in benchmark_files]
    
    if len(model_names) != len(benchmark_files):
        raise ValueError("Number of model names must match number of benchmark files")
    
    # Load all results
    all_results = []
    for file_path in benchmark_files:
        with open(file_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        all_results.append(results)
    
    # Build comparison table
    lines = ["Model Comparison", "=" * 80]
    
    # Find common batch sizes
    batch_size_keys: Set[str] = set()
    for result in all_results:
        for key in result.keys():
            if key.startswith("batch_"):
                batch_size_keys.add(key)
    
    batch_sizes = sorted(batch_size_keys, key=lambda x: int(x.replace("batch_", "")))
    
    # Header
    header = f"{'Batch Size':<12}"
    for name in model_names:
        header += f"{name:<20}"
    lines.append(header)
    lines.append("-" * len(header))
    
    # Mean latency comparison
    lines.append("\nMean Latency (ms):")
    for batch_size in batch_sizes:
        row = f"{batch_size.replace('batch_', ''):<12}"
        for results in all_results:
            if batch_size in results:
                latency = results[batch_size].get("mean_ms", 0.0)
                row += f"{latency:>18.2f}  "
            else:
                row += f"{'N/A':>18}  "
        lines.append(row)
    
    # Throughput comparison
    lines.append("\nThroughput (docs/sec):")
    for batch_size in batch_sizes:
        row = f"{batch_size.replace('batch_', ''):<12}"
        for results in all_results:
            if batch_size in results:
                throughput = results[batch_size].get("throughput_docs_per_sec", 0.0)
                row += f"{throughput:>18.2f}  "
            else:
                row += f"{'N/A':>18}  "
        lines.append(row)
    
    return "\n".join(lines)

