"""
@meta
name: benchmarking_cli
type: script
domain: benchmarking
responsibility:
  - CLI entry point for inference benchmarking
  - Orchestrate model loading, inference execution, and statistics
  - Parse command-line arguments
inputs:
  - Model checkpoint directory
  - Test data JSON file
outputs:
  - Benchmark results JSON file
tags:
  - entrypoint
  - cli
  - benchmarking
ci:
  runnable: true
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure src directory is in Python path for absolute imports
# This allows the script to be run directly: python src/evaluation/benchmarking/cli.py
_script_dir = Path(__file__).parent.parent.parent  # Go up to src/
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))
from typing import Any, Dict, List, Optional

# Import only when CLI is actually used (not at module level)
# This allows the module to be imported without torch being available


def benchmark_model(
    checkpoint_dir: Path,
    test_texts: List[str],
    batch_sizes: List[int] = [1, 8, 16],
    num_iterations: int = 100,
    warmup_iterations: int = 10,
    device: Optional[str] = None,
    max_length: int = 512,
) -> Dict[str, Any]:
    """Benchmark model inference performance across different batch sizes."""
    # Use absolute imports to support both module import and direct script execution
    from evaluation.benchmarking.data_loader import load_test_texts
    from evaluation.benchmarking.execution import run_batch_inference, run_warmup_iterations
    from evaluation.benchmarking.model_loader import load_model_from_checkpoint
    from evaluation.benchmarking.statistics import calculate_latency_stats
    """
    Benchmark model inference performance across different batch sizes.

    Args:
        checkpoint_dir: Path to checkpoint directory.
        test_texts: List of test texts to use for benchmarking.
        batch_sizes: List of batch sizes to test.
        num_iterations: Number of iterations per batch size.
        warmup_iterations: Number of warmup iterations.
        device: Device to use ('cuda', 'cpu', or None for auto-detect).
        max_length: Maximum sequence length.

    Returns:
        Dictionary with benchmark results for each batch size.
    """
    print(f"Starting benchmark for checkpoint: {checkpoint_dir}", flush=True)
    model, tokenizer, device_obj = load_model_from_checkpoint(checkpoint_dir, device)
    print(f"Model ready on device: {device_obj}", flush=True)
    
    results: Dict[str, Any] = {}
    
    for batch_size in batch_sizes:
        print(f"\nBenchmarking batch size {batch_size}...", flush=True)
        
        # Create batch
        batch_texts = test_texts[:batch_size]
        if len(batch_texts) < batch_size:
            # Repeat texts if needed
            batch_texts = (batch_texts * ((batch_size // len(batch_texts)) + 1))[:batch_size]
        
        # Benchmark this batch size
        print(f"  Running {warmup_iterations} warmup iterations, then {num_iterations} measurement iterations...", flush=True)
        
        # Run warmup
        run_warmup_iterations(
            model=model,
            tokenizer=tokenizer,
            texts=batch_texts,
            device=device_obj,
            max_length=max_length,
            count=warmup_iterations,
        )
        
        # Run inference and collect latencies
        latencies = run_batch_inference(
            model=model,
            tokenizer=tokenizer,
            texts=batch_texts,
            device=device_obj,
            max_length=max_length,
            num_iterations=num_iterations,
        )
        
        # Calculate statistics
        batch_results = calculate_latency_stats(latencies, batch_size)
        results[f"batch_{batch_size}"] = batch_results
        
        print(f"  Mean latency: {batch_results['mean_ms']:.2f} ms", flush=True)
        print(f"  P95 latency: {batch_results['p95_ms']:.2f} ms", flush=True)
        print(f"  Throughput: {batch_results['throughput_docs_per_sec']:.2f} docs/sec", flush=True)
    
    # Add metadata
    results["device"] = str(device_obj)
    results["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    return results


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Benchmark NER model inference performance"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Path to model checkpoint directory",
    )
    parser.add_argument(
        "--test-data",
        type=str,
        required=True,
        help="Path to test data JSON file (list of texts or list of dicts with 'text' field)",
    )
    parser.add_argument(
        "--batch-sizes",
        type=int,
        nargs="+",
        default=[1, 8, 16],
        help="Batch sizes to test (default: 1 8 16)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations per batch size (default: 100)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
        help="Number of warmup iterations (default: 10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output JSON file for benchmark results",
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["cuda", "cpu"],
        default=None,
        help="Device to use (default: auto-detect)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="Maximum sequence length (default: 512)",
    )
    
    return parser.parse_args()


def main() -> None:
    """CLI entry point for benchmarking script."""
    # Use absolute imports to support both module import and direct script execution
    from evaluation.benchmarking.data_loader import load_test_texts
    
    args = parse_args()
    
    # Load test data
    checkpoint_dir = Path(args.checkpoint)
    test_data_path = Path(args.test_data)
    output_path = Path(args.output)
    
    if not checkpoint_dir.exists():
        raise ValueError(f"Checkpoint directory not found: {checkpoint_dir}")
    
    if not test_data_path.exists():
        raise ValueError(f"Test data file not found: {test_data_path}")
    
    # Load test texts
    test_texts = load_test_texts(test_data_path)
    
    if not test_texts:
        raise ValueError("No test texts found in test data file")
    
    print(f"Loaded {len(test_texts)} test texts", flush=True)
    
    # Run benchmark
    results = benchmark_model(
        checkpoint_dir=checkpoint_dir,
        test_texts=test_texts,
        batch_sizes=args.batch_sizes,
        num_iterations=args.iterations,
        warmup_iterations=args.warmup,
        device=args.device,
        max_length=args.max_length,
    )
    
    # Save results
    print(f"\nSaving results to {output_path}...", flush=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"Benchmark results saved to {output_path}", flush=True)


if __name__ == "__main__":
    main()

