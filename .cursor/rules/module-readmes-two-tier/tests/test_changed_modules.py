from pathlib import Path
import sys

# Add scripts directory to path for imports
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from changed_modules import _parse_diff_lines  # type: ignore[attr-defined]


def _load_fixture(name: str) -> str:
    here = Path(__file__).resolve().parent
    return (here.parent / "scripts" / "fixtures" / "diffs" / name).read_text(encoding="utf-8")


def test_changed_modules_add_modify_delete() -> None:
    text = _load_fixture("add_modify_delete.txt")
    modules = _parse_diff_lines(text.splitlines())
    assert modules == {"common", "training", "evaluation"}


def test_changed_modules_rename_cross_module() -> None:
    text = _load_fixture("rename_cross_module.txt")
    modules = _parse_diff_lines(text.splitlines())
    # common and training both impacted; deployment impacted but script moved out of src so excluded
    assert modules == {"common", "training", "deployment"}


