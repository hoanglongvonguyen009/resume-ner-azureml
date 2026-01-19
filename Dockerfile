# Dockerfile for Resume NER API Server
# Build from conda environment definition

FROM continuumio/miniconda3:latest

WORKDIR /app

# Copy conda environment file
COPY config/environment/conda.yaml /app/config/environment/conda.yaml

# Create conda environment from yaml
# Note: This may take 10-15 minutes due to PyTorch and ML dependencies
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

# Default command (should be overridden with model paths)
# Users should provide --onnx-model and --checkpoint arguments
CMD ["conda", "run", "-n", "resume-ner-training", "python", "-m", "src.deployment.api.cli.run_api", "--help"]

