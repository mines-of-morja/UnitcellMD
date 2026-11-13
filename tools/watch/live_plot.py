"""Live plot of a ucmd thermo table while the run is going (a stopgap until the B2a GUI).

    python tools/watch/live_plot.py RUN/out/thermo.tsv                # window, updates every second
    python tools/watch/live_plot.py RUN/out/thermo.tsv --png plot.png  # one snapshot, no window

Needs NumPy and matplotlib, e.g. ucmd-builder/.venv/bin/python. It reads the thermo columns by
the names of spec/run-config.md, so it works for any run, and ignores a line that is still
being written.
"""

import argparse
from pathlib import Path

import numpy as np

PANELS = [
    ("temperature (K)", ["temperature_K"]),
    ("energy (kJ/mol)", ["potential_kjmol", "total_kjmol", "conserved_energy_kjmol"]),
    ("kinetic energy (kJ/mol)", ["kinetic_kjmol"]),
    ("pressure (bar)", ["pressure_bar"]),
    ("energy terms (kJ/mol)", "term:"),  # every term:<name>_kjmol column
]


def read(path: Path) -> tuple[list[str], np.ndarray]:
    """Column names and the complete rows written so far."""
    lines = path.read_text().splitlines() if path.exists() else []
    if not lines:
        return [], np.empty((0, 0))
    names = lines[0].lstrip("# ").split("\t")
    rows = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != len(names):
            continue  # still being written
        try:
            rows.append([float(x) for x in parts])
        except ValueError:
            continue
    return names, np.array(rows).reshape(-1, len(names))


def columns(names: list[str], wanted) -> list[str]:
    if isinstance(wanted, str):
        return [n for n in names if n.startswith(wanted)]
    return [n for n in wanted if n in names]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("thermo", type=Path, help="thermo.tsv of a run")
    ap.add_argument(
        "--png", type=Path, help="write one snapshot instead of opening a window"
    )
    ap.add_argument(
        "--every", type=float, default=1.0, help="refresh interval in seconds"
    )
    args = ap.parse_args()

    import matplotlib

    if args.png:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    fig, axes = plt.subplots(len(PANELS), 1, sharex=True, figsize=(9, 11))
    fig.canvas.manager.set_window_title(f"ucmd: {args.thermo}")
    lines: dict[str, object] = {}

    def update(_frame=None):
        names, data = read(args.thermo)
        if data.shape[0] == 0:
            fig.suptitle(f"{args.thermo}: waiting for data …")
            return
        t = data[:, names.index("time_ps")]
        for ax, (label, wanted) in zip(axes, PANELS):
            for name in columns(names, wanted):
                y = data[:, names.index(name)]
                if name not in lines:
                    short = name.removeprefix("term:").removesuffix("_kjmol")
                    (lines[name],) = ax.plot(t, y, lw=1, label=short)
                    ax.set_ylabel(label)
                    ax.legend(loc="upper right", fontsize="small", ncols=4)
                else:
                    lines[name].set_data(t, y)
            ax.relim()
            ax.autoscale_view()
        last = data[-1]
        status = f"step {int(last[names.index('step')])}, t = {t[-1]:.3f} ps"
        if "temperature_K" in names:
            status += f", T = {last[names.index('temperature_K')]:.1f} K"
        fig.suptitle(f"{args.thermo.resolve().parent.parent.name}: {status}")

    axes[-1].set_xlabel("time (ps)")
    update()
    fig.tight_layout()
    if args.png:
        fig.savefig(args.png, dpi=90)
        return
    _animation = FuncAnimation(
        fig, update, interval=1000 * args.every, cache_frame_data=False
    )
    plt.show()


if __name__ == "__main__":
    main()
