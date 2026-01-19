"""
@meta
type: test
scope: unit
domain: docs
covers:
  - markdown relative link parsing
  - broken link detection
excludes:
  - network requests
  - external tools
tags:
  - fast
  - ci-safe
"""

from pathlib import Path
import sys


scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from check_markdown_links import find_broken_links_in_text  # type: ignore[attr-defined]


def _fixture_text(name: str) -> str:
    fixture_path = scripts_dir / "fixtures" / "links" / name
    return fixture_path.read_text(encoding="utf-8")


def test_good_links_fixture_has_no_broken_links() -> None:
    source = (scripts_dir / "fixtures" / "links" / "good_links.md").resolve()
    text = _fixture_text("good_links.md")
    broken = find_broken_links_in_text(source, text)
    assert broken == []


def test_bad_links_fixture_reports_broken_links() -> None:
    source = (scripts_dir / "fixtures" / "links" / "bad_links.md").resolve()
    text = _fixture_text("bad_links.md")
    broken = find_broken_links_in_text(source, text)
    assert len(broken) == 2


def test_template_links_resolve_when_using_module_base_dir() -> None:
    template_path = (scripts_dir.parent / "templates" / "module-readme-curated-template.md").resolve()
    template_text = template_path.read_text(encoding="utf-8")
    # The template is intended to be copied into `src/<module>/README.md`, so resolve relative links
    # against an existing module directory.
    repo_root = Path(__file__).resolve().parents[4]
    base_dir = (repo_root / "src" / "common").resolve()
    broken = find_broken_links_in_text(template_path, template_text, base_dir=base_dir)
    assert broken == []


