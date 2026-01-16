# Documentation Standards

This document defines the standards, template, and processes for creating technical documentation (README.md) for all modules in `src/`.

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

## Documentation Template

### For Simple Modules (core, common, selection)

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

### For Complex Modules (training, infrastructure, orchestration)

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

### Advanced Usage

[Complex scenarios]

## API Reference

### Main Classes

[Only top-level stable APIs - max 10 items]

- `Orchestrator`: [Brief description]
  - `run() -> Result`: [Brief description]
  - `configure(config: Config) -> None`: [Brief description]

For detailed signatures, see source code or generated docs.

### Configuration

[Configuration options, environment variables]

## Integration Points

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

## API Reference Policy

**Manual API documentation is limited to top-level stable surface (max 10 items)**. For more detailed APIs, link to source code or generated documentation.

### What to Include

- Top-level public functions/classes exported from `__init__.py`
- Main entry points (CLI commands, orchestrators, main classes)
- Stable interfaces that won't change frequently

### What to Exclude

- Internal helper functions
- Implementation details
- Frequently changing APIs
- More than 10 items (link to source instead)

### Format

```markdown
## API Reference

- `function_name(param: Type) -> ReturnType`: [Brief description]
- `ClassName`: [Brief description]
  - `method_name() -> ReturnType`: [Brief description]

For detailed signatures, see source code or generated docs.
```

## Module Structure Guidelines

**List key entry points and folders only**, not every file. Optionally note "where to add X" for common extension points.

### Good Examples

```markdown
## Module Structure

- `cli.py`: CLI entry point and argument parsing
- `orchestrator.py`: High-level orchestration
- `core/`: Core training components
- `execution/`: Execution backends (local, AzureML)
```

### Avoid

```markdown
## Module Structure

- `cli.py`
- `orchestrator.py`
- `core/trainer.py`
- `core/evaluator.py`
- `core/model.py`
- `execution/local.py`
- `execution/azureml.py`
- `utils.py`
- `helpers.py`
...
```

## Example Testing Requirements

All code examples must be verified before documentation is considered complete:

1. **Copy/paste runnable examples**: Test by copying and running in a clean environment
2. **CLI commands**: Verify `python -m ...` commands work as documented
3. **Import statements**: Ensure all imports are correct and available
4. **Output expectations**: Verify examples produce expected results

If an example cannot be tested (e.g., requires specific environment setup), document the reason clearly.

## Reference Example

See `src/benchmarking/README.md` for a comprehensive example that follows these standards:

- Clear TL;DR with working example
- Concise Overview with bullet points
- Module Structure lists only key files
- Multiple usage examples (CLI, programmatic)
- Integration points documented
- Best practices included
- Testing section present
