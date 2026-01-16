# Master Plan: Update README Files After Refactoring

## Goal

Update and maintain comprehensive technical documentation (README.md) for modules and test modules affected by recent refactoring to:
1. **Remove outdated references**: Update all READMEs to remove references to removed modules (`src/benchmarking/`, `src/orchestration/naming.py`, `src/api/`, `src/conversion/`)
2. **Update import paths**: Ensure all code examples use current import paths (`evaluation.benchmarking` instead of `benchmarking`, `infrastructure.naming` instead of `orchestration.naming`)
3. **Fix broken links**: Update all cross-references to reflect current module structure
4. **Maintain accuracy**: Ensure all READMEs reflect current codebase state after refactoring

## Status

**Last Updated**: 2026-01-16

**Current State**:
- ✅ `src/evaluation/benchmarking/README.md` exists (paths already correct)
- ⏳ `src/orchestration/README.md` references removed `naming.py` facade
- ⏳ Test READMEs may reference old paths
- ⏳ Cross-references may point to removed modules

### Completed Steps
- ✅ Step 0: Documentation audit completed
- ✅ Step 1: Audit source module READMEs for outdated references
- ✅ Step 2: Audit test module READMEs for outdated references
- ✅ Step 3: Update source module READMEs (Priority Group 1)
- ✅ Step 4: Update test module READMEs (Priority Group 1)
- ✅ Step 5: Update cross-references and verify links
- ✅ Step 6: Final review and consistency check

### Pending Steps
- (None - all steps complete)

## Preconditions

- Recent refactoring completed:
  - ✅ `src/benchmarking/` directory removed (moved to `src/evaluation/benchmarking/`)
  - ✅ `src/orchestration/naming.py` facade removed (use `infrastructure.naming` instead)
  - ✅ `src/api/` empty directory removed
  - ✅ `src/conversion/` empty directory removed
- Test suite updated to use new paths
- Code examples in READMEs need verification

## Refactoring Changes Summary

### Removed Modules/Directories

1. **`src/benchmarking/`** → Moved to `src/evaluation/benchmarking/`
   - Old import: `from benchmarking.cli import ...`
   - New import: `from evaluation.benchmarking.cli import ...`
   - Old CLI: `python -m src.benchmarking.cli`
   - New CLI: `python -m src.evaluation.benchmarking.cli`

2. **`src/orchestration/naming.py`** → Use `infrastructure.naming` instead
   - Old import: `from orchestration.naming import ...`
   - New import: `from infrastructure.naming import ...`

3. **`src/api/`** → Empty directory removed (no replacement needed)

4. **`src/conversion/`** → Empty directory removed (no replacement needed)

## Documentation Update Checklist

Each README should be reviewed against this checklist:

### Content Accuracy

- [ ] **Module Structure**: Lists current entry points (removed deprecated modules)
- [ ] **Code Examples**: All examples use current import paths
- [ ] **CLI Usage**: Documents current CLI commands (not old paths)
- [ ] **Import Examples**: All imports use current module paths
- [ ] **Cross-References**: All links point to existing modules
- [ ] **Deprecation Notes**: Updated to reflect current state (removed vs deprecated)

### Completeness

- [ ] **Migration Notes**: Documents migration path if applicable
- [ ] **Related Modules**: Links are valid and current
- [ ] **Examples**: All examples tested and working

## Documentation Audit Process

### 1. Scan for Outdated References

```bash
# Find READMEs that reference removed modules
grep -r "src/benchmarking\|benchmarking\.cli\|from.*benchmarking.*cli" src/ tests/ --include="*.md" | grep -v ".plan.md"

# Find READMEs that reference removed facade
grep -r "orchestration\.naming\|from.*orchestration.*naming" src/ tests/ --include="*.md" | grep -v ".plan.md"

# Find READMEs that reference removed empty directories
grep -r "src/api\|src/conversion" src/ tests/ --include="*.md" | grep -v ".plan.md"
```

### 2. Verify Code Examples

```bash
# Test if import examples work
# (Manually test each code example in README)

# Check if CLI commands still exist
grep -r "python -m src\.benchmarking" src/ tests/ --include="*.md"
```

