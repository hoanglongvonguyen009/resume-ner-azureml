# Analyze Deprecated Scripts and Code Throughout Codebase

## Goal

Conduct a comprehensive, systematic analysis of all deprecated code throughout the codebase, including:
- Deprecated modules and packages
- Deprecated functions and classes
- Deprecated scripts and entry points
- Deprecated configuration keys and options
- Deprecated notebooks and workflows

The analysis will categorize deprecated code by type, usage patterns, migration complexity, and removal priority to create a clear roadmap for cleanup.

## Status

**Last Updated**: 2025-01-27

### Completed Steps
- ✅ Step 1: Catalog all deprecated code markers
- ✅ Step 2: Categorize deprecated code by type
- ✅ Step 3: Analyze usage patterns (imports, calls, references)
- ✅ Step 4: Identify migration paths and replacements
- ✅ Step 5: Assess removal complexity and risk
- ✅ Step 6: Prioritize deprecated code for removal
- ✅ Step 7: Document findings in structured format
- ✅ Step 8: Create removal roadmap

### Pending Steps
- (None - all steps complete)

## Preconditions

- Codebase is in a stable state
- Previous deprecated code removal plan completed (reference: `FINISHED-remove-deprecated-code.plan.md`)
- Understanding of current module structure and naming conventions

## Steps

### Step 1: Catalog All Deprecated Code Markers

**Objective**: Systematically identify all deprecated code markers in the codebase.

1. Search for deprecation patterns:
   - `DEPRECATED` (uppercase comments/docstrings)
   - `deprecated` (lowercase in strings/comments)
   - `DeprecationWarning` (Python warnings)
   - `@deprecated` (decorators, if used)
   - `deprecated::` (Sphinx-style, if used)

2. Search across all file types:
   - Python source files (`src/**/*.py`)
   - Test files (`tests/**/*.py`)
   - Notebooks (`notebooks/**/*.ipynb`)
   - Configuration files (`*.yaml`, `*.yml`, `*.json`)
   - Documentation files (`docs/**/*.md`)

3. Extract metadata for each finding:
   - File path
   - Line number(s)
   - Deprecation message/description
   - Type (module, function, class, config key, etc.)
   - Replacement suggestion (if mentioned)

**Success criteria**:
- ✅ Complete inventory of all deprecation markers in `docs/implementation_plans/audits/deprecated-code-inventory.md`
- ✅ All deprecation patterns identified (at least 4 patterns: DEPRECATED, deprecated, DeprecationWarning, deprecated::)
- ✅ Metadata extracted for each finding (file, line, message, type, replacement)
- ✅ Search covers all file types (Python, notebooks, configs, docs)

**Verification**:
```bash
# Find all deprecation markers
grep -rn "DEPRECATED\|deprecated\|DeprecationWarning\|@deprecated\|deprecated::" \
  src/ tests/ notebooks/ docs/ *.yaml *.yml *.json 2>/dev/null | \
  grep -v ".plan.md\|.md:" | sort > docs/implementation_plans/audits/deprecated-code-inventory-raw.txt

# Count findings by pattern
echo "=== Deprecation Pattern Counts ==="
grep -c "DEPRECATED" docs/implementation_plans/audits/deprecated-code-inventory-raw.txt || echo "0"
grep -c "deprecated" docs/implementation_plans/audits/deprecated-code-inventory-raw.txt || echo "0"
grep -c "DeprecationWarning" docs/implementation_plans/audits/deprecated-code-inventory-raw.txt || echo "0"
```

### Step 2: Categorize Deprecated Code by Type

**Objective**: Organize deprecated code into logical categories for analysis.

1. Create categories:
   - **Modules/Packages**: Entire modules marked deprecated (e.g., `orchestration.*`, `training_exec.*`)
   - **Functions**: Individual functions marked deprecated
   - **Classes**: Deprecated classes
   - **Configuration Keys**: Deprecated config options (e.g., `objective.goal`)
   - **Scripts/Entry Points**: Scripts with `if __name__ == "__main__"` that are deprecated
   - **Notebooks**: Deprecated notebook workflows
   - **Imports/Facades**: Deprecated import paths or facade modules

