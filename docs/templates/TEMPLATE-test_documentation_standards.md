# Test Documentation Standards

This document defines the standards, template, and processes for creating technical documentation (README.md) for all test modules in `tests/`.

## File Location

- Each test module should have a `README.md` at its root level
- Path: `tests/<module>/README.md`
- Submodules: `tests/<module>/<submodule>/README.md`

## Required Sections

### Minimum Required (All Test Modules)

1. **Title** - Test module name as H1 (e.g., "HPO Tests")
2. **TL;DR / Quick Start** - Required for complex test modules, recommended for all
3. **Overview** - 1-2 paragraphs describing what this test module covers (use bullet points)
4. **Test Structure** - List key test files and folders only (not every test function)
5. **Running Tests** - At least one working test execution example
6. **What Is Tested** - Clear list of test coverage
7. **Related Test Modules** - Links to related test documentation

### Optional Sections (Include Only When Applicable)

- **Test Categories** - For test modules with multiple test types (unit, integration, e2e)
- **Test Fixtures and Helpers** - For test modules that use fixtures or helpers
- **What Is Not Tested** - For documenting gaps or limitations
- **Advanced Execution** - For complex test execution scenarios
- **Configuration** - For tests that require configuration
- **Dependencies** - For tests with special dependencies
- **Troubleshooting** - For test modules with known issues or setup complexity
- **Test Examples** - For test modules with complex test patterns

**Important**: Do not create empty headings for optional sections.

## Documentation Template

### For Simple Test Modules (fixtures, shared, test_data)

Simple test modules with focused responsibilities should have concise documentation:

```markdown
# [Module Name] Tests

[One-sentence overview]

## TL;DR / Quick Start

[1-2 sentence summary + minimal test execution example]

```bash
uvx pytest tests/module/ -v
```

## Overview

[1-2 paragraphs: what this test module covers, its role. Use bullet points for clarity.]

## Test Structure

- `file.py`: [Main purpose]
- `subfolder/`: [Purpose of folder]

## Running Tests

```bash
# Run all tests in this module
uvx pytest tests/module/ -v

# Run specific test file
uvx pytest tests/module/test_file.py -v
```

## What Is Tested

- ✅ [Feature/component 1]
- ✅ [Feature/component 2]

## Related Test Modules

- [`../related_module/README.md`](../related_module/README.md) - [Brief description]
```

### For Complex Test Modules (workflows, hpo, benchmarking)

Complex test modules with multiple test types should have hierarchical documentation:

```markdown
# [Module Name] Tests

[One-sentence overview]

## TL;DR / Quick Start

**[Required for complex test modules]**

[1-2 sentence summary + minimal test execution example]

```bash
# Run all tests in this module
uvx pytest tests/module/ -v

# Run specific category
uvx pytest tests/module/unit/ -v
uvx pytest tests/module/integration/ -v
```

## Overview

[1-2 paragraphs: what this test module covers, test architecture. Use bullet points for clarity.]

## Test Structure

This test module is organized into the following categories:

- `unit/`: [Purpose and responsibility]
- `integration/`: [Purpose and responsibility]
- `e2e/`: [Purpose and responsibility]

## Test Categories

- **Unit Tests** (`unit/`): [What unit tests cover - fast, isolated tests]
- **Integration Tests** (`integration/`): [What integration tests cover - tests with real components]
- **E2E Tests** (`e2e/`): [What E2E tests cover - full workflow tests]

## Running Tests

### Basic Execution

[Common test execution patterns]

```bash
# Run all tests in this module
uvx pytest tests/module/ -v

# Run with coverage
uvx pytest tests/module/ --cov=src.module --cov-report=html

# Run specific category
uvx pytest tests/module/unit/ -v
uvx pytest tests/module/integration/ -v
```

### Advanced Execution

[Complex scenarios, markers, environment variables]

```bash
# Run with specific markers
uvx pytest tests/module/ -m "slow" -v

