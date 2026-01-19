# Resume NER with Azure ML

Named Entity Recognition (NER) model training, evaluation, and deployment pipeline using Azure ML, MLflow, and a configuration-driven workflow.

## Project Overview

This project provides a complete ML pipeline for training, evaluating, and deploying NER models:

- **Training**: Hyperparameter optimization (HPO) and model training workflows (local + AzureML)
- **Evaluation**: Model selection, benchmarking, and performance evaluation
- **Deployment**: Model conversion (PyTorch → ONNX) and FastAPI API serving (Docker-ready)
- **Infrastructure**: Configuration management, MLflow tracking, naming, paths, and platform abstraction

The codebase is structured to keep notebooks thin and put all reusable logic in `src/`, with MLflow and AzureML integration handled by the `infrastructure` layer.

## Local Environment Setup

- **Python**: 3.10 (recommended; see `pyproject.toml` for details)
- **Dependencies**: Managed via `pyproject.toml` and tooling such as `uv`/`uvx` (preferred) or `pip`.

Minimal local setup:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -e .  # or use your preferred installer for pyproject-based projects
```

Run tests to verify:

```bash
uvx pytest tests/
```

## Pain points this project solves

If you’ve built ML pipelines before, these are the recurring problems this repo is designed to remove:

- **Reproducibility drift (“which config produced this model?”)**  
  Solved by a configuration-driven workflow (`config/`) + consistent output layout (`outputs/`) + explicit fingerprints/metadata in the infrastructure layer.

- **Run naming chaos (hard to compare experiments across sweeps/backbones)**  
  Solved by centralized naming policies and run keys in `src/infrastructure/naming/` and MLflow index helpers in `src/infrastructure/tracking/mlflow/`.

- **Fragmented experiment tracking (metrics/artifacts scattered across notebooks, local files, and cloud logs)**  
  Solved by centralizing metrics and artifacts in **MLflow** (local MLflow or **AzureML-backed MLflow** when running in Azure) using `setup_mlflow(...)` as a **single source of truth** for tracking setup, and by standardizing what gets logged during HPO/training (see [`docs/architecture/mlflow-utilities.md`](docs/architecture/mlflow-utilities.md)).

- **Selection is subjective (picking “best” trial by eyeballing charts)**  
  Solved by explicit selection logic in `src/evaluation/selection` that supports accuracy–speed tradeoffs and can run on both local and AzureML sweep outputs.

## Configuration-Driven Workflows

All major workflows (HPO, training, evaluation, conversion, deployment) read from configuration files under `config/`:

- **Experiment configs**: Select which backbone, data asset, and training/HPO settings to use.
- **MLflow + naming configs**: Control tracking URI, experiment names, naming policies, and run indexing.
- **Path configs**: Define how outputs are laid out under `outputs/` (HPO, training, conversion, benchmarking).

The `infrastructure` module provides:

- `load_experiment_config(...)` – load experiment config from `config/`
- `resolve_output_path(...)` – compute consistent output paths under `outputs/`
- `setup_mlflow(...)` – Single Source of Truth for MLflow setup

See `src/infrastructure/README.md` and related submodule READMEs for details.

## End-to-End Pipeline

The end-to-end flow is:

| Stage | How it runs (examples) | Key artifacts (examples) |
| --- | --- | --- |
| **HPO** | Local Optuna sweeps via `training.hpo.run_local_hpo_sweep` or AzureML sweep jobs via `training.hpo.execution.azureml.*` utilities | `outputs/hpo/**`, MLflow runs (local `mlruns/` or AzureML-backed MLflow) |
| **Best config selection** | Selection functions in `evaluation.selection` (e.g., `select_best_configuration_across_studies`) using HPO outputs | Best-config JSON / structures under `outputs/hpo/**` |
| **Final training** | Training workflows in `training.execution` (local) or AzureML training jobs via `training.execution.jobs.*` | `outputs/final_training/**` (checkpoints, metrics, MLflow) |
| **Conversion to ONNX** | Conversion workflow `deployment.conversion.orchestration.run_conversion_workflow` | `outputs/conversion/**` (ONNX models, metadata) |
| **API serving (local/Docker)** | FastAPI app in `src.deployment.api` via `uvicorn` or `python -m src.deployment.api.cli.run_api`, optionally containerized using `Dockerfile` and `docs/docker_build.md` | Running API on port 8000, logs, health + prediction endpoints |

Each stage has a dedicated module README with detailed usage examples:

- **Training**: [`src/training/README.md`](src/training/README.md)
- **Evaluation**: [`src/evaluation/README.md`](src/evaluation/README.md)
- **Deployment**: [`src/deployment/README.md`](src/deployment/README.md)
- **Infrastructure**: [`src/infrastructure/README.md`](src/infrastructure/README.md)

## Where outputs land (artifacts)

- **Local runs**
  - **Artifacts on disk**: under `outputs/` (HPO studies, checkpoints, conversion outputs, benchmarking summaries).
  - **MLflow tracking**:
    - If you use a local file-based tracking URI, you’ll typically see `mlruns/` in your working directory.
    - If you configure a DB-backed store (optional), your DB location depends on your MLflow config.
- **AzureML runs**
  - **MLflow runs**: appear in **AzureML-backed MLflow** (Azure ML Studio experiment/runs view).
  - **Artifacts**: stored with the job/run in the AzureML workspace backing storage (and are accessible via MLflow artifacts as well).

## Quick Start: Local HPO → Train → Convert → Serve

1. **Prepare data** under `dataset/` following the format in `src/data/README.md`.
2. **Run a local HPO sweep** using `training.hpo.run_local_hpo_sweep` (see `src/training/README.md` for concrete examples).
3. **Select the best configuration** using `evaluation.selection.select_best_configuration_across_studies`.
4. **Run final training** with `training.execution.run_final_training_workflow` using the best configuration.
5. **Convert the trained model to ONNX** with `deployment.conversion.orchestration.run_conversion_workflow`.
6. **Serve the ONNX model via FastAPI**:

   ```bash
   uvicorn src.deployment.api:app --host 0.0.0.0 --port 8000
   ```

7. **Call the API** (see `src/deployment/README.md` and `docs/docker_build.md` for full examples).

## Running on Azure ML

This repo supports AzureML HPO and training jobs via:

- `training.hpo.execution.azureml.*` – HPO sweep job creation and validation
- `training.execution.jobs.*` – final training job creation and validation
- `infrastructure.azureml.submit_and_wait_for_job(...)` – job submission, log streaming, and status monitoring

Workspace settings are read from `config.env` (copy from `config.env.example`).

### AzureML prerequisites (do this before submitting jobs)

- **Azure authentication**
  - Run `az login` (local dev), or set service principal values in `config.env` if you can’t use interactive login.
- **Workspace configuration**
  - Copy `config.env.example` → `config.env` and set:
    - `AZURE_SUBSCRIPTION_ID`
    - `AZURE_RESOURCE_GROUP`
    - `AZURE_LOCATION`
    - Optional (only if not using `az login`): `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
- **AzureML workspace + compute**
  - Ensure the AzureML workspace exists in the configured subscription/resource group.
  - Ensure required compute targets referenced by your configs exist (see `src/training/README.md` for job details).

High-level pattern (see `src/training/README.md` for full code):

```python
from training.execution.jobs import (
    build_final_training_config,
    create_final_training_job,
    validate_final_training_job,
)
from infrastructure.azureml import submit_and_wait_for_job

final_config = build_final_training_config(best_config=best_hpo_config, train_config=train_config, random_seed=42)
training_job = create_final_training_job(..., final_config=final_config, ...)
completed_job = submit_and_wait_for_job(ml_client, training_job)
validate_final_training_job(completed_job)
```

Evaluation and selection utilities (`src/evaluation/selection`) can operate on both local Optuna and AzureML sweep outputs.

## Docker Usage (API Serving)

Docker support for the FastAPI API is described in detail in `docs/docker_build.md`. The typical flow:

```bash
docker build -t resume-ner-api:latest .

docker run -d \
  --name resume-ner-api \
  -p 8000:8000 \
  -v "$(pwd)/outputs:/app/outputs" \
  resume-ner-api:latest \
  conda run -n resume-ner-training python -m src.deployment.api.cli.run_api \
    --onnx-model /app/outputs/conversion/local/<model_path>/model.onnx \
    --checkpoint /app/outputs/final_training/local/<checkpoint_path>/checkpoint \
    --host 0.0.0.0 \
    --port 8000
```

For more advanced patterns (auto-discovering models, docker-compose, health checks, troubleshooting), see `docs/docker_build.md`.

## Project Structure

```text
src/
├── core/              # Core utilities (tokens, normalization, placeholders)
├── common/            # Shared utilities (logging, hashing, constants)
├── data/              # Data loading and processing
├── training/          # Training workflows, HPO, execution (local + AzureML)
├── infrastructure/    # Configuration, paths, tracking, naming, platform, AzureML runtime
├── evaluation/        # Model evaluation, selection, benchmarking
├── orchestration/     # Job orchestration and workflows
├── deployment/        # Model conversion and API serving
└── testing/           # Testing infrastructure

tests/                 # Test suites
config/                # Configuration files (experiment, paths, MLflow, naming, etc.)
outputs/               # Generated artifacts (HPO, training, conversion, benchmarking)
```

## Module Documentation

Comprehensive module documentation is available in the **Module Documentation Index**:

- [`docs/modules/INDEX.md`](docs/modules/INDEX.md)

Each module README follows the shared documentation standards in:

- [`docs/templates/TEMPLATE-documentation_standards.md`](docs/templates/TEMPLATE-documentation_standards.md)

Module READMEs include:

- TL;DR / Quick Start
- Overview and key concepts
- Usage examples
- API reference (stable surface only)
- Integration points
- Related modules

## Getting Help

- **Module documentation**: See [`docs/modules/INDEX.md`](docs/modules/INDEX.md)
- **Implementation plans**: See [`docs/implementation_plans/`](docs/implementation_plans/)
- **Documentation standards**: See [`docs/templates/TEMPLATE-documentation_standards.md`](docs/templates/TEMPLATE-documentation_standards.md)
