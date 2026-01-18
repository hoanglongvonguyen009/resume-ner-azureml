# Plan: Update API Testing Notebook with Latest Scripts from src

## Goal

Update `notebooks/api_testing.ipynb` to use Python utilities from `src/` instead of hardcoded bash commands, making it more maintainable, portable, and aligned with the codebase structure.

## Status

**Last Updated**: 2026-01-18

**Current State**:
- ⏳ Notebook uses bash commands for finding models and starting server
- ⏳ Hardcoded paths that may not match actual outputs structure
- ⏳ No reusable Python utilities for model discovery
- ⏳ Manual path extraction using bash/sed commands

### Completed Steps
- ✅ Step 1: Create Python utility for finding ONNX models and checkpoints
- ✅ Step 2: Create Python utility for starting API server programmatically
- ✅ Step 3: Update notebook prerequisites section with Python code
- ✅ Step 4: Add helper functions to notebook setup cell
- ✅ Step 5: Update all references to use Python utilities

### Pending Steps
- ⏳ Step 6: Test notebook execution with new utilities

## Preconditions

- `src/deployment/api/cli/run_api.py` exists and works
- Outputs directory structure follows pattern: `outputs/{conversion,final_training}/local/{model_name}/{spec_hash}/...`
- Notebook can import from `src/` modules

## Steps

### Step 1: Create Python Utility for Finding Models

**Location**: `src/deployment/api/tools/model_finder.py`

**What to do**:
1. Create new file `src/deployment/api/tools/model_finder.py`
2. Implement functions:
   - `find_latest_onnx_model(outputs_dir: Path) -> Optional[Path]`: Find latest ONNX model in `outputs/conversion`
   - `find_matching_checkpoint(onnx_path: Path, outputs_dir: Path) -> Optional[Path]`: Find checkpoint matching ONNX model's spec hash
   - `find_model_pair(outputs_dir: Path) -> tuple[Optional[Path], Optional[Path]]`: Find matching ONNX and checkpoint pair
   - `list_available_models(outputs_dir: Path) -> dict[str, list[Path]]`: List all available models and checkpoints
3. Extract spec hash from path using Python regex (not bash/sed)
4. Handle edge cases (no models found, multiple models, etc.)
5. Add proper type hints and docstrings

**Success criteria**:
- `src/deployment/api/tools/model_finder.py` exists with all functions
- `uvx mypy src/deployment/api/tools/model_finder.py` passes with 0 errors
- Functions handle the actual outputs directory structure
- Functions return `None` when models not found (no exceptions)

### Step 2: Create Python Utility for Starting API Server

**Location**: `src/deployment/api/tools/server_launcher.py`

**What to do**:
1. Create new file `src/deployment/api/tools/server_launcher.py`
2. Implement functions:
   - `start_api_server(onnx_path: Path, checkpoint_dir: Path, host: str = "0.0.0.0", port: int = 8000, background: bool = False) -> subprocess.Popen | None`: Start API server
   - `check_server_health(base_url: str = "http://localhost:8000", timeout: int = 5) -> bool`: Check if server is running
   - `get_server_info(base_url: str = "http://localhost:8000") -> dict[str, Any]`: Get server info
3. Use `subprocess` to launch `python -m src.deployment.api.cli.run_api`
4. Support both foreground and background modes
5. Add proper error handling and logging

**Success criteria**:
- `src/deployment/api/tools/server_launcher.py` exists with all functions
- `uvx mypy src/deployment/api/tools/server_launcher.py` passes with 0 errors
- Functions can start server in both foreground and background modes
- Health check function works correctly

### Step 3: Update Notebook Prerequisites Section

**Location**: `notebooks/api_testing.ipynb` (Cell 0 - markdown)

**What to do**:
1. Replace bash commands with Python code examples
2. Show how to use `model_finder` utilities
3. Show how to use `server_launcher` utilities
4. Keep markdown explanations but reference Python functions
5. Update paths to reflect actual structure (`src.deployment.api` not `src.api`)

**Success criteria**:
- Prerequisites section shows Python code instead of bash
- Code examples use `from src.deployment.api.tools.model_finder import ...`
- Code examples use `from src.deployment.api.tools.server_launcher import ...`
- Instructions are clear for codespace users

### Step 4: Add Helper Functions to Notebook Setup Cell

**Location**: `notebooks/api_testing.ipynb` (Cell 2 - after imports)

**What to do**:
1. Add new code cell after imports cell
2. Import model finder and server launcher utilities
3. Add helper functions:
   - `find_and_display_models()`: Find and print available models
   - `start_api_server_interactive()`: Interactive function to start server
   - `verify_server_running()`: Check if server is running
4. Make functions user-friendly with clear output messages
5. Handle errors gracefully with helpful error messages

**Success criteria**:
- New cell exists with helper functions
- Functions can be called interactively in notebook
- Functions provide clear feedback to user
- Functions handle missing models gracefully

### Step 5: Update All References to Use Python Utilities

**Location**: `notebooks/api_testing.ipynb` (throughout)

**What to do**:
1. Review all cells for bash command references
2. Replace any remaining bash commands with Python equivalents
3. Update any hardcoded paths to use `model_finder` utilities
4. Ensure consistency in how models are discovered
5. Update any documentation strings that reference bash commands

**Success criteria**:
- No bash commands in notebook cells (except in markdown examples)
- All model discovery uses Python utilities
- All server startup uses Python utilities
- Notebook is self-contained (no external bash scripts needed)

### Step 6: Test Notebook Execution

**What to do**:
1. Run notebook cells in order
2. Verify model finder functions work with actual outputs structure
3. Verify server launcher can start server
4. Verify health check works
5. Test with different scenarios:
   - Models exist
   - No models found
   - Multiple models available
   - Server already running
   - Server not running

**Success criteria**:
- All notebook cells execute without errors
- Model finder finds correct models
- Server launcher starts server successfully
- Health check returns correct status
- Error cases handled gracefully

## Success Criteria (Overall)

- ✅ Python utilities exist in `src/deployment/api/tools/` for model finding and server launching
- ✅ Notebook uses Python code instead of bash commands
- ✅ Notebook is more maintainable and aligned with codebase structure
- ✅ All functions have proper type hints and pass mypy
- ✅ Notebook works correctly in codespace environment
- ✅ Error handling is robust and user-friendly

## Notes

- Keep backward compatibility: Users can still run bash commands manually if preferred
- Python utilities should be reusable by other scripts/notebooks
- Follow existing code patterns in `src/deployment/api/`
- Use `Path` objects consistently (not strings) for file paths
- Add proper logging for debugging

## Related Files

- `notebooks/api_testing.ipynb` - Target notebook to update
- `src/deployment/api/cli/run_api.py` - CLI script for starting server
- `src/deployment/api/config.py` - API configuration
- `src/deployment/conversion/orchestration.py` - Contains `_find_onnx_model` function (reference)
- `outputs/` - Directory structure to understand

