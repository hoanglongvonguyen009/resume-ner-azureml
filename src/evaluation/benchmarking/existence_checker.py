"""Benchmark existence checking utilities."""

from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def _is_valid_uuid(run_id: Optional[str]) -> bool:
    """
    Check if a run_id is a valid UUID format.
    
    Args:
        run_id: Run ID string to validate
        
    Returns:
        True if valid UUID format, False otherwise
    """
    if not run_id:
        return False
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(run_id))


def benchmark_exists_in_mlflow(
    benchmark_key: str,
    benchmark_experiment: Dict[str, str],
    mlflow_client: Any,
    trial_key_hash: Optional[str] = None,  # Fallback only
    study_key_hash: Optional[str] = None,  # Fallback only
    config_dir: Optional[Path] = None,
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
        config_dir: Optional config directory path
        
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
                tags_registry = load_tags_registry(config_dir=config_dir)
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


def benchmark_exists_on_disk(
    benchmark_key: str,
    root_dir: Path,
    environment: str,
) -> bool:
    """
    Check if benchmark file exists on disk.
    
    Args:
        benchmark_key: Stable benchmark key
        root_dir: Root directory of the project
        environment: Platform environment (local, colab, kaggle)
        
    Returns:
        True if benchmark file exists, False otherwise
    """
    cache_dir = root_dir / "outputs" / "benchmarking" / environment / "cache"
    benchmark_file = cache_dir / f"benchmark_{benchmark_key}.json"
    
    return benchmark_file.exists() if benchmark_file else False


def benchmark_already_exists(
    benchmark_key: str,
    benchmark_experiment: Dict[str, str],
    root_dir: Path,
    environment: str,
    mlflow_client: Optional[Any] = None,
    trial_key_hash: Optional[str] = None,
    study_key_hash: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> bool:
    """
    Check if benchmark exists (MLflow or disk).
    
    Args:
        benchmark_key: Stable benchmark key (from build_benchmark_key)
        benchmark_experiment: Benchmark experiment info (name, id)
        root_dir: Root directory of the project
        environment: Platform environment (local, colab, kaggle)
        mlflow_client: Optional MLflow client instance
        trial_key_hash: Optional trial key hash (fallback only)
        study_key_hash: Optional study key hash (fallback only)
        config_dir: Optional config directory path
        
    Returns:
        True if benchmark already exists, False otherwise
    """
    # Derive config_dir from root_dir if not provided
    if config_dir is None:
        config_dir = root_dir / "config"
    
    # Check MLflow first (authoritative)
    if mlflow_client:
        try:
            if benchmark_exists_in_mlflow(
                benchmark_key, 
                benchmark_experiment, 
                mlflow_client,
                trial_key_hash=trial_key_hash,
                study_key_hash=study_key_hash,
                config_dir=config_dir,
            ):
                return True
        except Exception as e:
            logger.debug(f"MLflow check failed: {e}, falling back to disk check")
    
    # Fallback to disk
    if benchmark_exists_on_disk(benchmark_key, root_dir, environment):
        return True
    
    return False

