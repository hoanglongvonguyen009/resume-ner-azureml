"""
@meta
type: utility
domain: docs
responsibility:
  - Safely rewrite the generated README marker block
  - Preserve curated content outside markers
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple
import json

START_MARKER = "<!-- AUTO-GENERATED:START -->"
END_MARKER = "<!-- AUTO-GENERATED:END -->"


def _find_marker_indices(lines: Iterable[str]) -> Tuple[int | None, int | None, int, int]:
    """
    Find indices of START and END markers and count occurrences.

    Returns (start_index, end_index, start_count, end_count).
    """

    start_index: int | None = None
    end_index: int | None = None
    start_count = 0
    end_count = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == START_MARKER:
            start_count += 1
            if start_index is None:
                start_index = idx
        if stripped == END_MARKER:
            end_count += 1
            if end_index is None:
                end_index = idx

    return start_index, end_index, start_count, end_count


def render_generated_block(evidence: dict) -> str:
    """
    Render the generated README block from evidence.

    Initial minimal implementation:
    - Module heading
    - Simple file list summary
    """

    module_name = evidence.get("module_name", "unknown-module")
    files = sorted(evidence.get("files", []))

    lines = [
        f"### Auto-generated overview for `{module_name}`",
        "",
        "This section is generated from repository structure. Do not edit manually.",
        "",
        "#### Files",
    ]
    for path in files:
        lines.append(f"- `{path}`")

    if not files:
        lines.append("- _(no tracked files found)_")

    return "\n".join(lines) + "\n"


def update_generated_block(readme_text: str, evidence: dict) -> str:
    """
    Update only the generated block between markers in the given README text.

    Rules:
    - If exactly one START/END pair exists: replace content between them.
    - If multiple START/END markers or an unmatched pair exists: raise.
    - If no markers exist: insert a single marker block near the top.
    """

    lines = readme_text.splitlines(keepends=True)
    start_index, end_index, start_count, end_count = _find_marker_indices(lines)

    if start_count > 1 or end_count > 1:
        raise ValueError("Multiple AUTO-GENERATED markers found; refusing to modify README.")
    if (start_count == 0 and end_count > 0) or (start_count > 0 and end_count == 0):
        raise ValueError("Unmatched AUTO-GENERATED markers; refusing to modify README.")

    generated_body = render_generated_block(evidence)
    generated_block = f"{START_MARKER}\n{generated_body}{END_MARKER}\n"

    # Case 1: markers already exist – replace content between them.
    if start_index is not None and end_index is not None:
        before = "".join(lines[: start_index + 1])
        after = "".join(lines[end_index:])

        # `before` already includes the START line, `after` starts with END line.
        # We want: everything up to START, then generated body, then END and rest.
        # So rebuild around the marker lines.
        before_without_start = "".join(lines[:start_index])
        end_line = lines[end_index]
        after_rest = "".join(lines[end_index + 1 :])

        return f"{before_without_start}{generated_block}{after_rest}"

    # Case 2: no markers – insert a new block.
    # Prefer inserting under "## Module Structure" if present, otherwise after first heading.
    if not lines:
        # Minimal README.
        return f"{generated_block}"

    insert_index = 0
    module_structure_index: int | None = None
    
    # First pass: look for "## Module Structure" section
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "## Module Structure" or stripped.startswith("## Module Structure"):
            module_structure_index = idx + 1
            break
    
    if module_structure_index is not None:
        # Insert right after "## Module Structure" heading
        insert_index = module_structure_index
    else:
        # Fallback: insert after first heading
        for idx, line in enumerate(lines):
            if line.lstrip().startswith("#"):
                insert_index = idx + 1
                continue
            # Stop once we leave the heading region (title + maybe TL;DR).
            if insert_index and not line.strip():
                insert_index = idx + 1
                continue
            if insert_index:
                break

    before = "".join(lines[:insert_index])
    after = "".join(lines[insert_index:])
    return f"{before}{generated_block}{after}"


def update_generated_block_file(readme_path: Path, evidence_path: Path) -> bool:
    """
    Load README and evidence, update generated block, and write back if changed.

    Returns True if the file was modified, False otherwise.
    """

    readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    updated = update_generated_block(readme_text, evidence)

    if updated != readme_text:
        readme_path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    import sys

    if len(sys.argv) != 3:
        raise SystemExit("Usage: update_generated_block.py <readme-path> <evidence-json-path>")

    readme_path = Path(sys.argv[1])
    evidence_path = Path(sys.argv[2])
    changed = update_generated_block_file(readme_path, evidence_path)
    if changed:
        print(f"Updated generated block in {readme_path}")
    else:
        print(f"No changes for {readme_path}")


if __name__ == "__main__":
    main()