2. For each category, extract:
   - Count of deprecated items
   - Common patterns (e.g., all `orchestration.*` modules follow similar deprecation pattern)
   - Replacement patterns (e.g., all `orchestration.*` → `infrastructure.*`)

3. Create category summary table

**Success criteria**:
- ✅ All deprecated code categorized into at least 6 categories
- ✅ Category summary table created in audit document
- ✅ Common patterns identified (e.g., orchestration → infrastructure migration pattern)
- ✅ Replacement patterns documented for each category

**Verification**:
```bash
# Count by category (approximate)
echo "=== Module/Package Deprecations ==="
grep -r "DEPRECATED.*module\|module.*deprecated" src/ | wc -l

echo "=== Function Deprecations ==="
grep -r "def.*deprecated\|deprecated.*def" src/ | wc -l

echo "=== Config Key Deprecations ==="
grep -r "deprecated.*key\|key.*deprecated" src/ | wc -l
```

### Step 3: Analyze Usage Patterns (Imports, Calls, References)

**Objective**: Understand how deprecated code is currently being used.

1. For each deprecated item, search for:
   - **Direct imports**: `from deprecated.module import ...`
   - **Indirect imports**: `import deprecated.module`
   - **Function calls**: `deprecated_function(...)`
   - **Class instantiations**: `DeprecatedClass(...)`
   - **Config usage**: References to deprecated config keys
   - **Notebook usage**: Deprecated imports/calls in notebooks

2. Distinguish usage types:
   - **Internal usage**: Within deprecated module itself (expected, will be removed)
   - **External usage**: Outside deprecated module (needs migration)
   - **Test usage**: In test files (needs test updates)
   - **Notebook usage**: In notebooks (needs notebook updates)

3. For each usage, document:
   - File path
   - Line number
   - Usage type (import, call, reference)
   - Context (function/class where used)

**Success criteria**:
- ✅ Usage analysis completed for all deprecated modules
- ✅ Usage analysis completed for all deprecated functions
- ✅ Internal vs external usage clearly distinguished
- ✅ Test and notebook usage identified separately
- ✅ Usage counts documented in audit report

**Verification**:
```bash
# Example: Analyze usage of deprecated orchestration module
echo "=== orchestration.* imports ==="
grep -r "from orchestration\|import orchestration" src/ tests/ notebooks/ | \
  grep -v "orchestration/__init__.py\|orchestration/jobs/__init__.py" | wc -l

# Example: Analyze usage of deprecated training_exec
echo "=== training_exec.* imports ==="
grep -r "from training_exec\|import training_exec" src/ tests/ notebooks/ | \
  grep -v "training_exec/__init__.py" | wc -l
```

### Step 4: Identify Migration Paths and Replacements

**Objective**: Document clear migration paths for each deprecated item.

1. For each deprecated item, identify:
   - **Replacement module/function**: What should be used instead
   - **Migration pattern**: How to update imports/calls
   - **Breaking changes**: Any API differences between deprecated and replacement
   - **Migration examples**: Code examples showing before/after

2. Verify replacements exist:
   - Check that replacement modules/functions actually exist
   - Verify replacement has equivalent functionality
   - Note any missing replacements (blockers for removal)

3. Document migration complexity:
   - **Simple**: Direct 1:1 replacement (e.g., `orchestration.paths` → `infrastructure.paths`)
   - **Moderate**: Requires parameter changes or minor refactoring
   - **Complex**: Significant refactoring required, API changes

**Success criteria**:
- ✅ Migration path documented for all deprecated items
- ✅ Replacement modules/functions verified to exist
   - Missing replacements flagged as blockers
- ✅ Migration complexity assessed (simple/moderate/complex)
- ✅ Migration examples provided for common patterns

**Verification**:
```bash
# Verify replacements exist
echo "=== Checking replacement modules ==="
# Example: Check if infrastructure.paths exists (replacement for orchestration.paths)
test -f src/infrastructure/paths/__init__.py && echo "✓ infrastructure.paths exists" || echo "✗ infrastructure.paths missing"

# Check if training.execution exists (replacement for training_exec)
test -d src/training/execution && echo "✓ training.execution exists" || echo "✗ training.execution missing"
```

