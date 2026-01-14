"""
@meta
name: benchmarking_execution
type: utility
domain: benchmarking
responsibility:
  - Execute model inference with timing measurement
  - Run warmup iterations to avoid cold start effects
  - Measure batch inference latency
inputs:
  - Loaded model and tokenizer
  - Input texts
  - Device configuration
outputs:
  - Latency measurements (milliseconds)
tags:
  - utility
  - benchmarking
  - inference
ci:
  runnable: true
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

"""Inference execution and measurement for benchmarking."""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer

# Progress reporting intervals
WARMUP_PROGRESS_INTERVAL = 10  # Show progress every N warmup iterations
BATCH_PROGRESS_INTERVAL = 20  # Show progress every N batch iterations


def run_single_inference(
    model: "AutoModelForTokenClassification",
    tokenizer: "AutoTokenizer",
    text: str,
    device: "torch.device",
    max_length: int = 512,
) -> float:
    """
    Measure single document inference time.

    Args:
        model: Loaded model.
        tokenizer: Loaded tokenizer.
        text: Input text to process.
        device: Device to run inference on.
        max_length: Maximum sequence length.

    Returns:
        Inference time in milliseconds.
    """
    import torch
    import time
    
    # Tokenize
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Measure inference time
    start = time.perf_counter()
    with torch.no_grad():
        outputs = model(**inputs)
    end = time.perf_counter()
    
    latency_ms = (end - start) * 1000
    return latency_ms


def run_warmup_iterations(
    model: "AutoModelForTokenClassification",
    tokenizer: "AutoTokenizer",
    texts: List[str],
    device: "torch.device",
    max_length: int = 512,
    count: int = 10,
) -> None:
    """
    Run warmup iterations to avoid cold start effects.

    Args:
        model: Loaded model.
        tokenizer: Loaded tokenizer.
        texts: List of input texts to process.
        device: Device to run inference on.
        max_length: Maximum sequence length.
        count: Number of warmup iterations.
    """
    import torch
    
    if count <= 0:
        return
    
    print(f"    Warmup: {count} iterations...", flush=True, end="")
    for i in range(count):
        inputs = tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            _ = model(**inputs)
        # Show progress every N iterations
        if (i + 1) % WARMUP_PROGRESS_INTERVAL == 0 or (i + 1) == count:
            print(f" {i + 1}/{count}", flush=True, end="")
    print(" done.", flush=True)


def run_batch_inference(
    model: "AutoModelForTokenClassification",
    tokenizer: "AutoTokenizer",
    texts: List[str],
    device: "torch.device",
    max_length: int = 512,
    num_iterations: int = 100,
) -> List[float]:
    """
    Measure batch inference latency for multiple iterations.

    Args:
        model: Loaded model.
        tokenizer: Loaded tokenizer.
        texts: List of input texts to process.
        device: Device to run inference on.
        max_length: Maximum sequence length.
        num_iterations: Number of iterations to measure.

    Returns:
        List of latency measurements in milliseconds.
    """
    import torch
    import time
    
    latencies = []
    
    # Actual measurement
    print(f"    Measurement: {num_iterations} iterations...", flush=True, end="")
    for i in range(num_iterations):
        inputs = tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        start = time.perf_counter()
        with torch.no_grad():
            _ = model(**inputs)
        end = time.perf_counter()
        
        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)
        
        # Show progress every N iterations
        if (i + 1) % BATCH_PROGRESS_INTERVAL == 0 or (i + 1) == num_iterations:
            print(f" {i + 1}/{num_iterations}", flush=True, end="")
    print(" done.", flush=True)
    
    return latencies

