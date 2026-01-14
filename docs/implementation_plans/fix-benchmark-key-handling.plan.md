# Fix Benchmark Key Handling: Idempotency & Best Model Selection

## Overview

### Purpose

Fix critical issues in benchmark handling that cause:
1. **Weak idempotency**: Skips benchmarking based on `trial_key_hash` alone, ignoring benchmark config differences
2. **Outlier bias**: Best model selection picks "best latency ever" across multiple benchmark runs, not representative latency
3. **Missing deduplication**: No aggregation of multiple benchmark runs with same `benchmark_key`

### Current Problems

#### Problem 1: Idempotency Check is Too Weak

**Current behavior:**
- `filter_missing_benchmarks()` checks for ANY finished benchmark with `(trial_key_hash, study_key_hash)`
- Ignores benchmark config differences (batch size, seq length, device, etc.)
- Can skip needed benchmarks when config changes

**Example:**
- Benchmark exists with `batch_size=1, max_length=512`
- Config changes to `batch_size=8, max_length=256`
- System skips benchmarking because `trial_key_hash` matches
- Later uses stale latency from old config

**Root cause:**
- `_benchmark_exists_in_mlflow()` uses `trial_key_hash` + `study_key_hash` as PRIMARY check
- `benchmark_key` (which includes `benchmark_config_hash`) is only used as FALLBACK
- This is backwards - `benchmark_key` should be PRIMARY

#### Problem 2: Best Model Selection Picks Outlier Latency

**Current behavior:**
- `find_best_model_from_mlflow()` processes ALL benchmark runs
- Creates separate candidates for each benchmark run with same `trial_key_hash`
- All candidates have same F1 score, different latency
- Selects candidate with best (lowest) latency → picks outlier

**Example:**
- 3 benchmark runs for same trial:
  - Run 1: latency=200ms (normal)
  - Run 2: latency=150ms (lucky outlier)
  - Run 3: latency=210ms (normal)
- System picks Run 2 (150ms) as "best"
- This is not representative of actual performance

**Root cause:**
- No deduplication by `benchmark_key` before creating candidates
- No aggregation (median/latest) of multiple runs with same `benchmark_key`

#### Problem 3: Missing benchmark_key Tag

**Current behavior:**
- `build_benchmark_key()` creates proper key including config hash
- But `benchmark_key` tag may not be set on MLflow runs
- Falls back to hash-based search (which is less reliable)

**Root cause:**
- Benchmarking code may not be setting `benchmark_key` tag on MLflow runs
- Need to verify and ensure tag is set

## Solution Design

### Key Principles

1. **benchmark_key as Primary Identity**: Use `benchmark_key` (includes config hash) as primary check, not `trial_key_hash`
2. **Deduplication Before Aggregation**: Group by `(study_key_hash, trial_key_hash, benchmark_key)` before creating candidates
3. **Robust Latency Aggregation**: Use median or latest, not best (outlier)
4. **Backward Compatibility**: Support runs without `benchmark_key` tag (fallback to hash-based)

### Architecture Changes

```
Current Flow:
1. filter_missing_benchmarks() → checks by trial_key_hash (WRONG)
2. find_best_model_from_mlflow() → processes all runs, picks best latency (OUTLIER BIAS)

Fixed Flow:
1. filter_missing_benchmarks() → checks by benchmark_key (CORRECT)
2. find_best_model_from_mlflow() → deduplicates by benchmark_key, aggregates latency (ROBUST)
```

## Implementation Steps

### Step 1: Fix Benchmark Idempotency Check

**File:** `src/evaluation/benchmarking/orchestrator.py`

**Changes:**
1. Make `benchmark_key` PRIMARY check in `_benchmark_exists_in_mlflow()`
2. Use `trial_key_hash` + `study_key_hash` as FALLBACK only (backward compatibility)
3. Update docstring to reflect correct priority

**Code:**

