# Resume NER Training with Azure ML

A comprehensive Named Entity Recognition (NER) training pipeline for resume parsing, supporting multiple execution platforms including Azure ML, Google Colab, and Kaggle.

## Features

- **Multi-Platform Support**: Train on Azure ML, Google Colab, or Kaggle
- **Hyperparameter Optimization**: Automated HPO using Optuna or Azure ML Sweeps
- **Model Selection**: Automated best model selection with benchmarking
- **ONNX Export**: Convert trained models to ONNX for optimized inference
- **Centralized Configuration**: YAML-based configuration management
- **Experiment Tracking**: MLflow integration for experiment tracking

## Platform Support

### ✅ Tested and Verified

- **Google Colab**: ✅ Successfully tested with GPU runtime
- **Kaggle**: ✅ Successfully tested with GPU kernels
- **Azure ML**: Full support for cloud-based training
- **Local**: Support for local machine training

### Platform-Specific Features

#### Google Colab
- Automatic checkpoint backup to Google Drive
- Session persistence across disconnections
- GPU runtime support

#### Kaggle
- Automatic output persistence in `/kaggle/working/`
- GPU kernel support
- No manual backup required

## Quick Start

### Google Colab / Kaggle

1. Open the notebook: `notebooks/01_orchestrate_training_colab.ipynb`
2. Clone the repository:
   ```python
   # For Google Colab
   !git clone -b feature/google-colab-compute https://github.com/longdang193/resume-ner-azureml.git /content/resume-ner-azureml
   
   # For Kaggle
   !git clone -b feature/google-colab-compute https://github.com/longdang193/resume-ner-azureml.git /kaggle/working/resume-ner-azureml
   ```
3. Run all cells sequentially

### Azure ML

See `notebooks/01_orchestrate_training.ipynb` for Azure ML-based training.

### Local Training

See `notebooks/01_orchestrate_training_local.ipynb` for local machine training.

## Documentation

- [Local Training Workflow](docs/LOCAL_TRAINING.md)
- [Centralized Configuration](docs/Centralized_Configuration.md)
- [Model Selection Strategy](docs/MODEL_SELECTION_STRATEGY.md)
- [Platform Adapter Architecture](docs/PLATFORM_ADAPTER_ARCHITECTURE.md)

## Project Structure

```
resume-ner-azureml/
├── config/              # Centralized YAML configurations
│   ├── experiment/      # Experiment definitions
│   ├── data/           # Dataset configurations
│   ├── model/          # Model configurations
│   ├── hpo/            # Hyperparameter optimization configs
│   └── train.yaml      # Training defaults
├── src/                # Source code
│   ├── training/       # Training modules
│   ├── orchestration/  # Orchestration logic
│   └── platform_adapters/  # Platform-specific adapters
├── notebooks/          # Jupyter notebooks
│   ├── 01_orchestrate_training.ipynb          # Azure ML
│   ├── 01_orchestrate_training_colab.ipynb    # Colab/Kaggle
│   └── 01_orchestrate_training_local.ipynb   # Local
└── docs/               # Documentation
```

## Requirements

- Python 3.10+
- PyTorch (with CUDA for GPU support)
- See `config/environment/conda.yaml` for full dependencies

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

