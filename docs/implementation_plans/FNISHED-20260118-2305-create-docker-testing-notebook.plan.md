# Create Docker Testing Notebook

## Goal

Create a Jupyter notebook (`notebooks/docker_testing.ipynb`) to test the Resume NER API running in Docker containers, similar to `api_testing.ipynb`. The notebook should test Docker image building, container lifecycle, API functionality through Docker, Docker Compose, volume mounts, environment variables, and compare Docker vs local performance.

## Status

**Last Updated**: 2026-01-18

### Completed Steps
- ✅ Step 1: Create notebook structure and setup cells
- ✅ Step 2: Implement Docker image building tests
- ✅ Step 3: Implement Docker container lifecycle management
- ✅ Step 4: Implement API testing through Docker
- ✅ Step 5: Implement Docker Compose testing
- ✅ Step 6: Implement volume mount and environment variable tests
- ✅ Step 7: Implement performance comparison (Docker vs local)
- ✅ Step 8: Add helper functions and utilities
- ✅ Step 9: Add documentation and prerequisites section

### Pending Steps
- None - all steps completed

## Preconditions

- Docker and Docker Compose installed and running
- Access to trained models (ONNX model and checkpoint directory)
- Understanding of `api_testing.ipynb` structure and patterns
- Access to test fixtures from `tests/test_data/fixtures`

## Steps

### Step 1: Create notebook structure and setup cells

1. Create `notebooks/docker_testing.ipynb` with markdown header section
2. Add prerequisites section referencing `docs/docker_build.md`
3. Add setup cell with imports:
   - Standard library: `sys`, `Path`, `json`, `time`, `subprocess`, `typing`
   - Third-party: `requests`, `docker` (docker-py), `IPython.display`
   - Project imports: test fixtures, model finder utilities
4. Add configuration cell for Docker settings (image name, container name, ports, volumes)
5. Add helper function cell for Docker operations (build, run, stop, logs, health check)

**Success criteria**:
- `notebooks/docker_testing.ipynb` exists with proper structure
- All imports work without errors
- Configuration variables are clearly defined
- Helper functions are typed and documented

### Step 2: Implement Docker image building tests

1. Create section "1. Docker Image Building"
2. Add cell to test Dockerfile validation (syntax check)
3. Add cell to build Docker image with progress display
4. Add cell to verify image was created and show image details
5. Add cell to test image size and layer inspection
6. Add error handling for build failures

**Success criteria**:
- Image builds successfully from Dockerfile
- Build progress is displayed
- Image details are shown (size, layers, tags)
- Build errors are caught and displayed clearly

### Step 3: Implement Docker container lifecycle management

1. Create section "2. Container Lifecycle Management"
2. Add cell to find models (reuse `find_model_pair` from `api_testing.ipynb`)
3. Add cell to start container with proper volume mounts and model paths
4. Add cell to check container status (running, health, logs)
5. Add cell to stop and remove containers
6. Add helper function `manage_container()` for start/stop/restart operations

**Success criteria**:
- Container starts successfully with model paths
- Container health check passes
- Container logs are accessible
- Container can be stopped and removed cleanly
- Helper function works for all lifecycle operations

### Step 4: Implement API testing through Docker

1. Create section "3. API Testing Through Docker"
2. Reuse test patterns from `api_testing.ipynb`:
   - Single text prediction (`/predict`)
   - Single PDF file prediction (`/predict/file`)
   - Single image file prediction (`/predict/file`)
   - Batch text prediction (`/predict/batch`)
   - Batch file prediction (`/predict/file/batch`)
3. Add cells to test each endpoint with Docker container
4. Add entity visualization using `display_entities()` from `api_testing.ipynb`
5. Ensure API base URL points to Docker container (localhost:8000)

**Success criteria**:
- All API endpoints work through Docker container
- Entity extraction results match expected patterns
- Error handling works (e.g., missing OCR dependencies)
- Visualization displays entities correctly

### Step 5: Implement Docker Compose testing

