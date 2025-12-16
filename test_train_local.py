#!/usr/bin/env python3
"""Local test script for training code before submitting to Azure ML."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_training():
    """Test training locally with tiny dataset."""
    from train import build_training_config, load_dataset, train_model, write_metrics
    import argparse
    
    # Mock arguments
    args = argparse.Namespace(
        data_asset=str(Path("dataset_tiny").absolute()),
        config_dir=str(Path("config").absolute()),
        backbone="distilbert",
        learning_rate=2e-5,
        batch_size=8,
        dropout=0.1,
        weight_decay=0.01,
        epochs=1,
        random_seed=42,
        early_stopping_enabled="false",
        use_combined_data="false",
    )
    
    print("=" * 60)
    print("Testing training locally...")
    print(f"Dataset: {args.data_asset}")
    print(f"Backbone: {args.backbone}")
    print("=" * 60)
    
    config_dir = Path(args.config_dir)
    config = build_training_config(args, config_dir)
    dataset = load_dataset(args.data_asset)
    
    output_dir = Path("./test_outputs")
    output_dir.mkdir(exist_ok=True)
    
    metrics = train_model(config, dataset, output_dir)
    write_metrics(output_dir, metrics)
    
    print("\n✓ Local test completed!")
    print(f"Metrics: {metrics}")

if __name__ == "__main__":
    try:
        test_training()
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


