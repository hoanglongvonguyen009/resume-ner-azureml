# Plan: Build an AzureML-style Root `README.md` (modeled after churn repo)

## Goal

Create an upgraded repo-level `README.md` that matches the clarity and “how to run” completeness of the reference churn project README (inventory → setup → config-driven workflows → end-to-end pipeline → deployment), while staying accurate for **Resume NER with Azure ML**.

This plan targets **documentation only** (no code changes unless required to keep README instructions truthful).

Reference README: [customer-churn-prediction-azureml](https://github.com/longdang193/customer-churn-prediction-azureml)

## Status

**Last Updated**: 2026-01-19

### Completed Steps
- ✅ Step 0: Create plan and align with existing documentation standards
- ✅ Step 1: Audit current root README + identify gaps versus target outline
- ✅ Step 2: Inventory real repo entrypoints (scripts, notebooks, workflows) and artifacts
- ✅ Step 3: Draft new README structure + write “happy path” instructions
- ✅ Step 4: Add AzureML configuration + reproducibility guidance (env/configs)
- ✅ Step 5: Add end-to-end pipeline table (stages, how it runs, artifacts)
- ✅ Step 6: Add Docker + local verification commands (CI-safe where possible)
- ✅ Step 7: Final review (accuracy, links, runnable commands)

### Pending Steps
- (none – all steps completed; see “Success Criteria (Overall)”)

## Preconditions

- Root `README.md` exists and links to module documentation.
- Module-level READMEs exist under `src/**/README.md` and can be referenced (avoid duplicating deep API docs in root README).
- Documentation standards exist under `docs/templates/` (use as formatting guidance, even though it targets module READMEs).

## Non-Goals / Guardrails

- Do **not** invent commands, file names, or paths. Every referenced entrypoint must exist.
- Do **not** introduce new infrastructure patterns in docs (e.g., brand-new CI, Terraform) unless the repo already supports it.
- Keep root README focused on:
  - what the repo does,
  - how to set it up,
  - how to run the main workflows,
  - where artifacts/logs appear,
  - and how to deploy/serve.

## Target README Blueprint (modeled after churn repo)

The upgraded root `README.md` should include (adapted to this repo):

- **Project Overview**
  - Problem statement (Resume NER) + expected outputs.
  - What’s included: training / evaluation / deployment / infra.
- **Local Environment Setup**
  - Python version / tooling assumptions (e.g., uv/uvx if used).
  - Install steps (`pip` or `uv pip`) aligned with repo reality.
- **Azure ML Configuration**
  - How credentials/workspace are configured (e.g., `.env`, `az login`, config files).
  - What must be set (subscription, RG, workspace, compute).
- **Configuration-Driven Workflows**
  - List key config files in `config/` (or wherever) and what they control.
  - “Single source of truth” guidance (avoid duplication with module docs).
- **End-to-End Pipeline**
  - Table: stage → how it runs (local vs AzureML) → key artifacts (MLflow runs, models, ONNX, endpoints).
  - Explicit entrypoints: scripts/notebooks/workflow functions.
- **Running on Azure ML**
  - Minimum commands / steps to submit jobs/pipelines.
  - MLflow experiment/run organization conventions (if applicable).
- **Docker Usage**
  - Build + run commands if Dockerfile exists and is intended.
  - “Matches AzureML environment” statement only if true.
- **Project Limitations & Future Work**
  - Honest gaps and roadmap items (tests/CI, monitoring, promotion stages, drift).
- **Documentation Index**
  - Link to `docs/modules/INDEX.md` and key module READMEs.

## Steps

### Step 0: Align with existing repo documentation conventions

**Tasks**:
1. Use the repo’s markdown conventions (headings, bullet style, link style).
2. Prefer referencing existing module READMEs over duplicating details.
3. Confirm “documentation standards” links are correct (avoid broken paths).

**Success criteria**:
- Root README changes follow repo style and do not conflict with `docs/templates/`.

---

### Step 1: Audit current `README.md` vs. target blueprint

**Tasks**:
1. List what exists today (overview, structure, links).
2. Identify what’s missing vs the blueprint:
   - setup instructions,
   - AzureML config,
   - concrete run commands,
   - end-to-end pipeline table,
   - artifact locations,
   - docker instructions (if applicable),
   - limitations/future work.
3. Record gaps in a short checklist inside this plan (or in an audit note under `docs/implementation_plans/audits/`).

**Success criteria**:
- A clear “gap list” exists and maps 1:1 to README sections we will add.

---

### Step 2: Inventory “real entrypoints” and artifact outputs (truth source)

**Tasks**:
1. Identify the canonical entrypoints for:
   - training (HPO + train),
   - evaluation (selection + benchmarking),
   - deployment (conversion + serving).
2. Locate AzureML-related entrypoints:
   - pipeline/job submission scripts,
   - component specs (if any),
   - environment specs (if any).
3. Identify where outputs land:
   - local `outputs/` folders,
   - MLflow tracking locations,
   - model bundles (ONNX / tokenizer),
   - API artifacts (docker image, endpoint config).

**Recommended repo scan commands** (examples; adjust to repo reality):
```bash
find . -maxdepth 3 -type f -name "run_*.py" -o -name "*pipeline*.py" -o -name "Dockerfile" -o -name "*.ipynb"
find config -maxdepth 2 -type f -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.toml"
find src -maxdepth 5 -type f -path "*workflows*" -name "*.py"
```

**Success criteria**:
- We can point to concrete files for every “How it runs” statement in the README.
- Artifact paths listed in the README exist and match current behavior.

---

### Step 3: Draft the new root README outline and section stubs

**Tasks**:
1. Create the new outline (headings) mirroring the blueprint.
2. Add short, accurate copy for each section (avoid deep API docs).
3. Add a “Quickstart” that selects one canonical flow (e.g., local train + evaluate).

**Success criteria**:
- The README has the complete skeleton with no placeholder sections left empty.

---

### Step 4: Add “Local Environment Setup” + “Azure ML Configuration”

**Tasks**:
1. Write local setup steps:
   - Python version,
   - dependency install,
   - any required system packages (only if truly required).
2. Write AzureML setup steps:
   - authentication,
   - workspace selection,
   - required environment variables/config files,
   - compute assumptions.
3. Link to deeper docs (e.g., `docs/docker_build.md`, `docs/setup_guide.md`) if they exist; otherwise keep root README self-contained for essentials.

**Success criteria**:
- A new user can run at least one local workflow with only the README + repo files.
- AzureML prerequisites are explicit and minimal.

---

### Step 5: Add “Configuration-Driven Workflows” section

**Tasks**:
1. Enumerate key config files under `config/` (or actual location).
2. For each, add:
   - what it controls,
   - which scripts/workflows read it,
   - what typical values look like (brief; link to file for details).

**Success criteria**:
- Config files are described as the SSOT for behavior (no duplicated conflicting instructions).

---

### Step 6: Add end-to-end pipeline table (stage → how → artifacts)

**Tasks**:
1. Create a table similar to the churn README:
   - Stage (HPO, train, evaluate, convert, serve/deploy)
   - How it runs (local script / notebook / AzureML pipeline)
   - Key artifacts (paths + MLflow runs)
2. Ensure every stage links to:
   - the entrypoint file,
   - and the relevant module README for details.

**Success criteria**:
- The table is complete, accurate, and uses repo-true file paths.

---

### Step 7: Add Docker usage (only if supported) + final link/command validation

**Tasks**:
1. If Dockerfile exists and is intended for users:
   - document build/run,
   - clarify relationship to AzureML environment (only if true).
2. Validate all markdown links in the root README (paths exist).
3. Validate commands are runnable (or clearly labeled as “Azure-only”).

**Success criteria**:
- No broken links in root README.
- Commands are accurate, minimal, and appropriately scoped (local vs AzureML).

## Success Criteria (Overall)

- Root `README.md` enables a new developer to:
  - understand the project quickly,
  - set up locally,
  - run at least one “happy path” workflow,
  - understand AzureML submission prerequisites,
  - locate key artifacts and MLflow runs,
  - and find deeper documentation.
- README mirrors the churn README’s strengths (reproducibility, config-driven workflows, end-to-end clarity) without claiming features this repo doesn’t have.

## Notes / Reuse-First Decision

- **Existing options considered**: `docs/templates/TEMPLATE-documentation_standards.md`, `docs/docker_build.md`, module READMEs under `src/**/README.md`.
- **Reason new plan is necessary**: Those documents target module-level docs; this plan focuses on **repo-level onboarding and workflow execution** in an AzureML-style narrative, similar to the reference churn project.