```python
def _benchmark_exists_in_mlflow(
    benchmark_key: str,
    benchmark_experiment: Dict[str, str],
    mlflow_client: Any,
    trial_key_hash: Optional[str] = None,  # Fallback only
    study_key_hash: Optional[str] = None,  # Fallback only
) -> bool:
    """
    Check if benchmark run exists in MLflow with matching benchmark_key.
    
    Priority:
    1. benchmark_key tag (PRIMARY - includes config hash)
    2. trial_key_hash + study_key_hash (FALLBACK - backward compatibility)
    
    Args:
        benchmark_key: Stable benchmark key (includes config hash)
        benchmark_experiment: Benchmark experiment info (name, id)
        mlflow_client: MLflow client instance
        trial_key_hash: Optional trial key hash (fallback only)
        study_key_hash: Optional study key hash (fallback only)
        
    Returns:
        True if benchmark run exists and is finished, False otherwise
    """
    # PRIMARY: Check by benchmark_key tag (most reliable - includes config hash)
    try:
        runs = mlflow_client.search_runs(
            experiment_ids=[benchmark_experiment["id"]],
            filter_string=f"tags.benchmark_key = '{benchmark_key}'",
            max_results=10,
        )
        finished_runs = [r for r in runs if r.info.status == "FINISHED"]
        if finished_runs:
            logger.debug(
                f"Found {len(finished_runs)} finished benchmark run(s) with benchmark_key={benchmark_key[:32]}..."
            )
            return True
    except Exception as e:
        logger.debug(f"benchmark_key tag search failed: {e}")
    
    # FALLBACK: Check by trial_key_hash + study_key_hash (backward compatibility)
    # Only use this if benchmark_key tag is not set (older runs)
    if trial_key_hash and study_key_hash:
        try:
            trial_key_tag = "code.grouping.trial_key_hash"
            study_key_tag = "code.grouping.study_key_hash"
            
            try:
                from infrastructure.naming.mlflow.tags_registry import load_tags_registry
                tags_registry = load_tags_registry()
                trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
                study_key_tag = tags_registry.key("grouping", "study_key_hash")
            except Exception:
                # Fallback to hardcoded keys (backward compatibility)
                pass
            
            filter_string = f"tags.{trial_key_tag} = '{trial_key_hash}' AND tags.{study_key_tag} = '{study_key_hash}'"
            runs = mlflow_client.search_runs(
                experiment_ids=[benchmark_experiment["id"]],
                filter_string=filter_string,
                max_results=10,
            )
            
            finished_runs = [r for r in runs if r.info.status == "FINISHED"]
            if finished_runs:
                logger.warning(
                    f"Found {len(finished_runs)} finished benchmark run(s) by hash (fallback). "
                    f"Consider setting benchmark_key tag for more reliable idempotency. "
                    f"trial_key_hash={trial_key_hash[:16]}..."
                )
                return True
        except Exception as e:
            logger.debug(f"Hash-based fallback search failed: {e}")
    
    return False
```

### Step 2: Add Benchmark Key Deduplication in Best Model Selection

**File:** `src/evaluation/selection/mlflow_selection.py`

**Changes:**
1. Group benchmark runs by `(study_key_hash, trial_key_hash, benchmark_key)` before creating candidates
2. Aggregate latency per group (median or latest, configurable)
3. Create one candidate per group (not per run)

**Code:**

