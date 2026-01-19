"""
@meta
type: utility
domain: docs
responsibility:
  - Run docs_update in check-only mode
  - Fail if README drift is detected
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Support both direct execution and module import
try:
    from .docs_update import run_docs_update
except ImportError:
    # Fallback for direct execution: add scripts dir to path
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from docs_update import run_docs_update  # type: ignore[no-redef]


def run_docs_check(diff_range: str) -> int:
    # First, run the updater against the working tree.
    changed = run_docs_update(diff_range)

    # Then, check if any src/**/README.md files are now dirty.
    repo_root = Path(__file__).resolve().parents[4]
    pattern = "src/**/README.md"
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )
    dirty_readmes = [
        path for path in result.stdout.splitlines() if path.startswith("src/") and path.endswith("README.md")
    ]

    if dirty_readmes:
        print("README drift detected in the following files:")
        for path in sorted(dirty_readmes):
            print(f"  - {path}")
        print("Run the docs update command locally and commit the changes:")
        print("  uvx python .cursor/rules/module-readmes-two-tier/scripts/docs_update.py --diff <range>")
        return 1

    # Link check: validate relative links inside module READMEs and the curated template.
    try:
        from .check_markdown_links import find_broken_links  # type: ignore[attr-defined]
    except ImportError:
        scripts_dir = Path(__file__).resolve().parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from check_markdown_links import find_broken_links  # type: ignore[attr-defined,no-redef]

    # Only scan `src/**/README.md` for link drift in CI.
    broken_links = find_broken_links([repo_root / "src"])
    if broken_links:
        print("Broken relative markdown links detected:")
        for item in broken_links:
            print(f"- source: {item.source_file}")
            print(f"  target: {item.target}")
            print(f"  resolved: {item.resolved_path}")
        return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Check module README drift from git diff.")
    parser.add_argument(
        "--diff",
        required=True,
        help="Diff range to pass to `git diff --name-status`, e.g. 'HEAD~1..HEAD' or 'origin/main...HEAD'.",
    )
    args = parser.parse_args()

    try:
        code = run_docs_check(args.diff)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc

    sys.exit(code)


if __name__ == "__main__":
    main()


