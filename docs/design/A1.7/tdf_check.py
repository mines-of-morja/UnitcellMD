"""Numbers of docs/design/A1.7-tdf.md §3: Eq. (1) against Gee 2011 Eq. 10, and what lumping EC and
EMC into one solvent does on a toy fluctuation matrix. Needs NumPy; no data.

    ucmd-analysis/.venv/bin/python docs/design/A1.7/tdf_check.py
"""

import numpy as np


def tdf(b: np.ndarray, c: np.ndarray) -> float:
    """Eq. (1): species 0 = all ions together, the others solvents; b = fluctuation matrix."""
    a = np.linalg.inv(b)
    u = a @ c
    w = c @ u
    return c[0] * (a[0, 0] - u[0] ** 2 / w) / (1 - c[0] * u[0] / w)


rng = np.random.default_rng(0)
worst = 0.0
for _ in range(1000):
    c = np.array([1.2, 8.0])
    g = rng.normal(0, 0.05, (2, 2))
    g = (g + g.T) / 2
    exact = 1 / (1 + c[0] * (g[0, 0] - g[0, 1]))  # Gee 2011, Eq. 10
    worst = max(worst, abs(tdf(np.diag(c) + np.outer(c, c) * g, c) / exact - 1))
print(f"one solvent, 1000 random matrices: largest relative difference to Eq. 10 {worst:.1e}")

c = np.array([2.0, 2.9, 7.6])  # ions, EC, EMC; mol/L, about 1 M in EC:EMC 3:7
v = np.array([0.028, 0.067, 0.1])
v = v / (c @ v)  # volume fractions sum to 1
lump = np.array([[1, 0, 0], [0, 1, 1]])
for a12 in (-0.2, -0.1, 0.0, 0.1, 0.2):  # ion-EC term beyond an ideal, nearly incompressible mix
    a = np.diag(1 / c) + 400 * np.outer(v, v)
    a[0, 1] += a12
    a[1, 0] += a12
    b = np.linalg.inv(a)
    assert np.linalg.eigvalsh(a).min() > 0
    print(f"A12 {a12:+.2f} L/mol: three species {tdf(b, c):.3f}, "
          f"EC + EMC lumped {tdf(lump @ b @ lump.T, lump @ c):.3f}")  # fmt: skip