# Run with environment variables
E2E_USE_REAL_TRAINING=true uvx pytest tests/module/ -v
```

## Test Fixtures and Helpers

### Available Fixtures

[Document key fixtures used in this module]

- `fixture_name`: [Description of what it provides]
- `another_fixture`: [Description]

### Shared Helpers

[Document helper functions or utilities]

- `helper_function()`: [Description]

See [`../fixtures/README.md`](../fixtures/README.md) for shared fixtures.

## What Is Tested

[Clear list of what functionality is covered by these tests]

- ✅ [Feature/component 1]
- ✅ [Feature/component 2]
- ✅ [Edge case 1]

## What Is Not Tested

[Explicitly document gaps, limitations, or known untested areas]

- ❌ [Feature not tested - reason]
- ⚠️ [Feature partially tested - limitations]

## Configuration

[Test configuration files, environment variables, setup requirements]

## Related Test Modules

- [`../related_module/README.md`](../related_module/README.md) - [Description]
```

## Test Execution Example Format

- Use bash syntax highlighting: ` ```bash `
- Include full `uvx pytest` commands
- **Examples must be copy/paste runnable** or verified commands that work
- Add comments explaining non-obvious parts
- Reference actual test files from the module
- **Enforcement**: Examples should be tested via:
  - Manual smoke check (copy/paste and run)
  - Or verified `uvx pytest` commands

## Cross-Reference Format

- Use relative paths: `[../module/README.md](../module/README.md)`
- Include brief description: `[Module Name](../module/README.md) - Brief description`
- Group by relationship type (dependencies, related, consumers)

## Writing Style

- **Concise but complete**: Cover essentials without verbosity
- **Example-driven**: Show test execution before explaining theory
- **Practical focus**: Emphasize "how to run tests" and "what is tested" over "how tests work internally"
- **Consistent terminology**: Use test terms consistently (unit, integration, e2e, fixture, marker)
- **Avoid fluff**: 1-2 paragraphs max for Overview, use bullet points

## Test Documentation Intake Process

Before writing a test module README, perform this **repeatable intake** to prevent guessing:

### 1. Scan Test Files

```bash
# List all test files in module
find tests/module -name "test_*.py" | sort

# Count test functions
grep -r "^def test_\|^async def test_" tests/module/ | wc -l

# List test categories (unit, integration, e2e)
find tests/module -type d -name "unit\|integration\|e2e" | sort
```

### 2. Identify Test Patterns

```bash
# List fixtures used
grep -r "@pytest.fixture\|@pytest.mark.fixture" tests/module/ | head -20

# List markers used
grep -r "@pytest.mark\." tests/module/ | cut -d: -f2 | sort -u

# List conftest files
find tests/module -name "conftest.py"
```

### 3. Map Dependencies

**Inbound** (what fixtures/helpers this uses):
```bash
grep -r "from fixtures\|from shared\|from test_data" tests/module/ | cut -d: -f1 | sort -u
```

**Outbound** (what source modules this tests):
```bash
grep -r "^from src\.\|^import src\." tests/module/ | cut -d: -f2 | sort -u
```

### 4. Document Findings

Create a brief intake note:
- Test files: [list]
- Test categories: [unit, integration, e2e]
- Fixtures used: [list]
- Source modules tested: [list]
- Test coverage: [what is tested]

This intake makes "What Is Tested" and "Test Fixtures and Helpers" sections real and accurate.

## Per-Module Definition of Done

Each test module README is considered complete when:

- [ ] Has minimum required sections (Title, TL;DR/Quick Start, Overview, Test Structure, Running Tests, What Is Tested, Related Test Modules)
- [ ] Contains at least one working test execution example (copy/paste runnable or verified command)
- [ ] Has Test Categories section (if module has multiple test types)
- [ ] Has Test Fixtures and Helpers section (if module uses fixtures)
- [ ] Has What Is Tested section (clear list of coverage)
- [ ] Has What Is Not Tested section (if there are known gaps)
- [ ] Has Related Test Modules links (all links are valid)
- [ ] Test Structure lists only key test files and folders (not exhaustive function dumps)
- [ ] Overview is 1-2 paragraphs with bullet points (no fluff)
- [ ] All test execution examples have been smoke-tested (copy/paste or command verified)
- [ ] Cross-references are accurate and use relative paths

## Test Structure Guidelines

**List key test files and folders only**, not every test function. Optionally note "where to add X" for common extension points.

### Good Examples

```markdown
## Test Structure

