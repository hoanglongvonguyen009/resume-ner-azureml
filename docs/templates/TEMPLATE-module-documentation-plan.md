# Master Plan: Technical Documentation for All [MODULE_TYPE] Modules

## Goal

Create comprehensive technical documentation (README.md) for each module in `[TARGET_DIRECTORY]/` to:
1. **Improve developer onboarding**: Clear understanding of module purpose, structure, and usage
2. **Enable code reuse**: Document public APIs, utilities, and integration points
3. **Maintain consistency**: Standardized documentation format across all modules
4. **Support maintenance**: Clear module boundaries, dependencies, and responsibilities

## Status

**Last Updated**: [YYYY-MM-DD]

**Current State**:
- ✅ `[TARGET_DIRECTORY]/[example_module]/README.md` exists (comprehensive example)
- ✅ `docs/TEMPLATE-documentation_standards.md` exists (template and standards)
- ⏳ All other modules lack README documentation

### Completed Steps
- ✅ Step 0: Existing documentation infrastructure identified

### Pending Steps
- ⏳ Step 1: Define documentation template and standards
- ⏳ Step 2: Document [priority_group_1] modules ([list modules])
- ⏳ Step 3: Document [priority_group_2] modules ([list modules])
- ⏳ Step 4: Document [priority_group_3] modules ([list modules])
- ⏳ Step 5: Create module index and cross-references
- ⏳ Step 6: Final review and consistency check

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

```[LANGUAGE]
# Minimal example that works
from [module_path] import main_function

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
[TEST_COMMAND] tests/path/to/module/

# Or specific test file
[TEST_COMMAND] tests/path/to/module/test_module.py
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
[TARGET_DIRECTORY]/
├── [module1]/
│   └── README.md
├── [module2]/
│   ├── README.md
│   ├── [submodule1]/
│   │   └── README.md
│   └── [submodule2]/
│       └── README.md
└── ...
```

### Documentation File Structure

#### For Simple Modules

Simple modules with focused responsibilities should have concise documentation:

```markdown
# [Module Name]

[One-sentence overview]

## TL;DR / Quick Start

[1-2 sentence summary + minimal working example]

```[LANGUAGE]
from [module_path] import function

result = function(arg1, arg2)
```

## Overview

[1-2 paragraphs: purpose, role. Use bullet points for clarity.]

## Module Structure

- `entry_point.py`: [Main entry point or primary public API]
- `key_folder/`: [Purpose of folder]

## Usage

### Basic Example

```[LANGUAGE]
from [module_path] import function

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
[TEST_COMMAND] tests/path/to/module/
```

## Related Modules

- [`../related_module/README.md`](../related_module/README.md) - [Brief description]
```

#### For Complex Modules

Complex modules with submodules should have hierarchical documentation:

```markdown
# [Module Name]

[One-sentence overview]

## TL;DR / Quick Start

**[Required for complex modules]**

[1-2 sentence summary + minimal working example]

```[LANGUAGE]
from [module_path] import Orchestrator
from [module_path].config import Config

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

```[LANGUAGE]
from [module_path] import Orchestrator
from [module_path].config import Config

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

- `[dependency_module]`: [How it's used]
- `[another_module]`: [How it's used]

### Used By

- `[consumer_module]`: [How it uses this module]

## Examples

### Example 1: [Scenario Name]

[Complete working example with explanation]

```[LANGUAGE]
# Full example code
```

## Best Practices

1. [Guideline 1]
2. [Guideline 2]
3. [Guideline 3]

## Notes

- [Important caveat or limitation]
- [Known issue or workaround]

## Testing

```bash
[TEST_COMMAND] tests/path/to/module/
```

[Any fixtures, setup requirements, or test-specific notes]

## Related Modules

- [`../related_module/README.md`](../related_module/README.md) - [Description]
- [`submodule/README.md`](submodule/README.md) - [Description]
```

### Module Index Structure

Create `docs/[index_location]/INDEX.md` with the following structure:

```markdown
# Module Documentation Index

## [Category 1] Modules

### [`[TARGET_DIRECTORY]/[module1]/`](../../[TARGET_DIRECTORY]/[module1]/README.md)
[Brief description]

### [`[TARGET_DIRECTORY]/[module2]/`](../../[TARGET_DIRECTORY]/[module2]/README.md)
[Brief description]

- [`[submodule1]/`](../../[TARGET_DIRECTORY]/[module2]/[submodule1]/README.md) - [Description]
- [`[submodule2]/`](../../[TARGET_DIRECTORY]/[module2]/[submodule2]/README.md) - [Description]

## [Category 2] Modules

[Continue pattern...]
```

### Cross-Reference Structure

Each module README should include a "Related Modules" section with links:

```markdown
## Related Modules

- **Upstream dependencies** (modules this depends on):
  - [`../[dependency_module]/README.md`](../[dependency_module]/README.md) - [Description]

- **Downstream consumers** (modules that use this):
  - [`../[consumer_module]/README.md`](../[consumer_module]/README.md) - [Description]

- **Related modules** (similar functionality):
  - [`../[related_module]/README.md`](../[related_module]/README.md) - [Description]
```

## Module Documentation Intake Process

Before writing a module README, perform this **repeatable intake** to prevent guessing:

### 1. Scan Public Surface