### 3. Check Cross-References

```bash
# Find all links in READMEs
find src/ tests/ -name "README.md" -exec grep -o '\[.*\](.*\.md)' {} \; | while read link; do
    path=$(echo "$link" | sed 's/.*](\(.*\))/\1/')
    [ -f "$path" ] || echo "Broken link: $link"
done
```

## Steps

### Step 1: Audit Source Module READMEs

**Objective**: Identify which source module READMEs need updates

**Tasks**:
1. Scan all `src/*/README.md` files for references to:
   - `src/benchmarking/` or `benchmarking.cli`
   - `orchestration.naming`
   - `src/api/` or `src/conversion/`
2. Check code examples for outdated import paths
3. Verify CLI command examples use current paths
4. Check cross-references to removed modules
5. Create audit report with specific issues per README

**Expected findings**:
- `src/orchestration/README.md`: References `naming.py` as deprecated facade (line 67) - should update to note it's been removed
- `src/evaluation/benchmarking/README.md`: Should verify all examples use correct paths

**Success criteria**:
- Complete audit report exists
- All source READMEs categorized (needs update, up-to-date)
- Specific issues identified per README

---

### Step 2: Audit Test Module READMEs

**Objective**: Identify which test module READMEs need updates

**Tasks**:
1. Scan all `tests/*/README.md` files for references to:
   - Old benchmarking paths
   - Old import paths
   - Removed modules
2. Check test execution examples for outdated paths
3. Verify test structure documentation is current
4. Check cross-references to removed modules
5. Create audit report with specific issues per README

**Expected findings**:
- `tests/benchmarking/README.md`: May reference old paths (verify)

**Success criteria**:
- Complete audit report exists
- All test READMEs categorized (needs update, up-to-date)
- Specific issues identified per README

---

### Step 3: Update Source Module READMEs (Priority Group 1)

**Objective**: Update high-priority source module READMEs with outdated references

**Modules to update**:
- `src/orchestration/README.md` - **Priority: HIGH** (References removed `naming.py` facade)
- `src/evaluation/benchmarking/README.md` - **Priority: MEDIUM** (Verify all examples correct)

**Update Process** (for each module):

1. **Remove outdated references**:
   - Remove mentions of `orchestration.naming` (use `infrastructure.naming` instead)
   - Remove mentions of `src/benchmarking/` (use `src/evaluation/benchmarking/` instead)
   - Remove mentions of removed empty directories

2. **Update code examples**:
   - Change `from orchestration.naming import ...` → `from infrastructure.naming import ...`
   - Change `python -m src.benchmarking.cli` → `python -m src.evaluation.benchmarking.cli`
   - Change `from benchmarking.cli import ...` → `from evaluation.benchmarking.cli import ...`

3. **Update module structure**:
   - Remove `naming.py` from module structure (if listed)
   - Update descriptions to reflect current state

4. **Update deprecation notes**:
   - Change "deprecated" to "removed" where applicable
   - Update migration guidance

5. **Verify examples**:
   - Test all code examples
   - Verify all CLI commands work

**Specific updates for `src/orchestration/README.md`**:
- Line 67: Change "`naming.py`: Deprecated facade (use `infrastructure.naming` instead)" to "`naming.py`: Removed (use `infrastructure.naming` instead)"
- Remove any code examples using `orchestration.naming`
- Update any cross-references

**Success criteria**:
- All priority group 1 source READMEs updated
- All code examples tested and working
- All outdated references removed
- Cross-references valid

---

### Step 4: Update Test Module READMEs (Priority Group 1)

**Objective**: Update high-priority test module READMEs with outdated references

**Test modules to update**:
- `tests/benchmarking/README.md` - **Priority: MEDIUM** (Verify no old path references)

**Update Process** (for each test module):

1. **Remove outdated references**:
   - Remove mentions of old benchmarking paths
   - Update test structure if it references removed modules

2. **Update test execution examples**:
   - Verify all test commands use current paths
   - Update any test file references

3. **Update test coverage documentation**:
   - Ensure "What Is Tested" reflects current test structure
   - Remove references to tests for removed modules

