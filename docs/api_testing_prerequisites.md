# API Testing Notebook - Prerequisites

This notebook tests the Resume NER API with actual test files and visualizes extracted entities.

**Note:** For comprehensive error handling and edge case testing, see `tests/integration/api/test_api_local_server.py`.

## Quick Start

### 1. Find Models

**Option A: Using find commands (Simplest)**

```bash
# Find latest ONNX model
ONNX_MODEL=$(find outputs/conversion -name "model.onnx" -type f | head -1)
echo "ONNX Model: $ONNX_MODEL"

# Extract spec hash and find matching checkpoint
SPEC_HASH=$(echo "$ONNX_MODEL" | sed -n 's|.*\(spec-[a-f0-9]\{8\}_exec-[a-f0-9]\{8\}\).*|\1|p')
CHECKPOINT_DIR=$(find outputs/final_training -path "*${SPEC_HASH}*/checkpoint" -type d | head -1)
echo "Checkpoint: $CHECKPOINT_DIR"
```

**Option B: Using Python (in notebook)**

After running the setup cell in the notebook:

```python
find_and_display_models(verbose=True)  # Shows available models
```

### 2. Start Server

**Prerequisites:** Ensure dependencies are installed:
```bash
pip install python-multipart  # Required for file upload endpoints
```

**Recommended: Terminal**

```bash
# Activate environment
source /opt/conda/etc/profile.d/conda.sh
conda activate resume-ner-training

# Set PYTHONPATH to include src directory (required for infrastructure imports)
export PYTHONPATH="$(pwd)/src:$(pwd)"

python -m src.deployment.api.cli.run_api \
  --onnx-model <onnx_path> \
  --checkpoint <checkpoint_path>
```

**Note:** If `conda activate` doesn't work in your shell, use:
```bash
source $(conda info --base)/etc/profile.d/conda.sh
conda activate resume-ner-training
```

**Alternative: Python (in notebook)**

After running the setup cell:

```python
start_api_server_interactive()  # Auto-discovers models and starts server
```

### 3. Verify Server

```python
from src.deployment.api.tools.server_launcher import check_server_health

check_server_health()  # Returns True if healthy
```

### 4. Terminate Server

**Option A: Python (Background Process)**

If you started the server using `start_api_server()` with `background=True`, you'll have a process object:

```python
# Store the process when starting
process = start_api_server(onnx_path, checkpoint_path, background=True)

# Later, terminate it
process.terminate()  # Graceful shutdown
# or
process.kill()  # Force kill
```

**Option B: Terminal**

If running in foreground terminal:

- Press `Ctrl+C` to stop the server

If running in background:

```bash
# Find the process
ps aux | grep "run_api"

# Kill by PID (replace <PID> with actual process ID)
kill <PID>

# Or force kill
kill -9 <PID>
```

**Option C: Using Port**

```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill

# Or force kill
lsof -ti:8000 | xargs kill -9
```

## Directory Structure

- **ONNX models**: `outputs/conversion/local/{model}/{spec_hash}/v1/{conv_hash}/onnx_model/model.onnx`
- **Checkpoints**: `outputs/final_training/local/{model}/{spec_hash}/v1/checkpoint`

## Helper Functions

The notebook provides helper functions:

- `find_and_display_models()` - Find and display available models
- `start_api_server_interactive()` - Start server with auto-discovery
- `verify_server_running()` - Check server health

See the notebook setup cell for details.
