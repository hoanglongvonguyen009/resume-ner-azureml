# Master Plan: Technical Documentation for All Modules

## Goal

Create comprehensive technical documentation (README.md) for each module in `src/` to:
1. **Improve developer onboarding**: Clear understanding of module purpose, structure, and usage
2. **Enable code reuse**: Document public APIs, utilities, and integration points
3. **Maintain consistency**: Standardized documentation format across all modules
4. **Support maintenance**: Clear module boundaries, dependencies, and responsibilities

## Status

**Last Updated**: 2026-01-20

**Current State**:
- ✅ `src/benchmarking/README.md` exists (comprehensive example)
- ✅ `src/evaluation/benchmarking/README.md` exists
- ✅ `docs/TEMPLATE-documentation_standards.md` exists (template and standards)
- ✅ `src/core/README.md` exists
- ✅ `src/common/README.md` exists
- ✅ `src/data/README.md` exists
- ✅ `src/training/README.md` exists
- ✅ `src/training/core/README.md` exists
- ✅ `src/training/hpo/README.md` exists
- ✅ `src/training/execution/README.md` exists
- ✅ `src/infrastructure/README.md` exists
- ✅ `src/infrastructure/config/README.md` exists
- ✅ `src/infrastructure/paths/README.md` exists
- ✅ `src/infrastructure/tracking/README.md` exists
- ✅ `src/infrastructure/naming/README.md` exists
- ✅ `src/infrastructure/platform/README.md` exists
- ✅ `src/orchestration/README.md` exists
- ✅ `src/orchestration/jobs/README.md` exists
- ✅ `src/evaluation/README.md` exists
- ✅ `src/evaluation/selection/README.md` exists
- ✅ `src/evaluation/benchmarking/README.md` exists (already existed)
- ✅ `src/deployment/README.md` exists
- ✅ `src/deployment/api/README.md` exists
- ✅ `src/deployment/conversion/README.md` exists
- ✅ `src/testing/README.md` exists
- ⏳ All other modules lack README documentation

### Completed Steps
- ✅ Step 1: Define documentation template and standards
- ✅ Step 2: Document core modules (core, common)
- ✅ Step 3: Document data modules (data, conversion - conversion is empty, skipped)
- ✅ Step 4: Document training modules (training)
- ✅ Step 5: Document infrastructure modules (infrastructure)
- ✅ Step 6: Document orchestration modules (orchestration)
- ✅ Step 7: Document evaluation modules (evaluation, selection - selection is deprecated shim)
- ✅ Step 8: Document deployment modules (deployment)
- ✅ Step 9: Document testing modules (testing)
- ✅ Step 10: Document API modules (api - module is empty, skipped)
- ✅ Step 11: Create Module Index and Cross-References
- ✅ Step 12: Final Review and Consistency Check

### Pending Steps

NONE

## Preconditions

- Codebase structure is stable (no major refactoring in progress)
- Module boundaries are clear
- **Note**: If public API boundaries are unclear, the README should explicitly state "public vs internal" and note any TODOs for clarification

## Documentation Template

Each module README.md should follow the **minimum required skeleton** below; include optional sections only when applicable. Do not create empty headings for optional sections.

```markdown
# [Module Name]

[One-sentence overview of module purpose]

## TL;DR / Quick Start

**[Required for complex modules, recommended for all]**

[1-2 sentence summary + minimal working example]

```python
# Minimal example that works
from src.module import main_function

result = main_function(input)
```

## Overview

[1-2 paragraphs: what the module does, its role in the system. Use bullet points for clarity. Include non-goals if needed to set boundaries.]

## Key Concepts

[If applicable, explain domain concepts, design patterns, or architectural decisions]

## Module Structure

**[Required]**

List **key entry points and folders only**, not every file. Optionally note "where to add X" for common extension points.

- `entry_point.py`: [Main entry point or primary public API]
- `subfolder/`: [Purpose of subfolder]
- `other_key_file.py`: [Only if it's a major component]

Avoid exhaustive file dumps that will rot quickly.

## Usage

### Basic Usage

[Common use cases with code examples]

### Advanced Usage

[Complex scenarios, integration patterns]

### CLI Usage

[If module has CLI entry points]

## API Reference

**[Optional - include only if module has public APIs]**

**Policy**: Manual API documentation is limited to **top-level stable surface (max 10 items)**. For more detailed APIs, link to source code or generated documentation.

### Public Functions/Classes

[Only top-level stable APIs - max 10 items]

- `function_name(param: Type) -> ReturnType`: [Brief description]
- `ClassName`: [Brief description]

For detailed signatures, see source code or generated docs.

### Configuration

[Configuration options, environment variables, config files]

## Integration Points

[How this module integrates with others, dependencies, and usage by other modules]

## Examples

[Complete working examples]

## Best Practices

[Guidelines for using the module effectively]

## Notes

[Important caveats, limitations, known issues]

## Testing

**[Recommended for all modules, required for complex modules]**

How to test this module:

```bash
# Run module tests
uvx pytest tests/path/to/module/

