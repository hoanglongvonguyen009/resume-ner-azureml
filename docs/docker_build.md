# Docker Build Guide

This guide explains how to build and run the Resume NER API server using Docker.

## Prerequisites

- Docker installed and running
- Docker Compose (optional, for easier orchestration)
- Access to trained models (ONNX model and checkpoint directory)

## Overview

The Docker image is built from the conda environment definition (`config/environment/conda.yaml`), which includes all required dependencies:

- Python 3.10
- PyTorch 2.6+
- FastAPI and Uvicorn
- ONNX Runtime
- OCR dependencies (EasyOCR, Pillow)
- PDF extraction libraries (PyMuPDF, pdfplumber)
- All ML and AzureML dependencies

## Building the Docker Image

### Option 1: Using Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM continuumio/miniconda3:latest

WORKDIR /app

# Copy conda environment file
COPY config/environment/conda.yaml /app/config/environment/conda.yaml

# Create conda environment from yaml
RUN conda env create -f config/environment/conda.yaml && \
    conda clean -afy

# Copy source code
COPY src/ /app/src/
COPY config/ /app/config/

# Set environment variables
ENV PYTHONPATH=/app/src:/app
ENV PATH=/opt/conda/envs/resume-ner-training/bin:$PATH

# Activate conda environment in shell
SHELL ["conda", "run", "-n", "resume-ner-training", "/bin/bash", "-c"]

# Expose API port
EXPOSE 8000

# Default command (can be overridden)
CMD ["conda", "run", "-n", "resume-ner-training", "python", "-m", "src.deployment.api.cli.run_api", "--help"]
```

Then build:

```bash
docker build -t resume-ner-api:latest .
```

### Option 2: Multi-stage Build (Optimized)

For a smaller final image:

```dockerfile
# Stage 1: Build environment
FROM continuumio/miniconda3:latest AS builder

WORKDIR /app

COPY config/environment/conda.yaml /app/config/environment/conda.yaml

# Create conda environment
RUN conda env create -f config/environment/conda.yaml && \
    conda clean -afy

# Stage 2: Runtime image
FROM continuumio/miniconda3:latest

WORKDIR /app

# Copy conda environment from builder
COPY --from=builder /opt/conda/envs/resume-ner-training /opt/conda/envs/resume-ner-training

# Copy source code
COPY src/ /app/src/
COPY config/ /app/config/

# Set environment variables
ENV PYTHONPATH=/app/src:/app
ENV PATH=/opt/conda/envs/resume-ner-training/bin:$PATH

# Activate conda environment in shell
SHELL ["conda", "run", "-n", "resume-ner-training", "/bin/bash", "-c"]

EXPOSE 8000

CMD ["conda", "run", "-n", "resume-ner-training", "python", "-m", "src.deployment.api.cli.run_api", "--help"]
```

## Running the Container

### Basic Run

```bash
docker run -d \
  --name resume-ner-api \
  -p 8000:8000 \
  -v $(pwd)/outputs:/app/outputs \
  resume-ner-api:latest \
  conda run -n resume-ner-training python -m src.deployment.api.cli.run_api \
    --onnx-model /app/outputs/conversion/local/<model_path>/model.onnx \
    --checkpoint /app/outputs/final_training/local/<checkpoint_path>/checkpoint \
    --host 0.0.0.0 \
    --port 8000
```

### With Environment Variables

```bash
docker run -d \
  --name resume-ner-api \
  -p 8000:8000 \
  -v $(pwd)/outputs:/app/outputs \
  -e OCR_EXTRACTOR=easyocr \
  -e PDF_EXTRACTOR=pymupdf \
  resume-ner-api:latest \
  conda run -n resume-ner-training python -m src.deployment.api.cli.run_api \
    --onnx-model /app/outputs/conversion/local/<model_path>/model.onnx \
    --checkpoint /app/outputs/final_training/local/<checkpoint_path>/checkpoint \
    --host 0.0.0.0 \
    --port 8000
```

### Find Models Automatically

If you want to find models automatically, you can mount the outputs directory and use a helper script:

```bash
docker run -d \
  --name resume-ner-api \
  -p 8000:8000 \
  -v $(pwd)/outputs:/app/outputs \
  resume-ner-api:latest \
  conda run -n resume-ner-training bash -c "
    export PYTHONPATH=/app/src:/app && \
    python -c \"
from src.deployment.api.tools.model_finder import find_model_pair
from pathlib import Path
onnx_path, checkpoint_path = find_model_pair(Path('/app/outputs'))
if onnx_path and checkpoint_path:
    import subprocess
    subprocess.run([
        'python', '-m', 'src.deployment.api.cli.run_api',
        '--onnx-model', str(onnx_path),
        '--checkpoint', str(checkpoint_path),
        '--host', '0.0.0.0',
        '--port', '8000'
    ])
else:
    print('No models found')
    exit(1)
    \"
  "
