"""Local MLflow index cache for fast, backend-independent run retrieval."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# fcntl is Unix-only, handle import gracefully for Windows compatibility
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

from shared.json_cache import load_json, save_json
from shared.logging_utils import get_logger
from orchestration.jobs.tracking.mlflow_config_loader import get_index_config

logger = get_logger(__name__)


def get_mlflow_index_path(root_dir: Path, config_dir: Optional[Path] = None) -> Path:
    """
    Get path to mlflow_index.json in cache directory.
    
    Args:
        root_dir: Project root directory.
        config_dir: Optional config directory (defaults to root_dir / "config").
    
    Returns:
        Path to mlflow_index.json file.
    """
    if config_dir is None:
        config_dir = root_dir / "config"
    
    # Use same cache structure as index_manager
    cache_dir = root_dir / "outputs" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Read file_name from config
    index_config = get_index_config(config_dir)
    file_name = index_config.get("file_name", "mlflow_index.json")
    
    return cache_dir / file_name


def _acquire_lock(file_path: Path, timeout: float = 10.0) -> Optional[object]:
    """
    Acquire file lock for atomic writes (Unix/Linux).
    
    Args:
        file_path: Path to file to lock.
        timeout: Maximum time to wait for lock (seconds).
    
    Returns:
        File handle with lock, or None if lock failed.
    """
    if not HAS_FCNTL:
        # Windows or platform without fcntl - return None (fallback to non-atomic)
        return None
    
    try:
        lock_file = file_path.with_suffix('.lock')
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        
        # Try to acquire exclusive lock (non-blocking)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_fd
        except BlockingIOError:
            # Lock is held, wait with timeout
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return lock_fd
                except BlockingIOError:
                    time.sleep(0.1)
            os.close(lock_fd)
            return None
    except (OSError, AttributeError):
        # Windows or lock not available, return None (fallback to non-atomic)
        return None


def _release_lock(lock_fd: Optional[object], file_path: Path) -> None:
    """Release file lock."""
    if not HAS_FCNTL or lock_fd is None:
        return
    
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
        # Remove lock file
        lock_file = file_path.with_suffix('.lock')
        if lock_file.exists():
            try:
                lock_file.unlink()
            except OSError:
                pass
    except (OSError, AttributeError):
        pass


def update_mlflow_index(
    root_dir: Path,
    run_key_hash: str,
    run_id: str,
    experiment_id: str,
    tracking_uri: str,
    config_dir: Optional[Path] = None,
    max_entries: Optional[int] = None,
) -> Path:
    """
    Update index with new run_key_hash → run_id mapping.
    
    Uses file locking for concurrency protection. If locking is not available
    (e.g., Windows), falls back to non-atomic write (with warning).
    
    Args:
        root_dir: Project root directory.
        run_key_hash: SHA256 hash of run_key.
        run_id: MLflow run ID.
        experiment_id: MLflow experiment ID.
        tracking_uri: MLflow tracking URI.
        config_dir: Optional config directory.
        max_entries: Maximum number of entries to keep (LRU eviction). If None, reads from config.
    
    Returns:
        Path to index file.
    
    Raises:
        ValueError: If required parameters are missing.
    """
    if not run_key_hash or not run_id or not experiment_id or not tracking_uri:
        raise ValueError("All parameters (run_key_hash, run_id, experiment_id, tracking_uri) are required")
    
    # Read config for enabled flag and max_entries
    index_config = get_index_config(config_dir)
    enabled = index_config.get("enabled", True)
    
    if not enabled:
        logger.debug("MLflow index disabled in config, skipping update")
        return get_mlflow_index_path(root_dir, config_dir)
    
    # Read max_entries from config if not provided
    if max_entries is None:
        max_entries = index_config.get("max_entries", 1000)
    
    index_path = get_mlflow_index_path(root_dir, config_dir)
    
    # Acquire lock
    lock_fd = _acquire_lock(index_path)
    if lock_fd is None:
        logger.warning(f"Could not acquire lock for {index_path}, proceeding with non-atomic write")
    
    try:
        # Load existing index
        index = load_json(index_path, default={})
        
        # Update entry
        index[run_key_hash] = {
            "run_id": run_id,
            "experiment_id": experiment_id,
            "tracking_uri": tracking_uri,
            "updated_at": datetime.now().isoformat(),
        }
        
        # LRU eviction: keep only most recent max_entries
        if len(index) > max_entries:
            # Sort by updated_at (most recent first)
            sorted_entries = sorted(
                index.items(),
                key=lambda x: x[1].get("updated_at", ""),
                reverse=True
            )
            # Keep only max_entries
            index = dict(sorted_entries[:max_entries])
            logger.debug(f"Evicted {len(sorted_entries) - max_entries} old entries from MLflow index")
        
        # Save index atomically: write to temp file, then rename
        temp_path = index_path.with_suffix('.tmp')
        try:
            save_json(temp_path, index)
            
            # Atomic rename (works on both Unix and Windows)
            if sys.platform == 'win32':
                # Windows: need to remove target first for atomic replace
                if index_path.exists():
                    index_path.unlink()
            temp_path.replace(index_path)  # Atomic on Unix, safe on Windows after unlink
            
            logger.debug(f"Updated MLflow index: {run_key_hash[:16]}... → {run_id[:12]}...")
        except Exception as e:
            # Clean up temp file on error
            temp_path.unlink(missing_ok=True)
            raise
        
    finally:
        # Release lock
        _release_lock(lock_fd, index_path)
    
    return index_path


def find_in_mlflow_index(
    root_dir: Path,
    run_key_hash: str,
    tracking_uri: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Optional[Dict[str, str]]:
    """
    Find run_id in local index by run_key_hash.
    
    Optionally filters by tracking_uri to ensure alignment.
    
    Args:
        root_dir: Project root directory.
        run_key_hash: SHA256 hash of run_key to search for.
        tracking_uri: Optional tracking URI to verify alignment.
        config_dir: Optional config directory.
    
    Returns:
        Dictionary with run_id, experiment_id, tracking_uri if found, None otherwise.
    """
    if not run_key_hash:
        return None
    
    index_path = get_mlflow_index_path(root_dir, config_dir)
    
    if not index_path.exists():
        return None
    
    # Load index
    index = load_json(index_path, default={})
    
    # Lookup
    entry = index.get(run_key_hash)
    if not entry:
        return None
    
    # Verify tracking URI alignment if provided
    if tracking_uri:
        stored_uri = entry.get("tracking_uri", "")
        if stored_uri != tracking_uri:
            logger.warning(
                f"Tracking URI mismatch in index: stored={stored_uri[:50]}..., "
                f"requested={tracking_uri[:50]}..."
            )
            return None
    
    return {
        "run_id": entry.get("run_id"),
        "experiment_id": entry.get("experiment_id"),
        "tracking_uri": entry.get("tracking_uri"),
    }


def get_run_name_counter_path(root_dir: Path, config_dir: Optional[Path] = None) -> Path:
    """
    Get path to run_name_counter.json in cache directory.
    
    Args:
        root_dir: Project root directory.
        config_dir: Optional config directory (defaults to root_dir / "config").
    
    Returns:
        Path to run_name_counter.json file.
    """
    if config_dir is None:
        config_dir = root_dir / "config"
    
    # Use same cache structure as index_manager
    cache_dir = root_dir / "outputs" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    return cache_dir / "run_name_counter.json"


def reserve_run_name_version(
    counter_key: str,
    run_id: str,
    root_dir: Path,
    config_dir: Optional[Path] = None,
) -> int:
    """
    Reserve a version number for a run name using atomic counter store.
    
    Uses reserve/commit pattern to prevent duplicates on crashes.
    Never reuses numbers - always increments from max committed version.
    
    Args:
        counter_key: Counter key (format: "{project}:{process_type}:{run_key_hash}:{env}").
        run_id: MLflow run ID (or "pending" if not yet created).
        root_dir: Project root directory.
        config_dir: Optional config directory.
    
    Returns:
        Reserved version number (starts at 1 if key doesn't exist).
    
    Raises:
        RuntimeError: If lock acquisition fails after timeout.
    """
    counter_path = get_run_name_counter_path(root_dir, config_dir)
    
    logger.info(
        f"[Reserve Version] Starting reservation: counter_key={counter_key[:60]}..., "
        f"root_dir={root_dir}, config_dir={config_dir}, counter_path={counter_path}"
    )
    
    # Acquire lock
    lock_fd = _acquire_lock(counter_path, timeout=10.0)
    if lock_fd is None:
        logger.warning(
            f"[Reserve Version] Could not acquire lock for {counter_path}, "
            f"proceeding with non-atomic write"
        )
    
    try:
        # Load existing allocations
        counter_data = load_json(counter_path, default={"allocations": []})
        allocations: List[Dict[str, any]] = counter_data.get("allocations", [])
        logger.info(
            f"[Reserve Version] Loaded {len(allocations)} existing allocations from {counter_path}"
        )
        
        # Find max committed version for this counter_key
        max_version = 0
        matching_allocations = []
        committed_versions = []
        reserved_versions = []
        expired_versions = []
        
        for alloc in allocations:
            if alloc.get("counter_key") == counter_key:
                matching_allocations.append(alloc)
                status = alloc.get("status", "unknown")
                version = alloc.get("version", 0)
                
                if status == "committed":
                    max_version = max(max_version, version)
                    committed_versions.append(version)
                elif status == "reserved":
                    reserved_versions.append(version)
                elif status == "expired":
                    expired_versions.append(version)
        
        logger.info(
            f"[Reserve Version] Found {len(matching_allocations)} allocations for counter_key: "
            f"committed={committed_versions}, reserved={reserved_versions}, expired={expired_versions}, "
            f"max_committed_version={max_version}"
        )
        
        if matching_allocations:
            logger.info(
                f"[Reserve Version] Allocation details: "
                f"{[(a.get('version'), a.get('status'), a.get('run_id', '')[:12]) for a in matching_allocations]}"
            )
        
        # Increment to get next version (never reuse)
        next_version = max_version + 1
        logger.info(
            f"[Reserve Version] Reserving next version: {next_version} "
            f"(incremented from max_committed={max_version})"
        )
        
        # Add new reservation entry
        new_allocation = {
            "counter_key": counter_key,
            "version": next_version,
            "run_id": run_id,
            "status": "reserved",
            "reserved_at": datetime.now().isoformat(),
            "committed_at": None,
        }
        allocations.append(new_allocation)
        
        # Save atomically
        counter_data["allocations"] = allocations
        temp_path = counter_path.with_suffix('.tmp')
        try:
            save_json(temp_path, counter_data)
            
            # Atomic rename
            if sys.platform == 'win32':
                if counter_path.exists():
                    counter_path.unlink()
            temp_path.replace(counter_path)
            
            logger.info(
                f"[Reserve Version] ✓ Successfully reserved version {next_version} "
                f"for counter_key {counter_key[:50]}... "
                f"(run_id: {run_id[:12] if run_id != 'pending' else 'pending'}...)"
            )
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            logger.error(
                f"[Reserve Version] ✗ Failed to save reservation: {e}",
                exc_info=True
            )
            raise
        
        return next_version
        
    finally:
        _release_lock(lock_fd, counter_path)


def commit_run_name_version(
    counter_key: str,
    run_id: str,
    version: int,
    root_dir: Path,
    config_dir: Optional[Path] = None,
) -> None:
    """
    Commit a reserved version number after MLflow run is successfully created.
    
    Args:
        counter_key: Counter key (must match reservation).
        run_id: MLflow run ID (must match reservation or be "pending").
        version: Version number to commit (must match reservation).
        root_dir: Project root directory.
        config_dir: Optional config directory.
    
    Raises:
        RuntimeError: If lock acquisition fails after timeout.
    """
    counter_path = get_run_name_counter_path(root_dir, config_dir)
    
    logger.info(
        f"[Commit Version] Starting commit: counter_key={counter_key[:60]}..., "
        f"version={version}, run_id={run_id[:12]}..., counter_path={counter_path}"
    )
    
    # Acquire lock
    lock_fd = _acquire_lock(counter_path, timeout=10.0)
    if lock_fd is None:
        logger.warning(
            f"[Commit Version] Could not acquire lock for {counter_path}, proceeding with non-atomic write"
        )
    
    try:
        # Load existing allocations
        counter_data = load_json(counter_path, default={"allocations": []})
        allocations: List[Dict[str, any]] = counter_data.get("allocations", [])
        logger.info(
            f"[Commit Version] Loaded {len(allocations)} existing allocations from {counter_path}"
        )
        
        # Find matching reservation entry
        found = False
        matching_reservations = []
        all_matching = []
        
        for alloc in allocations:
            if alloc.get("counter_key") == counter_key:
                all_matching.append(alloc)
                if alloc.get("version") == version:
                    matching_reservations.append(alloc)
                    if alloc.get("status") == "reserved":
                        # Update to committed
                        old_status = alloc.get("status")
                        alloc["status"] = "committed"
                        alloc["committed_at"] = datetime.now().isoformat()
                        # Update run_id if it was "pending"
                        if alloc.get("run_id") == "pending" or run_id != "pending":
                            alloc["run_id"] = run_id
                        found = True
                        logger.info(
                            f"[Commit Version] ✓ Found and committed reservation: version={version}, "
                            f"status changed from '{old_status}' to 'committed', "
                            f"run_id={run_id[:12]}..., counter_key={counter_key[:50]}..."
                        )
                        break
        
        if not found:
            logger.warning(
                f"[Commit Version] ✗ Could not find reservation to commit: counter_key={counter_key[:50]}..., "
                f"version={version}, run_id={run_id[:12]}... "
            )
            if matching_reservations:
                logger.warning(
                    f"[Commit Version] Found {len(matching_reservations)} matching allocations with version {version}: "
                    f"{[(a.get('version'), a.get('status'), a.get('run_id', '')[:12]) for a in matching_reservations]}"
                )
            if all_matching:
                logger.warning(
                    f"[Commit Version] All allocations for counter_key: "
                    f"{[(a.get('version'), a.get('status'), a.get('run_id', '')[:12]) for a in all_matching]}"
                )
            # Don't fail - idempotent operation
        
        # Save atomically
        counter_data["allocations"] = allocations
        temp_path = counter_path.with_suffix('.tmp')
        try:
            save_json(temp_path, counter_data)
            
            # Atomic rename
            if sys.platform == 'win32':
                if counter_path.exists():
                    counter_path.unlink()
            temp_path.replace(counter_path)
            
            if found:
                logger.info(
                    f"[Commit Version] ✓ Successfully saved committed version {version} to {counter_path}"
                )
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            logger.error(
                f"[Commit Version] ✗ Failed to save commit: {e}",
                exc_info=True
            )
            raise
        
    finally:
        _release_lock(lock_fd, counter_path)


def cleanup_stale_reservations(
    root_dir: Path,
    config_dir: Optional[Path] = None,
    stale_minutes: int = 30,
) -> int:
    """
    Clean up stale "reserved" entries (crashed processes that never committed).
    
    Marks entries older than stale_minutes as "expired" (or removes them).
    
    Args:
        root_dir: Project root directory.
        config_dir: Optional config directory.
        stale_minutes: Minutes after which a reservation is considered stale.
    
    Returns:
        Count of cleaned entries.
    """
    counter_path = get_run_name_counter_path(root_dir, config_dir)
    
    if not counter_path.exists():
        return 0
    
    # Acquire lock
    lock_fd = _acquire_lock(counter_path, timeout=10.0)
    if lock_fd is None:
        logger.warning(f"Could not acquire lock for {counter_path}, skipping cleanup")
        return 0
    
    try:
        # Load existing allocations
        counter_data = load_json(counter_path, default={"allocations": []})
        allocations: List[Dict[str, any]] = counter_data.get("allocations", [])
        
        # Find stale reservations
        now = datetime.now()
        cleaned_count = 0
        updated_allocations = []
        
        for alloc in allocations:
            if alloc.get("status") == "reserved":
                reserved_at_str = alloc.get("reserved_at")
                if reserved_at_str:
                    try:
                        reserved_at = datetime.fromisoformat(reserved_at_str)
                        age_minutes = (now - reserved_at).total_seconds() / 60.0
                        
                        if age_minutes > stale_minutes:
                            # Mark as expired (or remove - we'll mark for now)
                            alloc["status"] = "expired"
                            alloc["expired_at"] = now.isoformat()
                            cleaned_count += 1
                            logger.debug(
                                f"Marked stale reservation as expired: counter_key={alloc.get('counter_key', '')[:50]}..., "
                                f"version={alloc.get('version')}, age={age_minutes:.1f} minutes"
                            )
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid reserved_at timestamp in allocation: {e}")
            
            # Keep all allocations (including expired ones for audit trail)
            updated_allocations.append(alloc)
        
        if cleaned_count > 0:
            # Save atomically
            counter_data["allocations"] = updated_allocations
            temp_path = counter_path.with_suffix('.tmp')
            try:
                save_json(temp_path, counter_data)
                
                # Atomic rename
                if sys.platform == 'win32':
                    if counter_path.exists():
                        counter_path.unlink()
                temp_path.replace(counter_path)
                
                logger.info(f"Cleaned up {cleaned_count} stale reservations")
            except Exception as e:
                temp_path.unlink(missing_ok=True)
                logger.warning(f"Failed to save cleaned allocations: {e}")
        
        return cleaned_count
        
    finally:
        _release_lock(lock_fd, counter_path)
