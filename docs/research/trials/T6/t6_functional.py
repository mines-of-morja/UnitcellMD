"""Trial T6, stage 1: choose the DFT functional by the pre-registered rule (Amendments 1 and 3).

    python3 docs/research/trials/T6/t6_functional.py MP2.json LABEL=DFT.json [LABEL=DFT.json ...]
        [--geometry-of LABEL=LABEL ...] [--out OUT.json]

Per functional, against MP2/aug-cc-pVTZ on the single-solvent complexes (EC, EMC, PC, DMC):
- errors of E_bind (no counterpoise) and of the counterpoise interaction energy at the complex
  geometry: 8 numbers; the largest absolute one ranks the functional;
- the condition: the EC − EMC difference of E_bind within 1 kcal/mol of MP2's;
- Li–O(carbonyl) distances; deviations above 0.03 Å are flagged.

The functional with the smallest largest error among those that meet the condition is chosen.
The best-ranked one is reported even if it fails the condition. If none meets it, nothing is
chosen: the clusters are not run, and the case goes to the author. --geometry-of names the
functional whose geometries a composite used (ωB97M-V//ωB97X-D, Amendment 3); its Li–O
distances are those. The fit uncertainties of Amendment 2 follow: s_E is the chosen functional's
largest energy error (floor 0.3 kcal/mol), s_d its largest Li–O error (floor 0.01 Å).

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CONDITION_KCALMOL = 1.0
FLAG_ANGSTROM = 0.03
FLOOR_D, FLOOR_E = 0.01, 0.3  # Å, kcal/mol (Amendment 2)
SOLVENTS = ("EC", "EMC", "PC", "DMC")


def solvent_of(start: str) -> str:
    m = re.match(r"m0_([A-Z]+)", start)
    if m is None or m.group(1) not in SOLVENTS:
        raise ValueError(f"cannot tell the solvent of {start!r}")
    return m.group(1)


def by_solvent(rows: list[dict]) -> dict[str, dict]:
    out = {solvent_of(r["start"]): r for r in rows}
    missing = set(SOLVENTS) - set(out)
    if missing:
        raise ValueError(f"missing complexes: {sorted(missing)}")
    return out


def li_o(row: dict) -> float:
    """Li–O(carbonyl) distance of a single-solvent complex, Å (DFT or MP2 row)."""
    if "li_o_angstrom" in row:
        return float(row["li_o_angstrom"])
    (d,) = row["li_o_carbonyl"]
    return float(d["li_o_angstrom"])


def assess(label: str, dft: dict[str, dict], mp2: dict[str, dict], geometry: dict | None) -> dict:
    errors = {}
    for s in SOLVENTS:
        errors[f"{s} E_bind"] = dft[s]["e_bind_kcalmol"] - mp2[s]["e_bind_kcalmol"]
        errors[f"{s} E_int_CP"] = (
            dft[s]["e_int_cp_at_complex_kcalmol"] - mp2[s]["e_int_cp_at_complex_kcalmol"]
        )
    diff_dft = dft["EC"]["e_bind_kcalmol"] - dft["EMC"]["e_bind_kcalmol"]
    diff_mp2 = mp2["EC"]["e_bind_kcalmol"] - mp2["EMC"]["e_bind_kcalmol"]
    geo = geometry or dft
    d_err = {s: li_o(geo[s]) - li_o(mp2[s]) for s in SOLVENTS}
    largest = max(abs(e) for e in errors.values())
    return {
        "functional": label,
        "errors_kcalmol": {k: round(v, 3) for k, v in errors.items()},
        "largest_error_kcalmol": round(largest, 3),
        "ec_minus_emc_kcalmol": round(diff_dft, 3),
        "ec_minus_emc_mp2_kcalmol": round(diff_mp2, 3),
        "condition_met": abs(diff_dft - diff_mp2) <= CONDITION_KCALMOL,
        "li_o_angstrom": {s: round(li_o(geo[s]), 4) for s in SOLVENTS},
        "li_o_error_angstrom": {s: round(v, 4) for s, v in d_err.items()},
        "li_o_flagged": [s for s, v in d_err.items() if abs(v) > FLAG_ANGSTROM],
        "s_E_kcalmol": round(max(largest, FLOOR_E), 3),
        "s_d_angstrom": round(max(max(abs(v) for v in d_err.values()), FLOOR_D), 4),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("mp2", type=Path)
    ap.add_argument("dft", nargs="+", help="LABEL=path.json")
    ap.add_argument("--geometry-of", action="append", default=[], help="COMPOSITE=LABEL")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    mp2 = by_solvent(json.loads(args.mp2.read_text()))
    runs = {}
    for item in args.dft:
        label, path = item.split("=", 1)
        runs[label] = by_solvent(json.loads(Path(path).read_text()))
    geometry_of = dict(item.split("=", 1) for item in args.geometry_of)
    rows = [
        assess(label, dft, mp2, runs[geometry_of[label]] if label in geometry_of else None)
        for label, dft in runs.items()
    ]
    rows.sort(key=lambda r: r["largest_error_kcalmol"])
    eligible = [r for r in rows if r["condition_met"]]
    result = {
        "rule": "T6 Amendment 1 (and 3): smallest largest |error| over 8 energies; "
        "EC-EMC within 1 kcal/mol of MP2",
        "ranking": rows,
        "best_ranked": rows[0]["functional"],
        "chosen": eligible[0]["functional"] if eligible else None,
        "geometry_of": geometry_of,
    }
    if not eligible:
        result["note"] = "no functional meets the EC-EMC condition: clusters not run; to the author"
    text = json.dumps(result, indent=1, ensure_ascii=False)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
