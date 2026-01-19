"""
@meta
type: utility
domain: docs
responsibility:
  - Scan markdown files for relative links and report broken targets
inputs:
  - One or more markdown file paths (or directories) under the repo
outputs:
  - Human-readable report to stdout
  - Exit code 0 if no broken links, else 1
tags:
  - docs
  - link-check
  - ci-safe
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence


# Markdown inline link: [text](target)
# We intentionally keep this conservative (no reference-style links for now).
_INLINE_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclass(frozen=True)
class BrokenLink:
    source_file: Path
    target: str
    resolved_path: Path


def _iter_markdown_files(paths: Sequence[Path]) -> Iterator[Path]:
    for p in paths:
        if p.is_dir():
            yield from sorted(p.rglob("*.md"))
        else:
            yield p


def _is_relative_file_link(target: str) -> bool:
    # Exclude obvious non-file targets.
    if not target:
        return False
    if target.startswith("#"):
        return False
    if "://" in target:
        return False
    if target.startswith("mailto:"):
        return False
    return target.startswith("./") or target.startswith("../")


def _strip_fragment_and_query(target: str) -> str:
    # ../file.md#section -> ../file.md
    # ../file.md?x=y -> ../file.md
    base = target.split("#", 1)[0]
    base = base.split("?", 1)[0]
    return base


def find_broken_links_in_text(source_file: Path, markdown_text: str, *, base_dir: Path | None = None) -> List[BrokenLink]:
    broken: List[BrokenLink] = []
    for match in _INLINE_LINK_RE.finditer(markdown_text):
        raw_target = match.group(1).strip()
        if not _is_relative_file_link(raw_target):
            continue

        target = _strip_fragment_and_query(raw_target)
        resolve_from = base_dir if base_dir is not None else source_file.parent
        resolved = (resolve_from / target).resolve()
        if not resolved.exists():
            broken.append(
                BrokenLink(
                    source_file=source_file,
                    target=raw_target,
                    resolved_path=resolved,
                )
            )
    return broken


def _default_base_dir_for_source(repo_root: Path, source_file: Path) -> Path | None:
    """
    Decide a sensible base directory for link resolution.

    For module READMEs under `src/<module>/README.md`, the correct base is the file's directory.
    For templates under the rule package, links are written as if the template were copied into
    `src/<module>/README.md`, so we resolve them against a representative module directory.
    """

    source_str = str(source_file).replace("\\", "/")
    if "/.cursor/rules/module-readmes-two-tier/templates/" in source_str:
        # Any existing module works for sibling-module README links (../infrastructure/README.md, etc.).
        # `src/common` is guaranteed in this repo.
        return repo_root / "src" / "common"
    return None


def find_broken_links(paths: Sequence[Path], *, base_dir: Path | None = None) -> List[BrokenLink]:
    broken: List[BrokenLink] = []
    for md_file in _iter_markdown_files(paths):
        if not md_file.exists():
            broken.append(
                BrokenLink(source_file=md_file, target="(file missing)", resolved_path=md_file.resolve())
            )
            continue
        text = md_file.read_text(encoding="utf-8")
        repo_root = Path(__file__).resolve().parents[4]
        per_file_base = base_dir if base_dir is not None else _default_base_dir_for_source(repo_root, md_file.resolve())
        broken.extend(find_broken_links_in_text(md_file.resolve(), text, base_dir=per_file_base))
    return broken


def _default_target_paths(repo_root: Path) -> List[Path]:
    # Default to checking the curated template (the file you called out),
    # plus all module READMEs under src/.
    return [
        repo_root / ".cursor" / "rules" / "module-readmes-two-tier" / "templates",
        repo_root / "src",
    ]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Check broken relative markdown links.")
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Optional base directory to resolve relative links from (overrides per-file defaults).",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files/directories to scan (default: rule template + src/**/README.md).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(__file__).resolve().parents[4]

    if args.paths:
        targets = [Path(p) for p in args.paths]
    else:
        targets = _default_target_paths(repo_root)

    base_dir = Path(args.base_dir).resolve() if args.base_dir else None
    broken = find_broken_links(targets, base_dir=base_dir)
    if not broken:
        print("No broken relative markdown links found.")
        raise SystemExit(0)

    print("Broken relative markdown links found:")
    for item in broken:
        print(f"- source: {item.source_file}")
        print(f"  target: {item.target}")
        print(f"  resolved: {item.resolved_path}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()