# Or specific test file
uvx pytest tests/path/to/module/test_module.py
```

[Any fixtures, setup requirements, or test-specific notes]

## Related Modules

**[Required]**

[Links to related modules and their documentation]
```

## Proposed Structure

### Directory Structure

Each module should have a `README.md` file at its root level:

```text
src/
├── core/
│   └── README.md
├── common/
│   └── README.md
├── training/
│   ├── README.md
│   ├── core/
│   │   └── README.md
│   ├── hpo/
│   │   └── README.md
│   └── execution/
│       └── README.md
├── infrastructure/
│   ├── README.md
│   ├── config/
│   │   └── README.md
│   └── tracking/
│       └── README.md
└── ...
```

### Documentation File Structure

#### For Simple Modules (core, common, selection)

Simple modules with focused responsibilities should have concise documentation:

```markdown
# [Module Name]

[One-sentence overview]

## TL;DR / Quick Start

[1-2 sentence summary + minimal working example]

```python
from src.module import function

result = function(arg1, arg2)
```

## Overview

[1-2 paragraphs: purpose, role. Use bullet points for clarity.]

## Module Structure

- `entry_point.py`: [Main entry point or primary public API]
- `key_folder/`: [Purpose of folder]

## Usage

### Basic Example

```python
from src.module import function

result = function(arg1, arg2)
```

### Advanced Usage

[If applicable]

## API Reference

[Only top-level stable APIs - max 10 items]

- `function_name(param: Type) -> ReturnType`: [Brief description]

For detailed signatures, see source code.

## Integration Points

- Used by: [list modules that import this]
- Depends on: [list dependencies]

## Testing

```bash
uvx pytest tests/path/to/module/
```

## Related Modules

- [`../related_module/README.md`](../related_module/README.md) - [Brief description]

```

#### For Complex Modules (training, infrastructure, orchestration)

Complex modules with submodules should have hierarchical documentation:

```markdown
# [Module Name]

[One-sentence overview]

## TL;DR / Quick Start

**[Required for complex modules]**

[1-2 sentence summary + minimal working example]

```python
from src.module import Orchestrator
from src.module.config import Config

config = Config.load("config.yaml")
orchestrator = Orchestrator(config)
result = orchestrator.run()
```

## Overview

[1-2 paragraphs: purpose, role, architecture. Use bullet points for clarity.]

## Key Concepts

[Explain domain concepts, design patterns, architectural decisions]

## Module Structure

This module is organized into the following submodules:

- `submodule1/`: [Purpose and responsibility]
- `submodule2/`: [Purpose and responsibility]

See individual submodule READMEs for detailed documentation:
- [`submodule1/README.md`](submodule1/README.md)
- [`submodule2/README.md`](submodule2/README.md)

## Usage

### Basic Workflow

[High-level workflow example]

```python
from src.module import Orchestrator
from src.module.config import Config

config = Config.load("config.yaml")
orchestrator = Orchestrator(config)
result = orchestrator.run()
```

### Advanced Usage (Complex Modules)

[Complex scenarios]

## API Reference (Complex Modules)

### Main Classes

[Only top-level stable APIs - max 10 items]

- `Orchestrator`: [Brief description]
  - `run() -> Result`: [Brief description]
  - `configure(config: Config) -> None`: [Brief description]

For detailed signatures, see source code or generated docs.

### Configuration (Complex Modules)

[Configuration options, environment variables]

## Integration Points (Complex Modules)

### Dependencies

- `src/dependency_module`: [How it's used]
- `src/another_module`: [How it's used]

### Used By

- `src/consumer_module`: [How it uses this module]

## Examples

### Example 1: [Scenario Name]

[Complete working example with explanation]

```python
# Full example code
```

### Example 2: [Scenario Name]

[Another example]

## Best Practices

1. [Guideline 1]
2. [Guideline 2]
3. [Guideline 3]

## Notes

- [Important caveat or limitation]
- [Known issue or workaround]

## Testing

```bash
uvx pytest tests/path/to/module/
```

[Any fixtures, setup requirements, or test-specific notes]

## Related Modules

- [`../related_module/README.md`](../related_module/README.md) - [Description]
- [`submodule/README.md`](submodule/README.md) - [Description]

```

