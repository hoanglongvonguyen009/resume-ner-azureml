from pathlib import Path
import sys

# Add scripts directory to path for imports
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from update_generated_block import (
    START_MARKER,
    END_MARKER,
    update_generated_block,
)


def _load_fixture(name: str) -> str:
    here = Path(__file__).resolve().parent
    return (here.parent / "scripts" / "fixtures" / "readmes" / name).read_text(encoding="utf-8")


def test_update_generated_block_replaces_between_markers_idempotent() -> None:
    original = _load_fixture("good_markers.md")
    evidence = {
        "module_name": "example",
        "files": ["src/example/__init__.py"],
    }

    once = update_generated_block(original, evidence)
    twice = update_generated_block(once, evidence)

    assert START_MARKER in once
    assert END_MARKER in once
    assert once == twice


def test_update_generated_block_inserts_when_missing_markers() -> None:
    text = "# Title\n\nSome text.\n"
    evidence = {"module_name": "example", "files": []}

    updated = update_generated_block(text, evidence)
    assert START_MARKER in updated
    assert END_MARKER in updated


