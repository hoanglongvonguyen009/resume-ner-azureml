"""Convert a trained Hugging Face token-classification checkpoint to ONNX.

This script is executed inside an Azure ML command job and is expected to:

* Read a training checkpoint (a folder created via ``save_pretrained``)
* Export an ONNX model into the provided output folder
* Optionally apply dynamic int8 quantization and run a smoke test
"""

from pathlib import Path

from .cli import parse_conversion_arguments
from .onnx_exporter import export_to_onnx
from .smoke_test import run_smoke_test
from platform_adapters import get_platform_adapter
from platform_adapters.checkpoint_resolver import CheckpointResolver
from shared.argument_parsing import validate_config_dir
from shared.logging_utils import get_script_logger

_log = get_script_logger("convert_to_onnx")


def resolve_checkpoint_dir(checkpoint_path: str) -> Path:
    """Resolve checkpoint path to HF checkpoint directory using platform adapter."""
    platform_adapter = get_platform_adapter()
    checkpoint_resolver = platform_adapter.get_checkpoint_resolver()
    
    _log(f"Resolving checkpoint directory from '{checkpoint_path}'")
    return checkpoint_resolver.resolve_checkpoint_dir(checkpoint_path)


def main() -> None:
    """Main conversion entry point."""
    args = parse_conversion_arguments()
    _log(
        "Starting model conversion job with arguments: "
        f"checkpoint_path='{args.checkpoint_path}', "
        f"config_dir='{args.config_dir}', "
        f"backbone='{args.backbone}', "
        f"output_dir='{args.output_dir}', "
        f"quantize_int8={args.quantize_int8}, "
        f"run_smoke_test={args.run_smoke_test}"
    )
    
    config_dir = validate_config_dir(args.config_dir)
    _log(f"Using config directory: '{config_dir}'")
    
    checkpoint_dir = resolve_checkpoint_dir(args.checkpoint_path)
    
    # Use platform adapter for output directory resolution
    platform_adapter = get_platform_adapter(default_output_dir=Path(args.output_dir))
    output_resolver = platform_adapter.get_output_path_resolver()
    output_dir = output_resolver.resolve_output_path("onnx_model", default=Path(args.output_dir))
    output_dir = output_resolver.ensure_output_directory(output_dir)
    _log(
        f"Resolved checkpoint directory to '{checkpoint_dir}', "
        f"output directory to '{output_dir}'"
    )
    
    onnx_path = export_to_onnx(
        checkpoint_dir=checkpoint_dir,
        output_dir=output_dir,
        quantize_int8=args.quantize_int8,
    )
    _log(f"Conversion completed. ONNX model written to '{onnx_path}'")
    
    if args.run_smoke_test:
        run_smoke_test(onnx_path, checkpoint_dir)
    else:
        _log("Smoke test not requested; skipping")


if __name__ == "__main__":
    main()