### Module Index Structure

Create `docs/modules/INDEX.md` with the following structure:

```markdown
# Module Documentation Index

## Core Modules

### [`src/core/`](../../src/core/README.md)
Core utilities for token validation, normalization, and placeholder handling.

### [`src/common/`](../../src/common/README.md)
Shared utilities and constants used across the codebase.

## Training Modules

### [`src/training/`](../../src/training/README.md)
Model training, hyperparameter optimization, and execution.

- [`training/core/`](../../src/training/core/README.md) - Core training components
- [`training/hpo/`](../../src/training/hpo/README.md) - Hyperparameter optimization
- [`training/execution/`](../../src/training/execution/README.md) - Execution backends

## Infrastructure Modules

### [`src/infrastructure/`](../../src/infrastructure/README.md)
Infrastructure layer for configuration, paths, tracking, and platform abstraction.

- [`infrastructure/config/`](../../src/infrastructure/config/README.md) - Configuration management
- [`infrastructure/paths/`](../../src/infrastructure/paths/README.md) - Path resolution
- [`infrastructure/tracking/`](../../src/infrastructure/tracking/README.md) - MLflow tracking
- [`infrastructure/naming/`](../../src/infrastructure/naming/README.md) - Naming conventions

## Evaluation Modules

### [`src/evaluation/`](../../src/evaluation/README.md)
Model evaluation, selection, and benchmarking.

- [`evaluation/selection/`](../../src/evaluation/selection/README.md) - Model selection logic
- [`evaluation/benchmarking/`](../../src/evaluation/benchmarking/README.md) - Benchmarking utilities

## Orchestration Modules

### [`src/orchestration/`](../../src/orchestration/README.md)
Job orchestration and workflow management.

- [`orchestration/jobs/`](../../src/orchestration/jobs/README.md) - Job definitions and execution

## Deployment Modules

### [`src/deployment/`](../../src/deployment/README.md)
Model deployment and API serving.

- [`deployment/api/`](../../src/deployment/api/README.md) - FastAPI deployment
- [`deployment/conversion/`](../../src/deployment/conversion/README.md) - Model conversion

## Data Modules

### [`src/data/`](../../src/data/README.md)
Data loading and processing utilities.

### [`src/conversion/`](../../src/conversion/README.md)
Data conversion utilities.

## Testing Modules

### [`src/testing/`](../../src/testing/README.md)
Testing infrastructure and utilities.

## Other Modules

### [`src/benchmarking/`](../../src/benchmarking/README.md)
Inference performance benchmarking.

### [`src/selection/`](../../src/selection/README.md)
Model selection utilities.
```

### Cross-Reference Structure

Each module README should include a "Related Modules" section with links:

```markdown
## Related Modules

- **Upstream dependencies** (modules this depends on):
  - [`../core/README.md`](../core/README.md) - Core utilities used by this module
  - [`../infrastructure/config/README.md`](../infrastructure/config/README.md) - Configuration system

- **Downstream consumers** (modules that use this):
  - [`../training/README.md`](../training/README.md) - Training workflows use this module
  - [`../evaluation/selection/README.md`](../evaluation/selection/README.md) - Selection logic uses this

- **Related modules** (similar functionality):
  - [`../similar_module/README.md`](../similar_module/README.md) - Alternative approach for similar use case
```

### Documentation Standards File Structure

Create `docs/documentation_standards.md`:

