"""
@meta
type: utility
domain: docs
responsibility:
  - Parse git diff output
  - Compute impacted top-level src modules
  - Emit JSON summary for downstream README tooling
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set


@dataclass(frozen=True)
class ChangedModule:
    """Representation of a single impacted top-level module under src/."""

    name: str


def _is_src_path(path: str) -> bool:
    return path.startswith("src/") and path.count("/") >= 2


def _extract_module_name(path: str) -> str | None:
    """
    Extract top-level module name from a src-relative path.

    Example:
    - src/common/shared/file_utils.py -> common
    - src/training/README.md          -> training
    """

    if not _is_src_path(path):
        return None
    parts = path.split("/")
    if len(parts) < 3:
        return None
    return parts[1]


def _should_trigger_for_path(path: str) -> bool:
    """
    Apply trigger file rules for deciding if a path should mark a module as impacted.

    This intentionally ignores:
    - src/**/README.md
    - obvious build / cache directories (dist, build, __pycache__, .venv)

    More exclusions can be added later as needed.
    """

    if not _is_src_path(path):
        return False

    # Normalize separators just in case.
    normalized = path.replace("\\", "/")

    # Exclude README files – they are outputs of this rule, not triggers.
    if normalized.endswith("/README.md") or normalized == "README.md":
        return False

    # Exclude common generated / build dirs under src.
    excluded_fragments = (
        "/__pycache__/",
        "/.venv/",
        "/dist/",
        "/build/",
        "/outputs/",
        "/mlruns/",
    )
    if any(fragment in normalized for fragment in excluded_fragments):
        return False

    return True


def _parse_diff_lines(lines: Iterable[str]) -> Set[str]:
    """
    Parse `git diff --name-status` style lines and produce impacted module names.

    Handles:
    - A\tpath
    - M\tpath
    - D\tpath
    - R<score>\told_path\tnew_path
    """

    modules: Set[str] = set()

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        parts = line.split("\t")
        if not parts:
            continue

        status = parts[0]

        # Simple A/M/D statuses: A\tpath, M\tpath, D\tpath
        if status in {"A", "M", "D"} and len(parts) >= 2:
            path = parts[1]
            if _should_trigger_for_path(path):
                module = _extract_module_name(path)
                if module:
                    modules.add(module)
            continue

        # Rename statuses: R100\told_path\tnew_path (score may vary)
        if status.startswith("R") and len(parts) >= 3:
            old_path, new_path = parts[1], parts[2]

            old_triggers = _should_trigger_for_path(old_path)
            new_triggers = _should_trigger_for_path(new_path)

            old_module = _extract_module_name(old_path) if old_triggers else None
            new_module = _extract_module_name(new_path) if new_triggers else None

            if old_module and new_module and old_module != new_module:
                modules.add(old_module)
                modules.add(new_module)
            elif old_module and not new_module:
                modules.add(old_module)
            elif new_module and not old_module:
                modules.add(new_module)

    return modules


def changed_modules_from_stdin() -> List[ChangedModule]:
    """Read diff lines from stdin and return sorted list of ChangedModule objects."""

    modules = _parse_diff_lines(sys.stdin)
    sorted_names = sorted(modules)
    return [ChangedModule(name=m) for m in sorted_names]


def main() -> None:
    modules = changed_modules_from_stdin()
    payload = {
        "schema_version": "v1",
        "modules": [{"name": m.name} for m in modules],
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()


