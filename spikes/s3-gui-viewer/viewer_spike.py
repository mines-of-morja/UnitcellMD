"""Spike S3: PySide6 + pyvistaqt viewer for 10k-50k atoms (PLAN.md B2.2, ADR 0006). Throwaway.

usage: python viewer_spike.py <n_atoms> <mode: impostor|glyph> <out_dir>

Builds the four-area layout of PLAN.md B2.1 (components | 3D | properties / validation), shows
n_atoms on a jittered grid with ~1 bond per atom and a triclinic cell, rotates the camera for a
fixed number of frames and reports build time and frames per second, then saves screenshots.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6 import QtCore, QtWidgets

ELEMENT_COLORS = {"C": "#909090", "O": "#ff0d0d", "H": "#ffffff", "Li": "#cc80ff", "P": "#ff8000", "F": "#90e050"}


def synthetic_system(n_atoms: int, seed: int = 7) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    rng = np.random.default_rng(seed)
    side = int(np.ceil(n_atoms ** (1 / 3)))
    grid = np.array([[i, j, k] for i in range(side) for j in range(side) for k in range(side)][:n_atoms], float)
    spacing = 0.3  # nm
    cell = np.array([[side * spacing, 0, 0], [0.25 * side * spacing, side * spacing, 0], [0, 0, side * spacing]])
    positions = (grid / side) @ cell + rng.normal(0, 0.02, (n_atoms, 3))
    elements = list(rng.choice(list(ELEMENT_COLORS), size=n_atoms))
    bonds = np.array([[i, i + 1] for i in range(0, n_atoms - 1) if (i + 1) % side != 0])
    return positions, bonds, elements, cell


def cell_lines(cell: np.ndarray) -> pv.PolyData:
    a, b, c = cell
    corners = np.array([o + x for o in (np.zeros(3), c) for x in (np.zeros(3), a, a + b, b)])
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    lines = np.hstack([[2, i, j] for i, j in edges])
    return pv.PolyData(corners, lines=lines)


class Window(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ucmd-builder viewer spike (S3)")
        self.resize(1400, 900)
        self.plotter = QtInteractor(self)
        self.setCentralWidget(self.plotter.interactor)
        for title, area in (
            ("Components", QtCore.Qt.LeftDockWidgetArea),
            ("Properties", QtCore.Qt.RightDockWidgetArea),
            ("Validation", QtCore.Qt.BottomDockWidgetArea),
        ):
            dock = QtWidgets.QDockWidget(title, self)
            dock.setWidget(QtWidgets.QLabel(f"{title} panel (placeholder)"))
            self.addDockWidget(area, dock)


def main() -> None:
    n_atoms, mode, out = int(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    app.processEvents()
    plotter = window.plotter

    t0 = time.perf_counter()
    positions, bonds, elements, cell = synthetic_system(n_atoms)
    colors = np.array([pv.Color(ELEMENT_COLORS[e]).int_rgb for e in elements], dtype=np.uint8)
    cloud = pv.PolyData(positions)
    cloud["rgb"] = colors
    if mode == "impostor":
        plotter.add_mesh(cloud, scalars="rgb", rgb=True, render_points_as_spheres=True, point_size=8)
    else:
        spheres = cloud.glyph(geom=pv.Sphere(radius=0.06, theta_resolution=10, phi_resolution=10), scale=False, orient=False)
        plotter.add_mesh(spheres, scalars="rgb", rgb=True, smooth_shading=True)
    lines = np.hstack([np.full((len(bonds), 1), 2), bonds]).ravel()
    plotter.add_mesh(pv.PolyData(positions, lines=lines), color="#606060", line_width=2)
    plotter.add_mesh(cell_lines(cell), color="#2060ff", line_width=3)
    plotter.reset_camera()
    plotter.render()
    app.processEvents()
    build_s = time.perf_counter() - t0

    # picking check: the properties panel would show the picked atom
    picked = {}
    plotter.enable_point_picking(callback=lambda point, *_: picked.update(point=list(point)), show_message=False)

    n_frames = 120
    t1 = time.perf_counter()
    for _ in range(n_frames):
        plotter.camera.azimuth = plotter.camera.azimuth + 3
        plotter.render()
        app.processEvents()
    fps = n_frames / (time.perf_counter() - t1)

    plotter.screenshot(str(out / f"vtk-{mode}-{n_atoms}.png"))
    window.grab().save(str(out / f"qt-{mode}-{n_atoms}.png"))
    result = {
        "atoms": n_atoms,
        "bonds": int(len(bonds)),
        "mode": mode,
        "build_s": round(build_s, 3),
        "fps": round(fps, 1),
        "qt_platform": app.platformName(),
        "opengl_renderer": plotter.ren_win.ReportCapabilities().split("OpenGL renderer string:")[1].split("\n")[0].strip()
        if "OpenGL renderer string:" in plotter.ren_win.ReportCapabilities()
        else "unknown",
    }
    print(json.dumps(result))
    plotter.close()
    window.close()
    app.quit()


if __name__ == "__main__":
    main()
