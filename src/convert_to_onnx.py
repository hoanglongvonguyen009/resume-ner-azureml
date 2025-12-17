"""Convert a trained Hugging Face token-classification checkpoint to ONNX.

This script is executed inside an Azure ML command job and is expected to:
- read a training checkpoint (a folder created via ``save_pretrained``),
- export an ONNX model into the provided output folder, and
- optionally apply dynamic int8 quantization and run a smoke test.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Iterable

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for model conversion.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Convert PyTorch checkpoint to ONNX")
    
    parser.add_argument(
        "--checkpoint-path",
        type=str,
        required=True,
        help="Path to PyTorch checkpoint directory",
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        required=True,
        help="Path to configuration directory",
    )
    parser.add_argument(
        "--backbone",
        type=str,
        required=True,
        help="Model backbone name (e.g., 'distilbert', 'deberta')",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for ONNX model",
    )
    parser.add_argument(
        "--quantize-int8",
        action="store_true",
        help="Enable int8 quantization",
    )
    parser.add_argument(
        "--run-smoke-test",
        action="store_true",
        help="Run smoke inference test after conversion",
    )
    
    return parser.parse_args()


def _list_files(root: Path, limit: int = 40) -> list[str]:
    if not root.exists():
        return []
    files: list[str] = []
    try:
        for item in root.rglob("*"):
            if item.is_file():
                files.append(str(item.relative_to(root)))
                if len(files) >= limit:
                    break
    except Exception:
        return files
    return files


def resolve_checkpoint_dir(checkpoint_path: str) -> Path:
    """Resolve an Azure ML mounted input folder to the HF checkpoint directory."""
    root = Path(checkpoint_path)
    if not root.exists():
        raise FileNotFoundError(f"Checkpoint path not found: {checkpoint_path}")

    # Training saves into `<output_dir>/checkpoint/` using Hugging Face save_pretrained.
    candidates = [root, root / "checkpoint"]
    for d in candidates:
        if not d.exists() or not d.is_dir():
            continue
        # A HF model directory contains at least one of these.
        if (d / "config.json").exists() and (
            (d / "pytorch_model.bin").exists()
            or (d / "model.safetensors").exists()
            or (d / "model.pt").exists()
        ):
            return d

    files = _list_files(root)
    raise FileNotFoundError(
        "Could not locate a Hugging Face checkpoint directory under "
        f"'{checkpoint_path}'. Expected a folder created by `save_pretrained` "
        "containing `config.json` and model weights. "
        f"Found files (up to 40): {files}"
    )


def _dynamic_axes_for(inputs: Dict[str, torch.Tensor]) -> Dict[str, Dict[int, str]]:
    axes: Dict[str, Dict[int, str]] = {}
    for name, tensor in inputs.items():
        if tensor.dim() >= 2:
            axes[name] = {0: "batch", 1: "seq"}
        elif tensor.dim() == 1:
            axes[name] = {0: "batch"}
    # Output logits are [batch, seq, num_labels]
    axes["logits"] = {0: "batch", 1: "seq"}
    return axes


def convert_to_onnx(
    output_dir: Path,
    quantize_int8: bool,
) -> Path:
    checkpoint_dir: Path,
) -> Path:
    """Export a token-classification model to ONNX (and optionally quantize)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load model + tokenizer from the saved checkpoint directory
    tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir, use_fast=True)
    model = AutoModelForTokenClassification.from_pretrained(checkpoint_dir)
    model.eval()

    # Build a tiny example batch for tracing
    example = tokenizer(
        "John Doe works at Microsoft in Seattle.",
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=32,
    )
    # Some models don't use token_type_ids; export only what the model accepts.
    allowed_keys: Iterable[str] = ("input_ids", "attention_mask", "token_type_ids")
    inputs: Dict[str, torch.Tensor] = {
        k: v for k, v in example.items() if k in allowed_keys
    }
    # Ensure stable ordering aligned with HF forward signature
    input_names = [k for k in ("input_ids", "attention_mask", "token_type_ids") if k in inputs]
    output_names = ["logits"]
    dynamic_axes = _dynamic_axes_for(inputs)

    fp32_path = output_dir / "model.onnx"
    torch.onnx.export(
        model,
        args=tuple(inputs[name] for name in input_names),
        f=str(fp32_path),
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
        opset_version=17,
        do_constant_folding=True,
    )

    if not quantize_int8:
        return fp32_path

    int8_path = output_dir / "model_int8.onnx"
    try:
        from onnxruntime.quantization import QuantType, quantize_dynamic

        quantize_dynamic(
            model_input=str(fp32_path),
            model_output=str(int8_path),
            weight_type=QuantType.QInt8,
        )
        return int8_path
    except Exception as e:
        # Don't fail the whole conversion if quantization tooling isn't available.
        # The caller requested int8, so we keep fp32 but emit a clear warning.
        import warnings

        warnings.warn(
            f"Int8 quantization requested but failed ({type(e).__name__}: {e}). "
            f"Falling back to fp32 ONNX at {fp32_path}."
        )
        return fp32_path


def run_smoke_test(onnx_path: Path, checkpoint_dir: Path) -> None:
    """Run a minimal ONNX Runtime inference to validate the exported graph."""
    try:
        import numpy as np
        import onnxruntime as ort
    except Exception as e:
        import warnings

        warnings.warn(
            f"Smoke test skipped because onnxruntime/numpy is not available: {e}"
        )
        return

    tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir, use_fast=True)
    example = tokenizer(
        "Jane Doe is a software engineer.",
        return_tensors="np",
        padding="max_length",
        truncation=True,
        max_length=16,
    )
    # Ensure int64 inputs (ORT expects int64 for ids/masks)
    feeds: Dict[str, Any] = {}
    for k, v in example.items():
        if k in ("input_ids", "attention_mask", "token_type_ids"):
            feeds[k] = v.astype(np.int64)

    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    # Only feed expected inputs (some models omit token_type_ids)
    input_names = {i.name for i in sess.get_inputs()}
    feeds = {k: v for k, v in feeds.items() if k in input_names}

    outputs = sess.run(None, feeds)
    if not outputs or outputs[0] is None:
        raise RuntimeError("ONNX smoke test failed: no logits returned")


def main() -> None:
    """
    Main conversion entry point.
    """
    args = parse_arguments()
    
    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    checkpoint_dir = resolve_checkpoint_dir(args.checkpoint_path)
    output_dir = Path(args.output_dir)

    onnx_path = convert_to_onnx(
        output_dir=output_dir,
        quantize_int8=args.quantize_int8,
        checkpoint_dir=checkpoint_dir,
    )

    if args.run_smoke_test:
        run_smoke_test(onnx_path, checkpoint_dir)


if __name__ == "__main__":
    main()