```python
# In find_best_model_from_mlflow(), after Step 2 (preloading runs)

# Step 2.5: Group benchmark runs by (study_key_hash, trial_key_hash, benchmark_key)
# This deduplicates multiple benchmark runs with same config
from collections import defaultdict

benchmark_groups = defaultdict(list)
for benchmark_run in valid_benchmark_runs:
    study_hash = benchmark_run.data.tags[study_key_tag]
    trial_hash = benchmark_run.data.tags[trial_key_tag]
    
    # Get benchmark_key from tag (primary) or construct fallback
    benchmark_key = benchmark_run.data.tags.get("benchmark_key")
    if not benchmark_key:
        # Fallback: use trial_key_hash as key (backward compatibility)
        # This groups all runs without benchmark_key tag together
        benchmark_key = f"legacy_{trial_hash}"
        logger.debug(
            f"Benchmark run {benchmark_run.info.run_id[:12]}... missing benchmark_key tag, "
            f"using fallback key"
        )
    
    key = (study_hash, trial_hash, benchmark_key)
    benchmark_groups[key].append(benchmark_run)

logger.info(
    f"Grouped {len(valid_benchmark_runs)} benchmark runs into {len(benchmark_groups)} unique groups "
    f"(by study_key_hash, trial_key_hash, benchmark_key)"
)

# Step 3: Join benchmark groups with trial runs and refit runs
candidates = []

# Get latency aggregation strategy from config
latency_aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
# Options: "latest" (use most recent), "median" (use median latency), "mean" (use mean latency)

for (study_hash, trial_hash, benchmark_key), benchmark_runs in benchmark_groups.items():
    # Aggregate latency across multiple runs with same benchmark_key
    latencies = [
        r.data.metrics.get("latency_batch_1_ms")
        for r in benchmark_runs
        if r.data.metrics.get("latency_batch_1_ms") is not None
    ]
    
    if not latencies:
        logger.warning(
            f"No valid latency found for group (study={study_hash[:8]}..., "
            f"trial={trial_hash[:8]}..., benchmark_key={benchmark_key[:16]}...)"
        )
        continue
    
    # Select representative benchmark run based on aggregation strategy
    if latency_aggregation == "median":
        import statistics
        target_latency = statistics.median(latencies)
        # Use run with latency closest to median
        representative_run = min(
            benchmark_runs,
            key=lambda r: abs(r.data.metrics.get("latency_batch_1_ms", float('inf')) - target_latency)
        )
        aggregated_latency = target_latency
    elif latency_aggregation == "mean":
        aggregated_latency = sum(latencies) / len(latencies)
        # Use run with latency closest to mean
        representative_run = min(
            benchmark_runs,
            key=lambda r: abs(r.data.metrics.get("latency_batch_1_ms", float('inf')) - aggregated_latency)
        )
    else:  # "latest" (default)
        # Use most recent run
        representative_run = max(
            benchmark_runs,
            key=lambda r: r.info.start_time if r.info.start_time else 0
        )
        aggregated_latency = representative_run.data.metrics.get("latency_batch_1_ms")
    
    if len(benchmark_runs) > 1:
        logger.debug(
            f"Aggregated {len(benchmark_runs)} benchmark runs for group "
            f"(study={study_hash[:8]}..., trial={trial_hash[:8]}...): "
            f"latencies={[f'{l:.1f}ms' for l in latencies]}, "
            f"aggregated={aggregated_latency:.1f}ms (strategy={latency_aggregation})"
        )
    
    benchmark_run = representative_run
    
    # Look up matching trial run (for metrics - has macro-f1)
    key = (study_hash, trial_hash)
    trial_run = trial_lookup.get(key)
    
    if trial_run is None:
        continue
    
    # Get F1 score from trial run
    f1_score = trial_run.data.metrics.get(objective_metric)
    if f1_score is None:
        continue
    
    # Look up matching refit run (for artifacts - has checkpoint)
    refit_run = refit_lookup.get(key)
    artifact_run = refit_run if refit_run is not None else trial_run
    
    # Get backbone from trial run
    backbone = (
        trial_run.data.params.get("backbone") or
        trial_run.data.tags.get(backbone_tag) or
        trial_run.data.tags.get("code.model", "unknown")
    )
    
    candidates.append({
        "benchmark_run": benchmark_run,
        "trial_run": trial_run,
        "artifact_run": artifact_run,
        "refit_run": refit_run,
        "f1_score": float(f1_score),
        "latency_ms": float(aggregated_latency),  # Use aggregated latency
        "backbone": backbone,
        "study_key_hash": study_hash,
        "trial_key_hash": trial_hash,
        "benchmark_key": benchmark_key,  # Include for debugging
        "benchmark_runs_count": len(benchmark_runs),  # Include for debugging
    })
```

### Step 3: Ensure benchmark_key Tag is Set

**File:** `src/evaluation/benchmarking/orchestrator.py` or `src/evaluation/benchmarking/utils.py`

**Changes:**
1. Verify that `benchmark_key` tag is set when creating MLflow benchmark runs
2. If not set, add code to set it

**Check:**
- Search for where benchmark runs are created/logged
- Ensure `benchmark_key` tag is set

**Code (if needed):**

```python
# In benchmark_champions() or run_benchmarking()
benchmark_key = build_benchmark_key(
    champion_run_id=champion_run_id,
    data_fingerprint=data_fingerprint,
    eval_fingerprint=eval_fingerprint,
    benchmark_config=benchmark_config,
)

# Ensure benchmark_key tag is set on MLflow run
if benchmark_tracker:
    benchmark_tracker.set_tag("benchmark_key", benchmark_key)
```

### Step 4: Update Configuration Files

**File:** `config/best_model_selection.yaml`

**Changes:**
1. Add `latency_aggregation` option to `benchmark` section
2. Document the options and default behavior

**Code:**

```yaml
# Benchmark requirements
benchmark:
  required_metrics:
    - "latency_batch_1_ms"
  
  # Latency aggregation strategy when multiple benchmark runs exist with same benchmark_key
  # Options:
  #   - "latest": Use most recent benchmark run (default, simple)
  #   - "median": Use median latency across all runs (most robust against outliers)
  #   - "mean": Use mean latency across all runs (balanced)
  # 
  # This prevents "best latency ever" bias when same trial is benchmarked multiple times
  latency_aggregation: "latest"  # "latest" | "median" | "mean"
```

**File:** `config/benchmark.yaml`

**Changes:**
1. Add documentation about `benchmark_key` and idempotency
2. Clarify that idempotency is based on `benchmark_key` (includes config hash)

