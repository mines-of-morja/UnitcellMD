"""SC-1: configurational minus displayed temperature per arm (reported, not judged).

    python3 docs/research/timestep/tconf/combine.py      # reads the *.json written by run_all.sh

Per run: T_conf ("all", molecule-centre translation, jackknife error of 8 blocks) minus the mean displayed T of the
same frames. Per arm: mean over the seeds, SE from the spread of the seeds (n - 1), and the mean jackknife error.
"""

import json
import math
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = {"1M_1fs": 3.4, "1M_0p5fs": 0.9, "water_1fs": 6.5, "water_0p5fs": 1.6, "water_0p25fs": 0.4}  # SC-1 README


def main() -> None:
    arms: dict[str, list[tuple[float, float]]] = {}
    for f in sorted(HERE.glob("*.json")):
        d = json.loads(f.read_text())
        arm = f.stem.rsplit("_s", 1)[0]
        arms.setdefault(arm, []).append((d["all"][0] - d["T displayed"][0], d["all"][1]))
    out = {}
    for arm, xs in arms.items():
        v = [x for x, _ in xs]
        se = st.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else math.nan
        out[arm] = {"excess_K": st.fmean(v), "seed_se_K": se, "mean_jackknife_K": st.fmean(e for _, e in xs),
                    "runs": v, "expected_K": EXPECTED.get(arm)}  # fmt: skip
        print(f"{arm:13s} {st.fmean(v):+6.2f} K  (seeds SE {se:.2f}, jackknife {out[arm]['mean_jackknife_K']:.2f}; "
              f"n = {len(v)}; expected {EXPECTED.get(arm, '-')})  runs " + " ".join(f"{x:+.1f}" for x in v))  # fmt: skip
    (HERE / "summary.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