```

## Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: resume-ner-api
    ports:
      - "8000:8000"
    volumes:
      - ./outputs:/app/outputs
      - ./src:/app/src
      - ./config:/app/config
    environment:
      - PYTHONPATH=/app/src:/app
      - OCR_EXTRACTOR=easyocr
      - PDF_EXTRACTOR=pymupdf
    command: >
      conda run -n resume-ner-training python -m src.deployment.api.cli.run_api
      --onnx-model /app/outputs/conversion/local/<model_path>/model.onnx
      --checkpoint /app/outputs/final_training/local/<checkpoint_path>/checkpoint
      --host 0.0.0.0
      --port 8000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Run with:

```bash
docker-compose up -d
```

## Volume Mounts

### Required Mounts

- **Models and Checkpoints**: Mount your `outputs/` directory to `/app/outputs` in the container

  ```bash
  -v $(pwd)/outputs:/app/outputs
  ```

### Optional Mounts

- **Source Code** (for development): Mount `src/` for live code changes

  ```bash
  -v $(pwd)/src:/app/src
  ```

- **Configuration**: Mount `config/` for configuration changes

  ```bash
  -v $(pwd)/config:/app/config
  ```

## Environment Variables

| Variable      | Default         | Description                                    |
|---------------|-----------------|------------------------------------------------|
| `PYTHONPATH`   | `/app/src:/app` | Python path for imports                        |
| `OCR_EXTRACTOR`| `easyocr`       | OCR library (`easyocr` or `pytesseract`)      |
| `PDF_EXTRACTOR`| `pymupdf`       | PDF extractor (`pymupdf` or `pdfplumber`)     |
| `HOST`         | `0.0.0.0`       | API server host (use `0.0.0.0` for Docker)    |
| `PORT`         | `8000`          | API server port                                |

## Port Mapping

The API server runs on port 8000 inside the container. Map it to your host:

```bash
-p 8000:8000  # Map container port 8000 to host port 8000
-p 8080:8000  # Map container port 8000 to host port 8080
```

## Health Check

The API includes a health endpoint:

```bash
# Check health from host
curl http://localhost:8000/health

# Check health from inside container
docker exec resume-ner-api curl http://localhost:8000/health
```

## Troubleshooting

### Container Won't Start

1. **Check logs:**

   ```bash
   docker logs resume-ner-api
   ```

2. **Verify model paths:**

   ```bash
   docker exec resume-ner-api ls -la /app/outputs/conversion/
   docker exec resume-ner-api ls -la /app/outputs/final_training/
   ```

3. **Check conda environment:**

   ```bash
   docker exec resume-ner-api conda env list
   docker exec resume-ner-api conda run -n resume-ner-training python --version
   ```

### OCR Not Working

If OCR dependencies are missing:

1. **Verify installation:**

   ```bash
   docker exec resume-ner-api conda run -n resume-ner-training pip list | grep easyocr
   docker exec resume-ner-api conda run -n resume-ner-training pip list | grep pillow
   ```

2. **Reinstall if needed:**

   ```bash
   docker exec resume-ner-api conda run -n resume-ner-training pip install easyocr pillow
   ```

### Permission Issues

If you encounter permission issues with mounted volumes:

```bash
# Fix permissions (Linux/Mac)
docker exec resume-ner-api chown -R $(id -u):$(id -g) /app/outputs
```

### Out of Memory

If the container runs out of memory:

1. **Increase Docker memory limit** in Docker Desktop settings
2. **Use CPU-only PyTorch** by uncommenting `cpuonly` in `conda.yaml`:

   ```yaml
   - cpuonly  # CPU-only PyTorch installation
   ```

## Building for Production

### Optimize Image Size

1. **Use multi-stage build** (see Option 3 above)
2. **Remove build dependencies:**

   ```dockerfile
   RUN conda env create -f config/environment/conda.yaml && \
       conda clean -afy && \
       rm -rf /opt/conda/pkgs/*
   ```

3. **Use .dockerignore:**

   ```text
   .git
   .mypy_cache
   __pycache__
   *.pyc
   outputs/
   mlruns/
   .venv
   ```

### Security Best Practices

1. **Run as non-root user:**

   ```dockerfile
   RUN useradd -m -u 1000 appuser && \
       chown -R appuser:appuser /app
   USER appuser
   ```

2. **Use specific image tags** instead of `latest`
3. **Scan for vulnerabilities:**

   ```bash
   docker scan resume-ner-api:latest
   ```

## Example: Complete Workflow

```bash
# 1. Build the image
docker build -t resume-ner-api:latest .

# 2. Find your models (on host)
ONNX_MODEL=$(find outputs/conversion -name "model.onnx" -type f | head -1)
SPEC_HASH=$(echo "$ONNX_MODEL" | sed -n 's|.*\(spec-[a-f0-9]\{8\}_exec-[a-f0-9]\{8\}\).*|\1|p')
CHECKPOINT_DIR=$(find outputs/final_training -path "*${SPEC_HASH}*/checkpoint" -type d | head -1)

# 3. Run the container
docker run -d \
  --name resume-ner-api \
  -p 8000:8000 \
  -v $(pwd)/outputs:/app/outputs \
  resume-ner-api:latest \
  conda run -n resume-ner-training python -m src.deployment.api.cli.run_api \
    --onnx-model "$ONNX_MODEL" \
    --checkpoint "$CHECKPOINT_DIR" \
    --host 0.0.0.0 \
    --port 8000

# 4. Check health
curl http://localhost:8000/health

# 5. Test API
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "John Doe is a software engineer at Google. Email: john.doe@example.com"}'

# 6. View logs
docker logs -f resume-ner-api

# 7. Stop container
docker stop resume-ner-api
docker rm resume-ner-api
```