**Code:**

```yaml
# Benchmarking configuration for inference performance measurement

# Run mode configuration
run:
  # Run mode determines overall behavior:
  # - reuse_if_exists: Reuse existing benchmark results if found (default)
  # - force_new: Always create new benchmark run (ignores existing)
  # 
  # Idempotency check:
  # - Uses benchmark_key (includes champion_run_id, data_fp, eval_fp, benchmark_config_hash)
  # - Skips benchmarking if finished run exists with matching benchmark_key
  # - Falls back to trial_key_hash + study_key_hash for backward compatibility
  mode: reuse_if_exists

benchmarking:
  # Batch sizes to test during benchmarking
  batch_sizes: [1]  # [1, 8, 16]
  
  # Number of iterations per batch size for statistical significance
  iterations: 10
  
  # Number of warmup iterations before measurement
  warmup_iterations: 10
  
  # Maximum sequence length for benchmarking
  max_length: 512
  
  # Device preference (null = auto-detect, "cuda", or "cpu")
  device: null
  
  # Test data source (relative to config dir or absolute path)
  # Can reference data config's test split or use separate test file
  # If null, will try dataset/test.json, then dataset/validation.json
  test_data: null

# Output configuration
output:
  # Filename for benchmark results
  filename: "benchmark.json"
```

## Testing Plan

### Test 1: Idempotency with Config Change

**Scenario:**
1. Run benchmarking with `batch_size=1, max_length=512`
2. Change config to `batch_size=8, max_length=256`
3. Run benchmarking again

**Expected:**
- First run: Creates benchmark
- Second run: Creates NEW benchmark (different `benchmark_key` due to config change)
- Both benchmarks exist in MLflow

### Test 2: Idempotency with Same Config

**Scenario:**
1. Run benchmarking with `batch_size=1, max_length=512`
2. Run benchmarking again with same config

**Expected:**
- First run: Creates benchmark
- Second run: Skips (finds existing benchmark with matching `benchmark_key`)

### Test 3: Best Model Selection with Multiple Benchmark Runs

**Scenario:**
1. Create 3 benchmark runs for same trial with same config:
   - Run 1: latency=200ms
   - Run 2: latency=150ms (outlier)
   - Run 3: latency=210ms
2. Run best model selection

**Expected:**
- With `latency_aggregation: "latest"`: Uses Run 3 (210ms)
- With `latency_aggregation: "median"`: Uses median (200ms)
- With `latency_aggregation: "mean"`: Uses mean (~186.7ms)
- Does NOT pick Run 2 (outlier)

### Test 4: Backward Compatibility

**Scenario:**
1. Use existing benchmark runs without `benchmark_key` tag
2. Run idempotency check and best model selection

**Expected:**
- Falls back to `trial_key_hash` + `study_key_hash` check
- Works correctly (backward compatible)
- Logs warning about missing `benchmark_key` tag

## Migration Notes

### Backward Compatibility

- Existing benchmark runs without `benchmark_key` tag will still work
- Falls back to `trial_key_hash` + `study_key_hash` check
- New runs will have `benchmark_key` tag set automatically

### Breaking Changes

- None - changes are backward compatible
- Existing behavior preserved for runs without `benchmark_key` tag

### Performance Impact

- Minimal: Additional grouping step in best model selection
- Slightly more MLflow queries (one per `benchmark_key` instead of per run)
- Overall faster due to fewer candidates to process

## Success Criteria

1. ✅ Idempotency check uses `benchmark_key` as PRIMARY check
2. ✅ Best model selection deduplicates by `benchmark_key` before aggregation
3. ✅ Latency aggregation uses median/latest (not best outlier)
4. ✅ `benchmark_key` tag is set on all new benchmark runs
5. ✅ Backward compatibility maintained for runs without `benchmark_key` tag
6. ✅ Configuration allows choosing aggregation strategy

## Implementation Priority

**Priority: HIGH** - These are correctness issues that can lead to:
- Stale benchmark results being used
- Outlier bias in model selection
- Inconsistent benchmarking behavior

## Related Files

- `src/evaluation/benchmarking/orchestrator.py` - Idempotency check
- `src/evaluation/selection/mlflow_selection.py` - Best model selection
- `config/best_model_selection.yaml` - Latency aggregation config
- `config/benchmark.yaml` - Benchmark config documentation

## Next Steps

1. Implement Step 1 (Fix idempotency check)
2. Implement Step 2 (Add deduplication in best model selection)
3. Verify Step 3 (benchmark_key tag is set)
4. Update config files (Step 4)
5. Run tests
6. Update documentation