```markdown
# Documentation Standards

## File Location

- Each module should have a `README.md` at its root level
- Path: `src/<module>/README.md`
- Submodules: `src/<module>/<submodule>/README.md`

## Required Sections

### Minimum Required (All Modules)

1. **Title** - Module name as H1
2. **TL;DR / Quick Start** - Required for complex modules, recommended for all
3. **Overview** - 1-2 paragraphs describing purpose and role (use bullet points)
4. **Module Structure** - List key entry points and folders only (not every file)
5. **Usage** - At least one working basic example
6. **Testing** - Recommended for all, required for complex modules
7. **Related Modules** - Links to related documentation

### Optional Sections (Include Only When Applicable)

- **Key Concepts** - For modules with domain-specific concepts
- **Advanced Usage** - For complex modules
- **CLI Usage** - For modules with CLI entry points
- **API Reference** - For modules with public APIs (max 10 top-level items)
- **Configuration** - For configurable modules
- **Integration Points** - For modules with complex dependencies
- **Examples** - For modules that benefit from multiple examples
- **Best Practices** - For modules with usage guidelines
- **Notes** - For important caveats or limitations

**Important**: Do not create empty headings for optional sections.

## Code Example Format

- Use Python syntax highlighting: ` ```python `
- Include imports in examples
- **Examples must be copy/paste runnable** or reference `python -m ...` commands that work
- Add comments explaining non-obvious parts
- Reference actual functions/classes from the module
- **Enforcement**: Examples should be tested via:
  - Manual smoke check (copy/paste and run)
  - Or doctest/pytest snippet harness
  - Or verified `python -m ...` commands

## Cross-Reference Format

- Use relative paths: `[../module/README.md](../module/README.md)`
- Include brief description: `[Module Name](../module/README.md) - Brief description`
- Group by relationship type (dependencies, consumers, related)

## Writing Style

- **Concise but complete**: Cover essentials without verbosity
- **Example-driven**: Show usage before explaining theory
- **Practical focus**: Emphasize "how to use" over "how it works"
- **Consistent terminology**: Use domain terms consistently
- **Avoid fluff**: 1-2 paragraphs max for Overview, use bullet points
```

## Module Documentation Intake Process

Before writing a module README, perform this **repeatable intake** to prevent guessing:

### 1. Scan Public Surface

```bash
# List public imports/exports
grep -r "^from src.module\|^import src.module" src/ tests/ | head -20

# List key classes/functions (check __init__.py if exists)
cat src/module/__init__.py 2>/dev/null || echo "No __init__.py"