### Step 5: Assess Removal Complexity and Risk

**Objective**: Evaluate the effort and risk involved in removing each deprecated item.

1. For each deprecated item, assess:
   - **Removal complexity**:
     - **Low**: No external usage, simple deletion
     - **Medium**: Some external usage, requires migration updates
     - **High**: Extensive usage, complex migration, potential breaking changes
   
   - **Risk level**:
     - **Low**: Well-tested, clear migration path, no production dependencies
     - **Medium**: Some uncertainty, moderate test coverage
     - **High**: Critical paths, unclear migration, production dependencies

2. Consider factors:
   - Number of external usages (from Step 3)
   - Migration complexity (from Step 4)
   - Test coverage of replacement
   - Production usage (if known)
   - Breaking change impact

3. Create risk matrix:
   - **Low complexity + Low risk**: Safe to remove immediately
   - **Low complexity + Medium risk**: Remove with caution
   - **Medium complexity + Low risk**: Plan migration, then remove
   - **Medium/High complexity + Medium/High risk**: Requires careful planning

**Success criteria**:
- ✅ Removal complexity assessed for all deprecated items
- ✅ Risk level assessed for all deprecated items
- ✅ Risk matrix created showing complexity vs risk
- ✅ Factors documented (usage count, migration complexity, test coverage)

**Verification**:
```bash
# Count deprecated items by usage level (approximate)
echo "=== Usage-based complexity estimate ==="
# Low complexity: 0 external usages
# Medium complexity: 1-5 external usages
# High complexity: 5+ external usages
```

### Step 6: Prioritize Deprecated Code for Removal

**Objective**: Create a prioritized removal roadmap based on complexity, risk, and impact.

1. Group deprecated items by priority:
   - **P0 - Immediate**: Low complexity, low risk, no usage (safe to remove now)
   - **P1 - High**: Low-medium complexity, clear migration path, low-medium risk
   - **P2 - Medium**: Medium complexity, moderate migration effort
   - **P3 - Low**: High complexity or high risk, requires careful planning
   - **P4 - Deferred**: Blocked (missing replacements, unclear migration)

2. Consider dependencies:
   - Remove lower-level deprecated code first (functions before modules)
   - Remove unused deprecated code before used code
   - Group related deprecated items for batch removal

3. Create removal phases:
   - **Phase 1**: P0 items (quick wins)
   - **Phase 2**: P1 items (high value, low risk)
   - **Phase 3**: P2 items (moderate effort)
   - **Phase 4**: P3 items (requires planning)
   - **Phase 5**: P4 items (blocked, needs investigation)

**Success criteria**:
- ✅ All deprecated items assigned priority (P0-P4)
- ✅ Removal phases defined (Phase 1-5)
- ✅ Dependencies between deprecated items identified
- ✅ Prioritized removal roadmap created

**Verification**:
```bash
# Count items by priority (will be in audit document)
echo "=== Priority Distribution ==="
# P0: X items
# P1: X items
# P2: X items
# P3: X items
# P4: X items
```

### Step 7: Document Findings in Structured Format

**Objective**: Create comprehensive documentation of all findings.

1. Create structured audit document: `docs/implementation_plans/audits/deprecated-scripts-analysis.md`

2. Document sections:
   - **Executive Summary**: High-level findings, counts, priorities
   - **Deprecated Code Inventory**: Complete list with metadata
   - **Category Analysis**: Breakdown by type (modules, functions, etc.)
   - **Usage Analysis**: Usage patterns and counts
   - **Migration Paths**: Replacement mappings and examples
   - **Risk Assessment**: Complexity and risk matrix
   - **Prioritization**: Priority assignments and phases
   - **Removal Roadmap**: Phased removal plan

3. Include tables and visualizations:
   - Summary tables (counts by category, priority)
   - Usage matrices (deprecated item → usage count)
   - Migration mapping tables (deprecated → replacement)
   - Risk matrix (complexity vs risk)
   - Priority timeline (phases with estimated effort)