1. Create section "4. Docker Compose Testing"
2. Add cell to validate `docker-compose.yml` syntax
3. Add cell to start services with `docker-compose up`
4. Add cell to check service status and health
5. Add cell to test API through Docker Compose
6. Add cell to stop services with `docker-compose down`
7. Add cell to test with different environment variable configurations

**Success criteria**:
- Docker Compose file validates successfully
- Services start and are healthy
- API works through Docker Compose
- Services can be stopped cleanly
- Environment variables are applied correctly

### Step 6: Implement volume mount and environment variable tests

1. Create section "5. Volume Mounts and Environment Variables"
2. Add cell to test required volume mounts (outputs directory)
3. Add cell to test optional volume mounts (src, config for development)
4. Add cell to test environment variables:
   - `OCR_EXTRACTOR` (easyocr vs pytesseract)
   - `PDF_EXTRACTOR` (pymupdf vs pdfplumber)
   - `PYTHONPATH`
5. Add cell to verify file access in container (check mounted volumes)
6. Add cell to test with different extractor combinations

**Success criteria**:
- Volume mounts work correctly
- Files are accessible in container
- Environment variables affect API behavior
- Different extractor configurations work

### Step 7: Implement performance comparison (Docker vs local)

1. Create section "6. Performance Comparison: Docker vs Local"
2. Add cell to start local API server (reuse `start_api_server_interactive` pattern)
3. Add cell to run same test cases on both Docker and local
4. Add cell to measure and compare:
   - Response latency
   - Processing time
   - Memory usage (if possible)
   - Startup time
5. Add cell to create comparison table/visualization
6. Add cell to analyze overhead (Docker vs local)

**Success criteria**:
- Both Docker and local servers run simultaneously
- Same test cases run on both
- Performance metrics are collected
- Comparison table shows differences
- Overhead analysis is meaningful

### Step 8: Add helper functions and utilities

1. Create helper functions section with reusable utilities:
   - `build_docker_image()` - Build image with progress
   - `start_docker_container()` - Start container with model discovery
   - `stop_docker_container()` - Stop and remove container
   - `check_container_health()` - Health check via Docker API
   - `get_container_logs()` - Fetch and display logs
   - `test_docker_api()` - Run API test through Docker
   - `compare_docker_vs_local()` - Performance comparison
2. Ensure all functions have type hints and docstrings
3. Reuse patterns from `api_testing.ipynb` where applicable

**Success criteria**:
- All helper functions are typed and documented
- Functions follow existing patterns from `api_testing.ipynb`
- Functions are reusable across notebook cells
- Error handling is comprehensive

### Step 9: Add documentation and prerequisites section

1. Add comprehensive markdown section at top with:
   - Purpose and scope
   - Prerequisites (Docker, models, etc.)
   - Quick start guide
   - Link to `docs/docker_build.md`
   - Troubleshooting tips
2. Add inline documentation in code cells explaining Docker-specific considerations
3. Add notes about differences from local API testing
4. Add cleanup section at end (stop containers, remove images if needed)

**Success criteria**:
- Documentation is clear and complete
- Prerequisites are clearly stated
- Quick start guide works
- Troubleshooting section is helpful
- Cleanup instructions are provided

## Success Criteria (Overall)

- ✅ Notebook `notebooks/docker_testing.ipynb` exists and is functional
- ✅ All Docker operations (build, run, stop) work correctly
- ✅ API testing through Docker matches `api_testing.ipynb` functionality
- ✅ Docker Compose testing works
- ✅ Volume mounts and environment variables are tested
- ✅ Performance comparison provides meaningful insights
- ✅ Helper functions are reusable and well-documented
- ✅ Documentation is complete and helpful
- ✅ Notebook follows same structure and patterns as `api_testing.ipynb`
- ✅ All cells execute without errors (when prerequisites are met)

## Notes

- Reuse as much code as possible from `api_testing.ipynb` (test fixtures, entity display, API request patterns)
- Use `docker` Python library for programmatic Docker control
- Ensure proper cleanup of containers and images in cleanup section
- Consider adding tests for edge cases (missing models, wrong paths, etc.)
- Follow notebook rules: keep notebooks thin, extract reusable logic to `src/` if needed

