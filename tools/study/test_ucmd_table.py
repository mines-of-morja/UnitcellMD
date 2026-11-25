import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ucmd_table import write_table


def test_the_file_is_exactly_this(tmp_path: Path) -> None:
    path = write_table(
        tmp_path / "t" / "runs.tsv",
        "Title",
        ["knob", "x", "y", "ok"],
        [["zeta", 2 / 3, None, True], ["base", 1, float("nan"), False]],
        notes=["a note"],
        plot={"x": "x", "y": "y", "group": "knob"},
    )
    assert path.read_text() == (
        "# ucmd-table 1\n# title: Title\n# note: a note\n# plot: x=x y=y group=knob\n"
        "knob\tx\ty\tok\nzeta\t0.666667\t\tyes\nbase\t1\tnan\tno\n"
    )
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize(
    "columns, rows, plot",
    [
        (["a", "a"], [], None),
        (["a", "b"], [["1"]], None),
        (["a", "b"], [["1\t2", "3"]], None),
        (["a", "b"], [], {"x": "a", "y": "c"}),
        (["a", "b"], [], {"x": "a"}),
    ],
)
def test_bad_tables_are_refused(tmp_path: Path, columns, rows, plot) -> None:
    with pytest.raises(ValueError):
        write_table(tmp_path / "t.tsv", "T", columns, rows, plot=plot)
    assert not (tmp_path / "t.tsv").exists()
