"""Digitize Figure S1 of Landesfeind & Gasteiger 2019 (SI) for EC:EMC 3:7 and compare with Eq. S1.

Usage: digitize_fig_s1.py word/media/image1.png   (from the unzipped SI docx; not in this repo)

The figure is a parallel projection, so pixel = origin + c*e_c + T*e_T + rho*e_rho. The axis ticks
below were read by hand from the 875 x 656 px image (+-0.5 px); the markers are found by colour.
Needs numpy and Pillow (ucmd-analysis venv).
"""

import sys
from collections import deque

import numpy as np
from PIL import Image

# hand-read ticks (px): T = 0, 20, 40 C and the front corner; c = 0, 1, 3 M; rho = 1.0, 1.2, 1.4
T_TICKS = {0.0: (710.5, 520.5), 20.0: (758.75, 450.75), 40.0: (807.5, 380.75)}
C_TICKS = {0.0: (147.0, 503.25), 1.0: (320.0, 521.25), 3.0: (666.25, 557.0)}
RHO_TICKS = {1.0: 475.0, 1.2: 374.25, 1.4: 273.5}
CORNER_LEFT, CORNER_RIGHT = (131.75, 501.25), (685.0, 559.5)  # front edge of the floor
P = (1.41, 0.0912, -0.00109)  # Table S1, EC:EMC 3:7


def blobs(mask, smallest):
    mask, found = mask.copy(), []
    for y, x in zip(*np.nonzero(mask), strict=True):
        if not mask[y, x]:
            continue
        queue, pts = deque([(y, x)]), []
        mask[y, x] = False
        while queue:
            a, b = queue.popleft()
            pts.append((b, a))
            for u in range(max(a - 1, 0), min(a + 2, mask.shape[0])):
                for v in range(max(b - 1, 0), min(b + 2, mask.shape[1])):
                    if mask[u, v]:
                        mask[u, v] = False
                        queue.append((u, v))
        pts = np.array(pts)
        if len(pts) >= smallest:
            found.append((pts.min(0) + pts.max(0)) / 2)
    return found


def slope(ticks):
    keys = sorted(ticks)
    return (np.array(ticks[keys[-1]]) - np.array(ticks[keys[0]])) / (keys[-1] - keys[0])


rgb = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
blue = (rgb[..., 2] > 150) & (rgb[..., 0] < 60) & (rgb[..., 1] < 120)
marks = [m for m in blobs(blue, 80) if not 247 < m[0] < 311 or m[1] > 100]  # drop the legend box

e_c, e_t = slope(C_TICKS), slope(T_TICKS)
e_rho = (RHO_TICKS[1.4] - RHO_TICKS[1.0]) / 0.4  # px per g/cm3, vertical
t_front = (CORNER_RIGHT[0] - T_TICKS[0.0][0]) / e_t[0]  # T of the front edge
t_front_y = (CORNER_RIGHT[1] - T_TICKS[0.0][1]) / e_t[1]
c_left = (CORNER_LEFT[0] - C_TICKS[0.0][0]) / e_c[0]
print(f"front edge T = {t_front:.1f} (x) / {t_front_y:.1f} (y) C; left edge c = {c_left:.3f} M")
t0 = 0.5 * (t_front + t_front_y)

rows = []
for x, y in sorted(map(tuple, marks)):
    # c from the nearest value of the plotted series, then T follows from x
    u = (x - C_TICKS[0.0][0]) / e_c[0] + t0 * e_t[0] / e_c[0]
    best = min(
        ((c, t) for c in (0.0, 1.0, 2.0, 3.0) for t in (10, 20, 30, 40, 50)),
        key=lambda ct: abs(ct[0] + ct[1] * e_t[0] / e_c[0] - u),
    )
    c, t = best
    off = (u - c - t * e_t[0] / e_c[0]) * e_c[0]
    rho = 1 + (RHO_TICKS[1.0] + e_c[1] * (c - c_left) + e_t[1] * (t - t0) - y) / -e_rho
    fit = P[0] + P[1] * c + P[2] * (t + 273.15)
    rows.append((c, t, rho, fit, off))
rows.sort()
print(" c/M  T/C   rho(fig)  Eq. S1   diff     x residual (px)")
for c, t, rho, fit, off in rows:
    print(f"{c:4.1f} {t:4d}  {rho:8.4f} {fit:8.4f} {rho - fit:+8.4f} {off:+6.1f}")
a = np.array(rows)
diff = a[:, 2] - a[:, 3]
print(f"{len(a)} points, mean diff {diff.mean():+.4f}, scatter {diff.std(ddof=1):.4f} g/cm3")
X = np.c_[np.ones(len(a)), a[:, 0], a[:, 1] + 273.15]
coef, *_ = np.linalg.lstsq(X, a[:, 2], rcond=None)
res = a[:, 2] - X @ coef
s2 = res @ res / (len(a) - 3)
cov = s2 * np.linalg.inv(X.T @ X)
r2 = 1 - res @ res / ((a[:, 2] - a[:, 2].mean()) ** 2).sum()
print("refit of the figure:", np.round(coef, 5), "SE", np.round(np.sqrt(np.diag(cov)), 5))
print(f"R2 {r2:.4f} (printed 0.997), residual SD {np.sqrt(s2):.4f}")
for name, t in (("20 C", 293.15), ("25 C", 298.15)):
    v = np.array([1.0, 1.0, t])
    print(f"1 M {name}: Eq. S1 {P[0] + P[1] + P[2] * t:.4f}, figure {v @ coef:.4f}"
          f" +- {np.sqrt(v @ cov @ v):.4f} (fit)")  # fmt: skip
r = (0.005, 0.00005, 0.000005)
print(f"rounding of Table S1 at 1 M, 20 C: +-{r[0] + r[1] + r[2] * 293.15:.4f} (worst case)")