4. **Verify examples**:
   - Test all test execution examples
   - Verify all paths are correct

**Success criteria**:
- All priority group 1 test READMEs updated
- All test execution examples tested and working
- All outdated references removed

---

### Step 5: Update Cross-References and Verify Links

**Objective**: Ensure all cross-references and navigation are current

**Tasks**:
1. Search for cross-references to removed modules:
   - `[benchmarking](../benchmarking/README.md)` → Update to `[benchmarking](../evaluation/benchmarking/README.md)`
   - `[orchestration.naming](naming.py)` → Remove or update
2. Verify all "Related Modules" sections:
   - All links valid
   - Descriptions current
   - No references to removed modules
3. Check root `README.md` if it exists:
   - Verify links to module documentation
   - Update if structure changed
4. Verify all internal links work:
   - Test all relative paths
   - Fix broken links

**Success criteria**:
- All cross-references updated
- All links valid and working
- No broken references to removed modules

---

### Step 6: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all updated documentation

**Tasks**:
1. Review all updated READMEs against Definition of Done checklist
2. **Enforce example testing**: Verify all code examples work
3. Check for consistency:
   - Terminology consistency (removed vs deprecated)
   - Import path consistency
   - Link accuracy
4. Create update summary:
   - List all READMEs updated
   - Note any remaining gaps or limitations
   - Include example testing status

**Success criteria**:
- All updated READMEs pass Definition of Done checklist
- All code examples are tested and work
- Cross-references are accurate
- Update summary exists
- No broken links or outdated examples

## Per-Module Definition of Done (Update)

Each README update is considered complete when:

- [ ] All outdated references to removed modules have been removed
- [ ] All code examples use current import paths
- [ ] All CLI commands use current paths
- [ ] All cross-references are valid and current
- [ ] Module Structure reflects current codebase (no removed modules)
- [ ] All code examples have been tested and work
- [ ] Deprecation notes updated to reflect current state
- [ ] Related Modules links are valid

## Module Update Priority

**High Priority** (Critical updates needed):
1. `src/orchestration/README.md` - References removed `naming.py` facade

**Medium Priority** (Important updates):
2. `src/evaluation/benchmarking/README.md` - Verify all examples correct
3. `tests/benchmarking/README.md` - Verify no old path references

**Lower Priority** (Nice to have updates):
4. Other READMEs that may have indirect references

## Migration Examples

### Import Path Updates

**Before**:
```python
from orchestration.naming import build_mlflow_experiment_name
```

**After**:
```python
from infrastructure.naming import build_mlflow_experiment_name
```

### CLI Command Updates

**Before**:
```bash
python -m src.benchmarking.cli --checkpoint ... --test-data ...
```

**After**:
```bash
python -m src.evaluation.benchmarking.cli --checkpoint ... --test-data ...
```

### Module Structure Updates

**Before**:
```
- `naming.py`: Deprecated facade (use `infrastructure.naming` instead)
```

**After**:
```
- `naming.py`: Removed (use `infrastructure.naming` instead)
```

## Success Criteria (Overall)

- ✅ All outdated references to removed modules have been removed
- ✅ All code examples use current import paths
- ✅ All CLI commands use current paths
- ✅ All cross-references are valid and current
- ✅ Module Structure reflects current codebase
- ✅ All code examples are tested and accurate
- ✅ No broken links or outdated examples

## Maintenance Guidelines

After update is complete:

1. **Ongoing maintenance**:
   - Update documentation when module structure changes
   - Review quarterly for accuracy
   - Test examples when import paths change
   - Keep cross-references current

2. **Update triggers**:
   - Module removal or migration
   - Import path changes
   - CLI command changes
   - Module structure changes

3. **Documentation ownership**:
   - Module maintainers responsible for their module docs
   - PR reviews should check documentation updates
   - Use this update plan for periodic reviews

## Notes

- This plan focuses on **updating existing documentation** after refactoring
- Priority is on removing outdated references and fixing broken examples
- Update incrementally - don't try to update everything at once
- Test all code examples to ensure they work with current codebase
- Focus on accuracy over comprehensive rewrites

