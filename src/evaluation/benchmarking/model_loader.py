"""
@meta
name: benchmarking_model_loader
type: utility
domain: benchmarking
responsibility:
  - Load model and tokenizer from checkpoint directory
  - Handle device selection (CUDA/CPU)
  - Set model to evaluation mode
inputs:
  - Checkpoint directory path
  - Device preference (optional)
outputs:
  - Loaded model, tokenizer, and device object
tags:
  - utility
  - benchmarking
  - model-loading
ci:
  runnable: true
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

"""Model loading utilities for benchmarking."""

from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer


def load_model_from_checkpoint(
    checkpoint_dir: Path,
    device: Optional[str] = None,
) -> Tuple["AutoModelForTokenClassification", "AutoTokenizer", "torch.device"]:
    """
    Load model and tokenizer from checkpoint directory.

    Args:
        checkpoint_dir: Path to checkpoint directory containing model files.
        device: Device to load model on ('cuda', 'cpu', or None for auto-detect).

    Returns:
        Tuple of (model, tokenizer, device).
    """
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer
    
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    device_obj = torch.device(device)
    
    # Load tokenizer
    print(f"Loading tokenizer from {checkpoint_dir}...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir)
    print("Tokenizer loaded.", flush=True)
    
    # Load model
    print(f"Loading model from {checkpoint_dir}...", flush=True)
    model = AutoModelForTokenClassification.from_pretrained(checkpoint_dir)
    print(f"Moving model to {device_obj}...", flush=True)
    model.to(device_obj)
    model.eval()
    print("Model loaded and set to eval mode.", flush=True)
    
    return model, tokenizer, device_obj

