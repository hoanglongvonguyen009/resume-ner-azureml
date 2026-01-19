# Remove Unused Fallbacks and Redundant Logic from Docker Testing Notebook

## Goal

Clean up `notebooks/docker_testing.ipynb` by removing:
1. Unused imports (json, subprocess, pandas, IPython.display, ContainerError)
2. Unused function imports (find_latest_onnx_model, find_matching_checkpoint, list_available_models, check_server_health, get_server_info, start_api_server, wait_for_server)
3. Unused variables (SRC_DIR, CONFIG_DIR)
4. Redundant port checking logic (duplicated in start_docker_container function)
5. Any remaining fragments from removed functions

## Status

**Last Updated**: 2026-01-19

### Completed Steps
- ✅ Step 1: Audit unused imports and variables
- ✅ Step 2: Remove unused imports from Cell 3
- ✅ Step 3: Remove unused variables from Cell 4
- ✅ Step 4: Remove redundant port check from Cell 12 (verified: already clean)
- ✅ Step 5: Verify notebook still works correctly

### Pending Steps
- None - all steps completed

## Preconditions

- Docker testing notebook exists at `notebooks/docker_testing.ipynb`
- Notebook has been tested and is functional
- All helper functions are defined and working

## Steps

### Step 1: Audit Unused Imports and Variables

Identify all unused imports and variables in the notebook.

**Actions:**
1. Review Cell 3 (index 2) imports:
   - Check if `json` is used anywhere in the notebook
   - Check if `subprocess` is used (only in commented code in Cell 28)
   - Check if `pandas` is used
   - Check if `IPython.display` (display, Markdown, JSON) is used
   - Check if `ContainerError` from docker.errors is used
   - Check if model_finder imports are all used (find_latest_onnx_model, find_matching_checkpoint, list_available_models)
   - Check if server_launcher imports are all used (check_server_health, get_server_info, start_api_server, wait_for_server)

2. Review Cell 4 (index 3) variables:
   - Check if `SRC_DIR` is used anywhere
   - Check if `CONFIG_DIR` is used anywhere

3. Review Cell 12 (index 12) for redundant logic:
   - Check if port availability check is duplicated (start_docker_container already handles this)

**Success criteria:**
- List of unused imports documented
- List of unused variables documented
- Redundant logic patterns identified

### Step 2: Remove Unused Imports from Cell 3

Clean up the import statements in Cell 3 to only include what's actually used.

**Actions:**
1. Remove `import json` (not used)
2. Remove `import subprocess` (only used in commented code)
3. Remove `from IPython.display import display, Markdown, JSON` (not used)
4. Remove `import pandas as pd` (not used)
5. Remove `ContainerError` from `from docker.errors import` (not used)
6. Update `from src.deployment.api.tools.model_finder import` to only include `find_model_pair`
7. Remove entire `from src.deployment.api.tools.server_launcher import` block (none of these are used)

**Success criteria:**
- Cell 3 only contains imports that are actually used
- Notebook still executes Cell 3 without errors
- No import errors when running subsequent cells

### Step 3: Remove Unused Variables from Cell 4

Remove unused variable definitions from Cell 4.

**Actions:**
1. Remove `SRC_DIR = project_root / "src"` (not used)
2. Remove `CONFIG_DIR = project_root / "config"` (not used)

**Success criteria:**
- Cell 4 only contains variables that are actually used
- Notebook still executes Cell 4 without errors
- No NameError exceptions in subsequent cells

### Step 4: Remove Redundant Port Check from Cell 12

Remove the redundant port availability check that duplicates logic in `start_docker_container()`.

**Actions:**
1. Remove the manual port check block:
   - `# Check port availability first`
   - `port_available, conflicting_container = check_port_available(...)`
   - `if not port_available:` block with print statements
2. Keep the `start_docker_container()` call with `force_port=True` (this already handles port conflicts)

**Success criteria:**
- Cell 12 no longer has redundant port checking
- Container startup still works correctly
- Port conflicts are still handled by `start_docker_container()` function

### Step 5: Verify Notebook Still Works Correctly

Test the cleaned notebook to ensure all functionality still works.

**Actions:**
1. Execute all cells in order from Cell 1 to Cell 7 (setup and configuration)
2. Verify Docker image verification works (Cell 8-9)
3. Verify model finding works (Cell 11)
4. Verify container startup works (Cell 12)
5. Verify API testing cells work (Cells 16-25)
6. Check for any NameError, ImportError, or AttributeError exceptions

**Success criteria:**
- All cells execute without errors
- Docker container can be started successfully
- API endpoints can be tested through the container
- No functionality is broken

## Success Criteria (Overall)

- ✅ All unused imports removed from Cell 3
- ✅ All unused variables removed from Cell 4
- ✅ Redundant port check removed from Cell 12
- ✅ Notebook executes all cells without errors
- ✅ Docker container functionality works correctly
- ✅ API testing through Docker works correctly
- ✅ Code is cleaner and easier to maintain

## Notes

- The `build_docker_image()` function was already removed in a previous cleanup
- The `check_port_available()` function is still needed (used by `start_docker_container()`)
- The `start_docker_container()` function already handles port conflicts internally, so manual checking is redundant
- Some imports like `subprocess` appear in Cell 28 but only in commented code - safe to remove

## Related Files

- `notebooks/docker_testing.ipynb` - Main file to clean up
- `src/deployment/api/tools/model_finder.py` - Source of model_finder imports
- `src/deployment/api/tools/server_launcher.py` - Source of server_launcher imports (unused)