```bash
# List public imports/exports
grep -r "^from [TARGET_DIRECTORY].module\|^import [TARGET_DIRECTORY].module" [TARGET_DIRECTORY]/ tests/ | head -20

# List key classes/functions (check __init__.py if exists)
cat [TARGET_DIRECTORY]/module/__init__.py 2>/dev/null || echo "No __init__.py"

# List entry points
find [TARGET_DIRECTORY]/module -name "*.py" -exec grep -l "if __name__ == '__main__'" {} \;
```

### 2. Identify Entry Points

- CLI commands: `[CLI_COMMAND_PATTERN]`
- Config files: `[CONFIG_FILE_PATTERN]`
- Main functions/classes exported from `__init__.py`

### 3. Map Dependencies

**Inbound** (who uses this module):
```bash
grep -r "from [TARGET_DIRECTORY].module\|import [TARGET_DIRECTORY].module" [TARGET_DIRECTORY]/ --exclude-dir=module | cut -d: -f1 | sort -u
```

**Outbound** (what this module uses):
```bash
grep -r "^from [TARGET_DIRECTORY]\.\|^import [TARGET_DIRECTORY]\." [TARGET_DIRECTORY]/module/ | grep -v "from [TARGET_DIRECTORY].module" | cut -d: -f2 | sort -u
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
1. Review existing `[TARGET_DIRECTORY]/[example_module]/README.md` as reference
2. Create documentation template (see template above)
3. Define documentation standards:
   - Minimum required sections (with TL;DR/Quick Start and Testing)
   - Code example format and testing requirements
   - Cross-reference conventions
   - When to include vs. omit sections (no empty headings)
4. Document intake process (see "Module Documentation Intake Process" above)
5. Document per-module Definition of Done (see above)
6. Create `docs/TEMPLATE-documentation_standards.md` with all standards

**Success criteria**:
- Documentation template created and documented
- Standards document exists with intake process
- Per-module Definition of Done documented
- Template validated against existing example README

---

### Step 2: Document [Priority Group 1] Modules

**Objective**: Document foundational modules that other modules depend on

**Modules to document**:
- `[TARGET_DIRECTORY]/[module1]/` - [Description]
- `[TARGET_DIRECTORY]/[module2]/` - [Description]

**Batch Process** (repeat for each module):

1. **Intake**: Scan module public surface
   - List public imports/exports from `__init__.py` or key files
   - Identify entry points (CLI, main functions)
   - Map inbound dependencies (who uses this)
   - Map outbound dependencies (what this uses)

2. **Write README**: Create `[TARGET_DIRECTORY]/<module>/README.md`
   - Follow minimum required skeleton
   - Include TL;DR/Quick Start with working example
   - Document key entry points and folders only (not every file)
   - Add Integration Points based on intake findings
   - Add Related Modules links

3. **Add cross-links**: Update related module READMEs
   - Add this module to their "Related Modules" sections

4. **Run example checks**: Test all code examples
   - Copy/paste examples and verify they run
   - Or verify commands work
   - Fix any broken examples

5. **Verify Definition of Done**: Check against checklist

6. **Mark module done**: Update module index (Step N)

**Success criteria**:
- All READMEs exist with all required sections
- Code examples are tested and work (smoke-tested)
- Cross-references are accurate
- Definition of Done checklist completed for each module

---

### Step N: Create Module Index and Cross-References

**Objective**: Create navigation and cross-reference system

**Tasks**:
1. Create `docs/[index_location]/INDEX.md`
   - List all modules with brief descriptions
   - Organize by domain/category
   - Include links to module READMEs
2. Update root `README.md` to link to module index
3. Add "Related Modules" sections to each module README
4. Create module dependency diagram (optional)

**Success criteria**:
- Module index exists
- Root README links to module index
- All module READMEs have "Related Modules" sections
- Cross-references are accurate and helpful

---

### Step N+1: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all documentation

**Tasks**:
1. Review all READMEs against Definition of Done checklist
2. **Enforce example testing**: Verify all examples work
3. Check for consistency: terminology, formatting, links
4. Create documentation summary

**Success criteria**:
- All READMEs pass Definition of Done checklist
- All code examples are tested and work
- Cross-references are accurate
- Documentation summary exists
- No broken links or outdated examples

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
1. `[module1]/` - [Reason]
2. `[module2]/` - [Reason]
3. `[module3]/` - [Reason]

**Medium Priority** (Important but less foundational):
4. `[module4]/` - [Reason]
5. `[module5]/` - [Reason]

**Lower Priority** (Supporting modules):
6. `[module6]/` - [Reason]
7. `[module7]/` - [Reason]

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

## Template Usage Instructions

When using this template:

1. **Replace placeholders**:
   - `[MODULE_TYPE]` - Type of modules being documented (e.g., "Source", "Test", "Infrastructure")
   - `[TARGET_DIRECTORY]` - Directory containing modules (e.g., "src", "tests")
   - `[LANGUAGE]` - Programming language (e.g., "python", "javascript")
   - `[TEST_COMMAND]` - Test execution command (e.g., "uvx pytest", "npm test")
   - `[CLI_COMMAND_PATTERN]` - CLI command pattern (e.g., "python -m src.module.cli")
   - `[CONFIG_FILE_PATTERN]` - Config file pattern (e.g., "config/module.yaml")
   - `[index_location]` - Where to create index (e.g., "modules", "tests/docs")
   - `[module1]`, `[module2]`, etc. - Actual module names
   - `[Priority Group 1]`, etc. - Priority group names

2. **Customize steps**: Add or remove steps based on your module structure

3. **Update intake commands**: Adjust grep/find commands to match your codebase structure

4. **Set priorities**: Define your own priority groups based on dependencies and usage

