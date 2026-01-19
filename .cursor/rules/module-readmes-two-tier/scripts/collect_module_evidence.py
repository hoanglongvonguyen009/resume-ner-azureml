"""
@meta
type: utility
domain: docs
responsibility:
  - Collect lightweight evidence for a single src module
  - Emit JSON conforming to module_evidence.schema.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List


def collect_module_evidence(module_path: Path) -> Dict[str, object]:
    """
    Collect a minimal evidence payload for the given module.

    This initial implementation focuses on a stable file list so that the
    generated README block can describe basic module structure. It can be
    extended later to include richer metadata (entrypoints, tests, etc.).
    """

    module_path = module_path.resolve()
    src_dir = module_path.parent
    module_name = module_path.name

    files: List[str] = []
    if module_path.is_dir():
        for path in sorted(module_path.rglob("*")):
            if path.is_file():
                # Store paths relative to the repo root `src/` parent for stability.
                try:
                    rel = path.relative_to(src_dir.parent)
                except ValueError:
                    rel = path
                files.append(str(rel).replace("\\", "/"))

    payload: Dict[str, object] = {
        "schema_version": "v1",
        "module_name": module_name,
        "module_path": str(module_path),
        "files": files,
    }
    return payload


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: collect_module_evidence.py <module-path>")

    module_path = Path(sys.argv[1])
    data = collect_module_evidence(module_path)
    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()