- `test_hpo_workflow.py`: E2E HPO workflow tests
- `unit/`: Unit tests for HPO components (search space, trial selection)
- `integration/`: Integration tests with real components (sweep execution, checkpoint resume)
- `conftest.py`: Module-specific fixtures
```

### Avoid

```markdown
## Test Structure

- `test_hpo_workflow.py`
- `unit/test_search_space.py`
- `unit/test_trial_selection.py`
- `integration/test_sweep_execution.py`
- `integration/test_checkpoint_resume.py`
- `integration/test_refit_training.py`
- `conftest.py`
...
```

## Test Execution Example Requirements

All test execution examples must be verified before documentation is considered complete:

1. **Copy/paste runnable examples**: Test by copying and running in a clean environment
2. **Pytest commands**: Verify `uvx pytest` commands work as documented
3. **Environment variables**: Ensure environment variable examples are correct
4. **Markers**: Verify pytest markers work as documented

If an example cannot be tested (e.g., requires specific environment setup), document the reason clearly.

## What Is Tested Guidelines

The "What Is Tested" section should be:
- **Specific**: List actual features/components tested, not vague descriptions
- **Complete**: Cover all major test categories in the module
- **Clear**: Use checkmarks (✅) for tested items
- **Organized**: Group related items together

### Good Example

```markdown
## What Is Tested

- ✅ HPO search space generation and validation
- ✅ Trial selection and execution
- ✅ Checkpoint resume functionality
- ✅ Early termination logic
- ✅ MLflow tracking integration
- ✅ Path structure validation
```

### Avoid

```markdown
## What Is Tested

- HPO functionality
- Various edge cases
- Integration with other components
```

## What Is Not Tested Guidelines

The "What Is Not Tested" section should:
- **Be explicit**: Clearly state what is not tested and why
- **Use symbols**: Use ❌ for not tested, ⚠️ for partially tested
- **Provide context**: Explain reasons for gaps (if known)

### Good Example

```markdown
## What Is Not Tested

- ❌ Azure ML compute target provisioning (requires Azure ML workspace)
- ⚠️ Large-scale HPO sweeps (only small sweeps tested for CI speed)
- ❌ Distributed training (not supported in current implementation)
```

## Template Validation

This template has been validated against the existing `tests/README.md` to ensure consistency:

### Validation Checklist

- ✅ **Structure alignment**: Template sections match patterns in `tests/README.md`
- ✅ **Command format**: Uses `uvx pytest` consistently (matches project conventions)
- ✅ **Test organization**: Supports feature-based organization (workflows, hpo, benchmarking, etc.)
- ✅ **Execution examples**: Format matches existing examples in `tests/README.md`
- ✅ **Coverage documentation**: "What Is Tested" format aligns with existing documentation
- ✅ **Cross-references**: Relative path format matches existing link patterns
- ✅ **Writing style**: Concise, example-driven approach matches existing documentation

### Reference Example

See `tests/README.md` for a comprehensive example that follows these standards:

- Clear test structure documentation
- Multiple test execution examples
- Test coverage clearly documented
- Related modules documented
- Troubleshooting section included

The existing `tests/README.md` demonstrates:
- Feature-based test organization (workflows, hpo, benchmarking, etc.)
- Environment variable usage (`E2E_USE_REAL_TRAINING`, `E2E_TEST_SCOPE`)
- Test category documentation (unit, integration, e2e)
- Configuration documentation
- Troubleshooting guidance

