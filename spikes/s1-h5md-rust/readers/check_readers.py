"""Spike S1: read the Rust-written H5MD file with h5py and MDAnalysis and check every convention.

usage: python check_readers.py <traj.h5>
"""

import json
import sys
import time

import h5py
import MDAnalysis as mda
import numpy as np

path = sys.argv[1]
result: dict[str, object] = {}

with h5py.File(path, "r") as f:
    value = f["particles/all/position/value"]
    n_frames, n_atoms, _ = value.shape
    i = np.arange(n_atoms)
    for k in (0, 1, n_frames - 1):
        expected = np.stack(
            [(i % 100) * 0.05 + 1e-3 * k, ((i // 100) % 100) * 0.05, (i // 10000) * 0.05 + 2e-3 * k], axis=1
        )
        assert np.array_equal(value[k], expected), f"frame {k} differs"
    result["h5py_exact_values"] = True
    result["h5md_version"] = f["h5md"].attrs["version"].tolist()
    result["unit_position"] = f["particles/all/position/value"].attrs["unit"]
    result["chunks"] = value.chunks
    result["system_json_atom_count"] = json.loads(f["parameters/ucmd/system_json"][()])["atom_count"]
    edges = f["particles/all/box/edges/value"][0]

u = mda.Universe.empty(n_atoms, trajectory=False)
t0 = time.perf_counter()
u.load_new(path, format="H5MD")
result["mdanalysis_frames"] = len(u.trajectory)
ts = u.trajectory[n_frames - 1]
# MDAnalysis works in Angstrom: nm * 10
assert np.allclose(ts.positions[:5], value_last := np.stack(
    [(np.arange(5) % 100) * 0.05 + 1e-3 * (n_frames - 1), np.zeros(5), np.full(5, 2e-3 * (n_frames - 1))], axis=1
) * 10.0, atol=1e-4), "MDAnalysis positions differ"
result["mdanalysis_positions_angstrom_ok"] = True
result["mdanalysis_time_ps"] = float(ts.time)
result["mdanalysis_dimensions"] = [round(float(x), 6) for x in ts.dimensions]
# edges rows are a, b, c in nm; expected lengths/angles for a=(5,0,0), b=(1.25,5,0), c=(0,0,5)
a, b, c = edges * 10.0
expected = [np.linalg.norm(a), np.linalg.norm(b), np.linalg.norm(c),
            np.degrees(np.arccos(np.dot(b, c) / (np.linalg.norm(b) * np.linalg.norm(c)))),
            np.degrees(np.arccos(np.dot(a, c) / (np.linalg.norm(a) * np.linalg.norm(c)))),
            np.degrees(np.arccos(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))))]
result["box_rows_interpreted_as_lattice_vectors"] = bool(np.allclose(ts.dimensions, expected, atol=1e-3))
t1 = time.perf_counter()
for _ in u.trajectory:
    pass
result["mdanalysis_full_pass_s"] = round(time.perf_counter() - t1, 2)
print(json.dumps(result, indent=1))
