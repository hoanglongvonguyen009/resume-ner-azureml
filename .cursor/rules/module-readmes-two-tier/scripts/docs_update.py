"""
@meta
type: utility
domain: docs
responsibility:
  - Orchestrate module README updates from git diff
  - Call changed_modules.py, collect_module_evidence.py, update_generated_block.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List

# Support both direct execution and module import
try:
    from .changed_modules import ChangedModule
    from .collect_module_evidence import collect_module_evidence
    from .update_generated_block import update_generated_block_file
except ImportError:
    # Fallback for direct execution: add scripts dir to path
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from changed_modules import ChangedModule  # type: ignore[no-redef]
    from collect_module_evidence import collect_module_evidence  # type: ignore[no-redef]
    from update_generated_block import update_generated_block_file  # type: ignore[no-redef]


def _run_git_diff(diff_range: str) -> str:
    result = subprocess.run(
        ["git", "diff", "--name-status", diff_range],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _parse_changed_modules_from_text(text: str) -> List[ChangedModule]:
    try:
        from .changed_modules import _parse_diff_lines  # type: ignore[attr-defined]
    except ImportError:
        # Fallback for direct execution
        scripts_dir = Path(__file__).resolve().parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from changed_modules import _parse_diff_lines  # type: ignore[attr-defined,no-redef]

    modules = _parse_diff_lines(text.splitlines())
    return [ChangedModule(name=m) for m in sorted(modules)]


def run_docs_update(diff_range: str) -> int:
    repo_root = Path(__file__).resolve().parents[4]
    src_dir = repo_root / "src"

    diff_text = _run_git_diff(diff_range)
    modules = _parse_changed_modules_from_text(diff_text)

    if not modules:
        return 0

    changed_readmes = 0
    for module in modules:
        module_path = src_dir / module.name
        readme_path = module_path / "README.md"

        evidence = collect_module_evidence(module_path)
        evidence_json_path = module_path / ".module_readme_evidence.json"
        evidence_json_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

        try:
            changed = update_generated_block_file(readme_path, evidence_json_path)
        finally:
            # Best-effort cleanup of temporary evidence file.
            try:
                evidence_json_path.unlink()
            except FileNotFoundError:
                pass

        if changed:
            changed_readmes += 1

    return changed_readmes


def main() -> None:
    parser = argparse.ArgumentParser(description="Update module README generated blocks from git diff.")
    parser.add_argument(
        "--diff",
        required=True,
        help="Diff range to pass to `git diff --name-status`, e.g. 'HEAD~1..HEAD' or 'origin/main...HEAD'.",
    )
    args = parser.parse_args()

    try:
        changed = run_docs_update(args.diff)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc

    print(f"Updated {changed} module README(s).")
    sys.exit(0)


if __name__ == "__main__":
    main()