**Success criteria**:
- ✅ Comprehensive audit document created
- ✅ All sections documented with structured data
- ✅ Tables and summaries included for easy reference
- ✅ Document follows markdown best practices
- ✅ Document is searchable and navigable

**Verification**:
```bash
# Verify audit document exists and has required sections
test -f docs/implementation_plans/audits/deprecated-scripts-analysis.md && \
  echo "✓ Audit document exists" || echo "✗ Audit document missing"

# Check for required sections
grep -q "Executive Summary" docs/implementation_plans/audits/deprecated-scripts-analysis.md && \
  echo "✓ Executive Summary section exists" || echo "✗ Missing section"
```

### Step 8: Create Removal Roadmap

**Objective**: Create actionable roadmap for removing deprecated code in phases.

1. Create roadmap document: `docs/implementation_plans/deprecated-code-removal-roadmap.plan.md`

2. For each phase, document:
   - **Phase description**: What will be removed
   - **Items included**: List of deprecated items (with file paths)
   - **Prerequisites**: What must be done first
   - **Migration steps**: How to migrate remaining usage
   - **Removal steps**: How to remove deprecated code
   - **Verification**: How to verify removal was successful
   - **Estimated effort**: Time/complexity estimate
   - **Success criteria**: How to know phase is complete

3. Create phase timeline:
   - Phase 1: Immediate removals (P0 items)
   - Phase 2: High-priority removals (P1 items)
   - Phase 3: Medium-priority removals (P2 items)
   - Phase 4: Complex removals (P3 items)
   - Phase 5: Blocked items (P4 items)

4. Link to detailed implementation plans:
   - Each phase can spawn a separate implementation plan
   - Reference audit document for details
   - Track progress in roadmap

**Success criteria**:
- ✅ Removal roadmap document created
- ✅ All phases documented with clear steps
- ✅ Prerequisites and dependencies identified
- ✅ Verification steps defined for each phase
- ✅ Estimated effort provided (if possible)
- ✅ Roadmap is actionable and trackable

**Verification**:
```bash
# Verify roadmap document exists
test -f docs/implementation_plans/deprecated-code-removal-roadmap.plan.md && \
  echo "✓ Roadmap document exists" || echo "✗ Roadmap document missing"

# Check for phase sections
grep -c "## Phase" docs/implementation_plans/deprecated-code-removal-roadmap.plan.md
```

## Success Criteria (Overall)

- ✅ **Complete inventory**: All deprecated code identified and cataloged
- ✅ **Categorized analysis**: Deprecated code organized by type and pattern
- ✅ **Usage understanding**: Clear picture of how deprecated code is used
- ✅ **Migration paths**: Clear replacement paths for all deprecated items
- ✅ **Risk assessment**: Complexity and risk evaluated for each item
- ✅ **Prioritization**: Deprecated code prioritized for removal
- ✅ **Comprehensive documentation**: Audit document with all findings
- ✅ **Actionable roadmap**: Phased removal plan with clear steps

## Deliverables

1. **Audit Document**: `docs/implementation_plans/audits/deprecated-scripts-analysis.md`
   - Complete inventory of deprecated code
   - Category analysis
   - Usage analysis
   - Migration paths
   - Risk assessment
   - Prioritization

2. **Removal Roadmap**: `docs/implementation_plans/deprecated-code-removal-roadmap.plan.md`
   - Phased removal plan
   - Step-by-step instructions
   - Verification criteria

3. **Raw Data**: `docs/implementation_plans/audits/deprecated-code-inventory-raw.txt`
   - Raw grep output for reference
   - Can be used for automated analysis

## Notes

- **Scope**: This plan focuses on analysis and documentation. Actual removal will be handled in separate implementation plans per phase.
- **Automation**: Consider creating scripts to automate parts of the analysis (usage detection, migration path verification).
- **Maintenance**: Keep audit document updated as deprecated code is removed.
- **Related Plans**: 
  - `FINISHED-remove-deprecated-code.plan.md` - Previous removal work
  - Future phase-specific removal plans will reference this analysis

## Related Plans

- `FINISHED-remove-deprecated-code.plan.md` - Previous deprecated code removal
- Future phase-specific removal plans (to be created based on roadmap)

