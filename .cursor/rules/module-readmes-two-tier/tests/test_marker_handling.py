import pytest
from pathlib import Path
import sys

# Add scripts directory to path for imports
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from update_generated_block import (
    update_generated_block,
)


def _load_fixture(name: str) -> str:
    here = Path(__file__).resolve().parent
    return (here.parent / "scripts" / "fixtures" / "readmes" / name).read_text(encoding="utf-8")


def test_malformed_markers_raise_error() -> None:
    text = _load_fixture("malformed_markers.md")
    with pytest.raises(ValueError):
        update_generated_block(text, {"module_name": "example", "files": []})


def test_duplicate_markers_raise_error() -> None:
    text = _load_fixture("duplicate_markers.md")
    with pytest.raises(ValueError):
        update_generated_block(text, {"module_name": "example", "files": []})


