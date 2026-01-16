# Test Data Tests

Test data fixtures and utilities for FastAPI inference server tests.

## TL;DR / Quick Start

This module provides deterministic test data (text, PDF, PNG files) for API testing. Use the `fixtures.py` module to access test data programmatically.

```bash
# No tests to run - this is a test data module
# Import fixtures in your tests:
from tests.test_data.fixtures import get_text_fixture, get_file_fixture
```

## Overview

The `test_data/` module provides:

- **Text fixtures**: Standard resume text samples, edge cases (empty, unicode, long text)
- **File fixtures**: PDF and PNG versions of test resumes (identical content)
- **Batch fixtures**: Pre-configured batches for batch processing tests
- **Generation utilities**: Scripts to generate test files from text content

All test data is deterministic, version-controlled, and designed for FastAPI inference server testing.

## Test Structure

- `fixtures.py`: Python module providing programmatic access to test data
- `generate_test_files.py`: Script to generate PDF and PNG files from text
- `test_resume_ner_*.pdf/png`: Standard test files (10 files)
- `test_resume*.pdf/png`: Larger test files for performance testing (3 files)

## Running Tests

This module does not contain tests - it provides test data for other test modules. To verify test data works correctly, run tests that use it:

```bash
# Run API tests that use test data
uvx pytest tests/api/ -v
uvx pytest tests/integration/api/ -v
```

## Test Fixtures and Helpers

### Available Fixtures

#### Text Fixtures

- `text_1` through `text_10`: Standard resume text samples
- `text_empty`: Empty string
- `text_unicode`: Unicode characters
- `text_long`: Very long text (10,000+ characters)
- `text_special`: Special characters (email, phone, URL)

#### File Fixtures

- `file_1` through `file_10`: Standard test files (PDF and PNG)
- `file_resume_1`, `file_resume_2`, `file_resume_3`: Larger test files

#### Batch Fixtures

- `batch_text_small`: 3 text items
- `batch_text_medium`: 5 text items
- `batch_text_large`: 10 text items
- `batch_text_empty`: Empty batch
- `batch_text_mixed`: Mixed valid/invalid items
- `batch_file_small`: 3 files
- `batch_file_medium`: 5 files
- `batch_file_large`: 10 files
- `batch_file_mixed_types`: Mixed PDF/PNG files

### Usage Examples

Use the `fixtures.py` module to access test data in tests:

```python
from tests.test_data.fixtures import (
    get_text_fixture,
    get_file_fixture,
    get_batch_text_fixture,
    get_batch_file_fixture,
)

# Get text fixture
text = get_text_fixture("text_1")

# Get file fixture
pdf_path = get_file_fixture("file_1", "pdf")
png_path = get_file_fixture("file_1", "png")

# Get batch fixtures
texts = get_batch_text_fixture("batch_text_small")
files = get_batch_file_fixture("batch_file_small", "pdf")
```

## Generating Test Files

If test files are missing, generate them using:

```bash
cd tests/test_data
python generate_test_files.py
```

This requires:
- `reportlab` or `fpdf2` for PDF generation
- `Pillow` for PNG generation

Install dependencies:

```bash
pip install -r requirements_generate.txt
```

## File Content

Each pair of PDF/PNG files (e.g., `test_resume_ner_1.pdf` and `test_resume_ner_1.png`) contains identical text content. This allows testing consistency across different file format handling.

The text content matches the corresponding text fixtures in `fixtures.py`:
- `test_resume_ner_1.*` contains `text_1` content
- `test_resume_ner_2.*` contains `text_2` content
- etc.

## Validation

To validate that all required test files exist:

```python
from tests.test_data.fixtures import validate_all_fixtures

result = validate_all_fixtures()
print(f"Missing: {result['missing']}")
print(f"Found: {len(result['found'])} files")
```

## Determinism Requirements

- All test files are version-controlled
- Files are generated deterministically from known text content
- Same input produces same output (within floating-point tolerance)
- No external network dependencies required

## What Is Tested

This module does not contain tests - it provides test data. However, test data is validated through its usage in other test modules:

- ✅ Text fixtures provide valid resume text samples
- ✅ File fixtures provide valid PDF and PNG files
- ✅ Batch fixtures provide valid batch configurations
- ✅ File generation produces deterministic output

## Configuration

### Generating Test Files

If test files are missing, generate them using:

```bash
cd tests/test_data
python generate_test_files.py
```

This requires:
- `reportlab` or `fpdf2` for PDF generation
- `Pillow` for PNG generation

Install dependencies:

```bash
pip install -r requirements_generate.txt
```

### Validation

To validate that all required test files exist:

```python
from tests.test_data.fixtures import validate_all_fixtures

result = validate_all_fixtures()
print(f"Missing: {result['missing']}")
print(f"Found: {len(result['found'])} files")
```

## Dependencies

- **PDF generation**: `reportlab` or `fpdf2`
- **PNG generation**: `Pillow`
- **File content**: Each pair of PDF/PNG files contains identical text content, matching corresponding text fixtures in `fixtures.py`

## Related Test Modules

- **Downstream consumers** (test modules that use this test data):
  - [`../api/README.md`](../api/README.md) - API tests use test data fixtures
  - [`../integration/api/README.md`](../integration/api/README.md) - Integration API tests use test data

## References

See `docs/qa/QA_Local_FastAPI_Inference_Server/Appendices/test_data_descriptions.md` for detailed specifications of all test data fixtures.

