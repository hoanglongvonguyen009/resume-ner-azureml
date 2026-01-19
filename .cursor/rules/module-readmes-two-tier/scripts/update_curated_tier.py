"""
@meta
type: utility
domain: docs
responsibility:
  - Stub suggestion engine for curated-tier content
  - Never writes files; prints proposed curated content or patches
"""

from __future__ import annotations

import sys
from pathlib import Path


def propose_curated_section(readme_path: Path) -> str:
    """
    Very lightweight stub that returns a placeholder proposal for curated content.

    This is intentionally conservative: it does not attempt to rewrite curated text,
    only to signal where future suggestion logic could hook in.
    """

    title = readme_path.stem
    return (
        f"<!-- CURATED-SUGGESTION:START -->\n"
        f"_Suggested curated summary for `{title}` (no automatic writes yet)._ \n"
        f"<!-- CURATED-SUGGESTION:END -->\n"
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: update_curated_tier.py <readme-path>")

    readme_path = Path(sys.argv[1])
    suggestion = propose_curated_section(readme_path)
    # Print suggestion to stdout; caller may choose how to surface this (patch file, diff, etc.).
    sys.stdout.write(suggestion)


if __name__ == "__main__":
    main()


