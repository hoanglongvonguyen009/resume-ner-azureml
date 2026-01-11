"""
@meta
name: benchmarking_statistics
type: utility
domain: benchmarking
responsibility:
  - Calculate latency statistics from measurements
  - Compute percentiles (P95, P99)
  - Calculate throughput metrics
inputs:
  - List of latency measurements
  - Batch size
outputs:
  - Dictionary with statistical metrics
tags:
  - utility
  - benchmarking
  - statistics
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Statistics calculation for benchmarking results."""

import os
import sys
from typing import Dict, List

# Import standard library statistics module explicitly to avoid naming conflict
# with this file (statistics.py). The issue occurs when Python's import system
# finds this local file instead of the stdlib module.
# Solution: Temporarily modify sys.path to ensure stdlib is found first,
# then import the standard library module.

# Store original sys.path
_original_sys_path = sys.path[:]

# Get the directory containing this file and its parent
_this_file = __file__
_this_dir = os.path.dirname(os.path.abspath(_this_file))
_parent_dir = os.path.dirname(_this_dir)

# Temporarily remove paths that might contain this file from sys.path
# This ensures Python finds the stdlib module, not this local file
sys.path = [
    p for p in sys.path 
    if os.path.abspath(p) not in (os.path.abspath(_this_dir), os.path.abspath(_parent_dir))
]

try:
    # Now import statistics - Python will find the stdlib module
    import statistics
    
    # Verify it's the correct module (has 'mean' attribute)
    if not hasattr(statistics, 'mean'):
        raise ImportError("Imported wrong statistics module")
finally:
    # Always restore sys.path
    sys.path[:] = _original_sys_path


def calculate_latency_stats(
    latencies: List[float],
    batch_size: int,
) -> Dict[str, float]:
    """
    Calculate latency statistics from measurements.

    Args:
        latencies: List of latency measurements in milliseconds.
        batch_size: Batch size used for measurements.

    Returns:
        Dictionary with latency statistics:
        - mean_ms: Mean latency
        - median_ms: Median latency
        - p95_ms: 95th percentile latency
        - p99_ms: 99th percentile latency
        - throughput_docs_per_sec: Throughput in documents per second
    """
    if not latencies:
        return {
            "mean_ms": 0.0,
            "median_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "throughput_docs_per_sec": 0.0,
        }
    
    mean_ms = statistics.mean(latencies)
    median_ms = statistics.median(latencies)
    
    # Calculate percentiles
    sorted_latencies = sorted(latencies)
    p95_idx = int(len(sorted_latencies) * 0.95)
    p99_idx = int(len(sorted_latencies) * 0.99)
    p95_ms = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]
    p99_ms = sorted_latencies[min(p99_idx, len(sorted_latencies) - 1)]
    
    # Calculate throughput (documents per second)
    throughput_docs_per_sec = batch_size / (mean_ms / 1000)
    
    return {
        "mean_ms": mean_ms,
        "median_ms": median_ms,
        "p95_ms": p95_ms,
        "p99_ms": p99_ms,
        "throughput_docs_per_sec": throughput_docs_per_sec,
    }

