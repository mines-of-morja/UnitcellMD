# 0006 — GUI viewer: PySide6 + pyvistaqt confirmed

- **Status:** accepted by the author at Gate 0 (2026-11-12). Originally accepted 2026-11-12 by the
  agent, based on spike S3 (`spikes/s3-gui-viewer/`). It confirms the author's choice of
  2026-11-11.
- **Context:**
  - PLAN.md B2 needs a 3D view inside a PySide6 window that stays interactive for 10k–50k
    atoms, supports picking, and can be screenshotted, so the agent can check GUI changes as
    images.
  - The author's workstation runs a Wayland session with AMD GPUs (Mesa).
- **Setup:** PySide6 6.12.0, pyvista 0.49.2, pyvistaqt 0.13.2, VTK 9.7.2, all from PyPI. The
  venv is **1.5 GB**.
- **Experiment:** a QMainWindow with the B2.1 layout (dock panels left, right and bottom; a
  `QtInteractor` in the centre) showing:
  - a synthetic system with element colours;
  - about one bond per atom, drawn as lines;
  - a triclinic cell.

  The camera rotates through 120 frames.
- **Results:** Qt chose native **Wayland** (no `xcb` fallback needed). The renderer was the
  AMD Radeon RX 580 through Mesa radeonsi.

  | Atoms (bonds) | Spheres | Scene build | Frame rate |
  |---|---|---|---|
  | 10 000 (9 545) | impostor (`render_points_as_spheres`) | 0.30 s | 59 fps |
  | 10 000 (9 545) | geometric glyphs | 0.42 s | 60 fps |
  | 50 000 (48 648) | impostor | 0.56 s | 59 fps |
  | 50 000 (48 648) | geometric glyphs | 1.70 s | 58 fps |

  - The frame rate is capped by vsync at 60 Hz, so the GPU has headroom.
  - Both `plotter.screenshot()` and Qt's `QWidget.grab()` capture the 3D content (not black).
    See `screenshot-10k-atoms.jpg`.
  - The point-picking API is available.
  - Harmless warnings: VTK's "Failed to get color buffer size (1282)" on Wayland, and an ibus
    inotify-limit message from the desktop session.
- **Decision:**
  1. **B2 uses PySide6 + pyvistaqt,** as the author chose.
  2. **The GUI dependencies are an optional extra, `ucmd-builder[gui]`.** The headless builder
     (B1) installs without them, which keeps cluster and CI installs small.
  3. **Spheres:** geometric glyphs up to about 20 000 atoms (nicer shading), impostor spheres
     above that (faster scene builds).
  4. **The 3D view sits behind a small `Viewer` interface** (show system, highlight atoms,
     picking callback, screenshot). A web-based viewer or a Rust front end, which the author
     may add later, can implement the same interface.
  5. **GUI tests** use pytest-qt. Visual checks use `QWidget.grab()` screenshots, which the
     agent inspects as images. CI runs headless (Xvfb or `QT_QPA_PLATFORM=offscreen` with
     VTK offscreen rendering), to be set up in B2.
- **Consequences:** none for the spec. B2 can start any time after B1.