# List entry points
find src/module -name "*.py" -exec grep -l "if __name__ == '__main__'" {} \;
```

### 2. Identify Entry Points

- CLI commands: `python -m src.module.cli ...`
- Config files: `config/module.yaml`
- Main functions/classes exported from `__init__.py`

### 3. Map Dependencies

**Inbound** (who uses this module):
```bash
grep -r "from src.module\|import src.module" src/ --exclude-dir=module | cut -d: -f1 | sort -u
```

**Outbound** (what this module uses):
```bash
grep -r "^from src\.\|^import src\." src/module/ | grep -v "from src.module" | cut -d: -f2 | sort -u
```

### 4. Document Findings

Create a brief intake note:
- Public APIs: [list]
- Entry points: [list]
- Inbound dependencies: [list modules]
- Outbound dependencies: [list modules]

This intake makes Integration Points and Usage sections real and accurate.

## Per-Module Definition of Done

Each module README is considered complete when:

- [ ] Has minimum required sections (Title, TL;DR/Quick Start, Overview, Module Structure, Usage, Testing, Related Modules)
- [ ] Contains at least one working basic example (copy/paste runnable or verified command)
- [ ] Has Integration Points section (if module has dependencies)
- [ ] Has Related Modules links (all links are valid)
- [ ] Module Structure lists only key entry points and folders (not exhaustive file dumps)
- [ ] API Reference limited to top-level stable surface (max 10 items) or links to source
- [ ] Overview is 1-2 paragraphs with bullet points (no fluff)
- [ ] Testing section includes runnable test commands
- [ ] All code examples have been smoke-tested (copy/paste or command verified)
- [ ] Cross-references are accurate and use relative paths

## Steps

### Step 1: Define Documentation Template and Standards

**Objective**: Establish documentation standards and create a reusable template

**Tasks**:
1. Review existing `src/benchmarking/README.md` as reference
2. Create documentation template (see template above)
3. Define documentation standards:
   - Minimum required sections (with TL;DR/Quick Start and Testing)
   - Code example format and testing requirements
   - Cross-reference conventions
   - When to include vs. omit sections (no empty headings)
4. Document intake process (see "Module Documentation Intake Process" above)
5. Document per-module Definition of Done (see above)
6. Create `docs/documentation_standards.md` with all standards

**Success criteria**:
- Documentation template created and documented
- Standards document exists in `docs/documentation_standards.md` with intake process
- Per-module Definition of Done documented
- Template validated against existing `benchmarking/README.md`

---

### Step 2: Document Core Modules

**Objective**: Document foundational modules that other modules depend on

**Modules to document**:
- `src/core/` - Core utilities (normalize, placeholders, tokens)
- `src/common/` - Shared utilities (constants, shared helpers)

**Batch Process** (repeat for each module):

1. **Intake**: Scan module public surface
   - List public imports/exports from `__init__.py` or key files
   - Identify entry points (CLI, main functions)
   - Map inbound dependencies (who uses this)
   - Map outbound dependencies (what this uses)

2. **Write README**: Create `src/<module>/README.md`
   - Follow minimum required skeleton
   - Include TL;DR/Quick Start with working example
   - Document key entry points and folders only (not every file)
   - Add Integration Points based on intake findings
   - Add Related Modules links

3. **Add cross-links**: Update related module READMEs
   - Add this module to their "Related Modules" sections

4. **Run example checks**: Test all code examples
   - Copy/paste examples and verify they run
   - Or verify `python -m ...` commands work
   - Fix any broken examples

5. **Verify Definition of Done**: Check against checklist
   - All minimum required sections present
   - At least one working example
   - Links are valid
   - Module Structure lists only key items

6. **Mark module done**: Update module index (Step 11)

**Module-Specific Content**:

- `src/core/README.md`: Token validation, normalization, placeholder handling, core concepts
- `src/common/README.md`: Shared utilities (hash_utils, dict_utils, file_utils), constants, when to use common vs. module-specific

**Success criteria**:
- Both READMEs exist with all required sections
- Code examples are tested and work (smoke-tested)
- Cross-references are accurate
- Definition of Done checklist completed for each module

---

### Step 3: Document Data Modules

**Objective**: Document data loading and processing modules

**Modules to document**:
- `src/data/` - Data loaders and processing
- `src/conversion/` - Data conversion utilities

**Tasks**:
1. Create `src/data/README.md`
   - Document data loaders (formats, sources)
   - Document processing pipelines
   - Explain data formats and schemas
2. Create `src/conversion/README.md` (if module has significant content)
   - Document conversion utilities
   - Explain conversion workflows

**Success criteria**:
- `src/data/README.md` exists with all required sections
- `src/conversion/README.md` exists (if applicable)
- Data format examples are included
- Integration with training/evaluation modules documented

---

### Step 4: Document Training Modules

**Objective**: Document model training, HPO, and execution modules

**Modules to document**:
- `src/training/` - Main training module
  - `training/core/` - Core training components (trainer, evaluator, model)
  - `training/hpo/` - Hyperparameter optimization
  - `training/execution/` - Training execution (local, AzureML)
  - `training/cli/` - CLI entry points

**Tasks**:
1. Create `src/training/README.md`
   - Overview of training workflow
   - Document orchestrator, config, data_combiner
   - Link to submodule documentation
2. Create `src/training/core/README.md`
   - Document trainer, evaluator, model classes
   - Explain training loop, metrics, checkpointing
3. Create `src/training/hpo/README.md`
   - Document HPO workflow (Optuna integration, search spaces)
   - Explain trial execution, study management
   - Document checkpoint management
4. Create `src/training/execution/README.md`
   - Document execution backends (local, AzureML, distributed)
   - Explain subprocess runner, MLflow setup
   - Document tags and lineage

**Success criteria**:
- All training module READMEs exist
- Training workflow is clearly documented
- HPO process is explained with examples
- Execution backends are documented
- CLI usage is documented

---

### Step 5: Document Infrastructure Modules

**Objective**: Document infrastructure and platform abstraction modules

**Modules to document**:
- `src/infrastructure/` - Infrastructure layer
  - `infrastructure/config/` - Configuration management
  - `infrastructure/paths/` - Path resolution and management
  - `infrastructure/tracking/` - MLflow tracking integration
  - `infrastructure/naming/` - Naming conventions and policies
  - `infrastructure/platform/` - Platform adapters (AzureML, MLflow)
  - `infrastructure/storage/` - Storage abstractions
  - `infrastructure/setup/` - Setup utilities
  - `infrastructure/metadata/` - Metadata management
  - `infrastructure/fingerprints/` - Fingerprinting utilities

**Tasks**:
1. Create `src/infrastructure/README.md`
   - Overview of infrastructure layer
   - Explain abstraction patterns
   - Link to submodule documentation
2. Create submodule READMEs for major components:
   - `infrastructure/config/README.md` - Configuration system
   - `infrastructure/paths/README.md` - Path resolution
   - `infrastructure/tracking/README.md` - MLflow tracking
   - `infrastructure/naming/README.md` - Naming conventions
   - `infrastructure/platform/README.md` - Platform adapters

**Success criteria**:
- Main infrastructure README exists
- Major submodule READMEs exist (config, paths, tracking, naming, platform)
- Abstraction patterns are explained
- Integration with training/evaluation is documented

---

### Step 6: Document Orchestration Modules

**Objective**: Document job orchestration and workflow management

**Modules to document**:
- `src/orchestration/` - Orchestration layer
  - `orchestration/jobs/` - Job definitions
    - `jobs/hpo/` - HPO job orchestration (local, AzureML)
    - `jobs/tracking/` - Tracking job orchestration
    - `jobs/benchmarking/` - Benchmarking job orchestration
    - `jobs/conversion/` - Conversion job orchestration
  - `orchestration/naming.py` - Naming utilities

**Tasks**:
1. Create `src/orchestration/README.md`
   - Overview of orchestration layer
   - Explain job types and execution patterns
   - Link to submodule documentation
2. Create `src/orchestration/jobs/README.md`
   - Document job structure and execution
   - Explain HPO, tracking, benchmarking jobs
   - Document job dependencies and workflows

**Success criteria**:
- Orchestration READMEs exist
- Job execution patterns are documented
- Integration with training/evaluation is clear

---

### Step 7: Document Evaluation Modules

**Objective**: Document model evaluation, selection, and benchmarking

**Modules to document**:
- `src/evaluation/` - Evaluation module
  - `evaluation/selection/` - Model selection logic
  - `evaluation/benchmarking/` - Benchmarking utilities
- `src/selection/` - Selection module (may overlap with evaluation/selection)

**Tasks**:
1. Create `src/evaluation/README.md`
   - Overview of evaluation capabilities
   - Link to submodule documentation
2. Create `src/evaluation/selection/README.md`
   - Document selection algorithms and logic
   - Explain artifact discovery and acquisition
   - Document selection workflows
3. Create `src/evaluation/benchmarking/README.md` (if different from main benchmarking)
   - Document benchmarking utilities specific to evaluation
4. Create `src/selection/README.md` (if distinct from evaluation/selection)
   - Document selection module purpose and APIs

**Success criteria**:
- Evaluation module READMEs exist
- Selection logic is clearly documented
- Benchmarking integration is explained
- Workflow examples are provided

---

### Step 8: Document Deployment Modules

**Objective**: Document model deployment and API modules

**Modules to document**:
- `src/deployment/` - Deployment module
  - `deployment/api/` - API deployment (FastAPI, inference engine)
  - `deployment/conversion/` - Model conversion for deployment

**Tasks**:
1. Create `src/deployment/README.md`
   - Overview of deployment capabilities
   - Link to submodule documentation
2. Create `src/deployment/api/README.md`
   - Document API structure (FastAPI app, routes, middleware)
   - Document inference engine and decoder
   - Explain model loading and serving
   - Document API configuration and startup
3. Create `src/deployment/conversion/README.md`
   - Document model conversion workflows
   - Explain conversion orchestration

**Success criteria**:
- Deployment module READMEs exist
- API structure and usage are documented
- Inference engine is explained
- Deployment workflows are clear

---

### Step 9: Document Testing Modules

**Objective**: Document testing infrastructure and utilities

**Modules to document**:
- `src/testing/` - Testing module
  - `testing/orchestrators/` - Test orchestration
  - `testing/services/` - Testing services (HPO executor, KFold validator)
  - `testing/validators/` - Data validation
  - `testing/fixtures/` - Test fixtures and helpers
  - `testing/aggregators/` - Result aggregation
  - `testing/comparators/` - Result comparison
  - `testing/setup/` - Test environment setup

**Tasks**:
1. Create `src/testing/README.md`
   - Overview of testing infrastructure
   - Explain testing patterns and utilities
   - Link to submodule documentation
2. Document key submodules:
   - Testing services and validators
   - Fixtures and helpers
   - Result processing utilities

**Success criteria**:
- Testing module README exists
- Testing patterns are documented
- Integration with pytest is explained
- Example test scenarios are provided

---

### Step 10: Document API Modules

**Objective**: Document API module (if distinct from deployment/api)

**Modules to document**:
- `src/api/` - API module (if exists and has content)

**Tasks**:
1. Review `src/api/` structure
2. Create `src/api/README.md` if module has significant content
   - Document API purpose and structure
   - Explain relationship to deployment/api

**Success criteria**:
- API module README exists (if applicable)
- Relationship to deployment is clear

---

### Step 11: Create Module Index and Cross-References

**Objective**: Create navigation and cross-reference system

**Tasks**:
1. Create `docs/modules/INDEX.md`
   - List all modules with brief descriptions
   - Organize by domain (core, training, evaluation, etc.)
   - Include links to module READMEs
2. Update root `README.md` to link to module index
3. Add "Related Modules" sections to each module README
4. Create module dependency diagram (optional, in docs/)

**Success criteria**:
- Module index exists in `docs/modules/INDEX.md`
- Root README links to module index
- All module READMEs have "Related Modules" sections
- Cross-references are accurate and helpful

---

### Step 12: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all documentation

**Tasks**:
1. Review all READMEs against Definition of Done checklist:
   - Minimum required sections present
   - TL;DR/Quick Start included (required for complex, recommended for all)
   - Overview is 1-2 paragraphs (no fluff)
   - Module Structure lists only key items (not exhaustive)
   - At least one working example
   - Testing section included
   - Related Modules links present and valid

2. **Enforce example testing**:
   - For each module, verify examples are:
     - Copy/paste runnable (test manually), OR
     - Verified `python -m ...` commands work, OR
     - Tested via doctest/pytest snippet harness
   - Document any examples that cannot be tested (with reason)
   - Fix or remove broken examples

3. Check for consistency:
   - Terminology consistency
   - Formatting consistency
   - Link accuracy (all relative paths work)
   - API Reference limited to top-level (max 10 items) or links to source

4. Create documentation summary:
   - List all documented modules
   - Note any gaps or limitations
   - Document maintenance guidelines
   - Include example testing status

**Success criteria**:
- ✅ All READMEs pass Definition of Done checklist (23/23 modules)
- ✅ All code examples are tested and work (or documented why not)
- ✅ Cross-references are accurate (all links verified)
- ✅ Documentation summary exists (`docs/modules/DOCUMENTATION_SUMMARY.md`)
- ✅ No broken links or outdated examples (verified)

## Success Criteria (Overall)

- ✅ All major modules have README.md documentation
- ✅ Documentation follows standardized template
- ✅ Code examples are tested and accurate
- ✅ Cross-references between modules are established
- ✅ Module index exists for navigation
- ✅ Documentation is consistent in style and format
- ✅ Public APIs are clearly documented
- ✅ Integration points are explained
- ✅ Best practices are documented

## Module Priority

**High Priority** (Core functionality, frequently used):
1. `core/` - Foundation for other modules
2. `common/` - Shared utilities (foundational, used across codebase)
3. `training/` - Main training workflows
4. `infrastructure/` - Critical infrastructure
5. `evaluation/selection/` - Model selection logic

**Medium Priority** (Important but less foundational):
6. `orchestration/` - Job orchestration
7. `data/` - Data loading and processing
8. `deployment/` - Model deployment
9. `benchmarking/` - Performance benchmarking

**Lower Priority** (Supporting modules):
10. `testing/` - Testing infrastructure
11. `conversion/` - Data conversion
12. `api/` - API module (if applicable)

## Maintenance Guidelines

After initial documentation is complete:

1. **Update documentation when**:
   - Public APIs change
   - Module structure changes significantly
   - New major features are added
   - Integration patterns change

2. **Review documentation**:
   - Quarterly review for accuracy
   - Update examples when APIs change
   - Keep cross-references current

3. **Documentation ownership**:
   - Module maintainers responsible for their module docs
   - PR reviews should check documentation updates

## Notes

- Follow reuse-first principles: reference existing docs rather than duplicating
- Keep documentation concise but complete
- Focus on "how to use" rather than "how it works internally"
- Include practical examples over theoretical explanations
- Document public APIs, not internal implementation details

