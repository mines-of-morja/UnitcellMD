"""Write a result table that the GUI shows on a page of its own (docs/design/B2c.md §3.5).

    write_table(HERE / "tables/runs.tsv", "Title", columns, rows,
                notes=["shown above the table"], plot={"x": "x", "y": "kappa", "group": "knob"})

A cell is a string, a number, a bool or None (no value). Numbers keep 6 significant digits; the
full precision stays in the analysis' own JSON. The standard library only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from pathlib import Path

MAGIC = "# ucmd-table 1"
Cell = str | int | float | bool | None


def _text(value: Cell) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.6g}" if math.isfinite(value) else "nan"
    text = str(value)
    if "\t" in text or "\n" in text:
        raise ValueError(f"a cell cannot hold a tab or a line break: {text!r}")
    return text


def write_table(
    path: Path,
    title: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Cell]],
    notes: Sequence[str] = (),
    plot: dict[str, str] | None = None,
) -> Path:
    if len(set(columns)) != len(columns):
        raise ValueError("two columns have the same name")
    lines = [MAGIC, f"# title: {_text(title)}", *(f"# note: {_text(n)}" for n in notes)]
    if plot:
        missing = [c for c in plot.values() if c not in columns]
        if missing or not {"x", "y"} <= plot.keys():
            raise ValueError(f"plot needs x and y and existing columns, missing: {missing}")
        lines.append("# plot: " + " ".join(f"{k}={v}" for k, v in plot.items()))
    lines.append("\t".join(_text(c) for c in columns))
    for row in rows:
        if len(row) != len(columns):
            raise ValueError(f"{len(row)} cells, {len(columns)} columns: {row!r}")
        lines.append("\t".join(_text(c) for c in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)  # the GUI never reads half a table
    return path
