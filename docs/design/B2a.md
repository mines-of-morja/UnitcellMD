# B2a design — GUI preview: build, view, short local runs

- **Status:** approved by the author on 2026-11-13 ("take the recommendations"): every §11
  recommendation is taken. Implementation on branch `b2a` of ucmd-builder, started from `b1`
  (Gate B1a is still open), and on branch `b2a` of ucmd-engine for the graceful stop.
- **Scope:** PLAN.md §6, B2a = B2.1 app shell, B2.2 3D view, the liquid part of B2.3 with
  library molecules, the export part of B2.5, and B2.6 run preview.
  - Everything else is B2b: SMILES and file input, crystals, validator highlighting, editing
    packages.
- **Gate B2a (PLAN.md):** the author builds a small LiPF₆/EC:EMC box in the GUI, runs it for a
  few picoseconds, and watches temperature, energy and the trajectory, without touching files.
- **Spec:** v0.1.0, no change needed. The GUI reads and writes only spec'd files: recipe,
  system package, `run.toml`, thermo table, H5MD trajectory.
- **Stack:** PySide6 + pyvistaqt (ADR 0006, spike S3).

## 1. Boundaries

- **The GUI is a thin layer over the builder library (B1).**
  - Every GUI action is an edit of the `Recipe`, or a call of an existing library function:
    `compose`, `build`, `write_package`, `to_toml`.
  - It adds no physics and no parameters.
- **The builder library never imports the GUI, and never runs MD.**
- **The run preview starts the engine as an external program.**
  - `ucmd` is started by absolute path from the machine profile (`[executables] ucmd`), as
    every external program (CLAUDE.md, spec run-config.md §4).
  - The GUI reads only the engine's spec'd outputs (invariant 2). It never reads checkpoints:
    their format is private to the engine (checkpoint.md).
- **`tests/test_architecture.py` is extended:**
  - `ucmd_builder.gui` is imported only by itself and by the `gui` CLI subcommand;
  - no library module imports PySide6, pyvista or the GUI.

## 2. Packaging

- **The extra `ucmd-builder[gui]`** (ADR 0006, decision 2):
  - PySide6 ≥ 6.12, pyvista ≥ 0.49, pyvistaqt ≥ 0.13 (VTK comes with pyvista);
  - `ucmd-spec[trajectory]` for h5py, which reads the H5MD trajectory. Its wheels bundle
    HDF5, so no system package is needed.
  - The headless builder installs without any of these.
- **Plots** use QtCharts, which is part of PySide6. No plotting library is added.
- **Tests** add `pytest-qt` to `dev`.
- **Start:** `ucmd-build gui [RECIPE]`. Without the extra, it prints how to install it.

## 3. App shell (B2.1)

```
┌ toolbar: New  Open  Save  │  Build  Cancel  │  Export  │  Run preview ───────────┐
├──────────────┬──────────────────────────────────────────────┬────────────────────┤
│ Components   │                                              │ Properties         │
│  name  mol.  │                 3D view                      │  component: formula│
│  count  ζ    │                                              │  charge, types     │
│ [+] [−]      │                                              │  atom: element,    │
│ Composition… │                                              │  type, q, σ, ε     │
├──────────────┴──────────────────────────────────────────────┴────────────────────┤
│ Log: build progress · validator messages · engine output        │ T(t) │ E(t)     │
└───────────────────────────────────────────────────────────────────────────────────┘
```

- **`RecipeDocument` (QObject)** is the single source of truth.
  - It holds the current `Recipe`, its path and a modified flag, and emits `changed`.
  - `Recipe` and its parts are frozen dataclasses. An edit builds a new recipe with
    `dataclasses.replace` and pushes one `ReplaceRecipe(old, new, text)` command onto a
    `QUndoStack`. Undo and redo just swap recipes.
  - An edit that the recipe parser would reject (`RecipeError`) is not applied; the message
    goes to the log.
- **Files:**
  - Save writes `to_toml(recipe)`; Open uses `load_recipe`.
  - The test is a round trip: open → edit → save → reopen gives the same recipe.
- **Docks:** left, components (a `QTableView` over the components); right, properties of
  the selection; bottom, the log and the live plots. The centre holds the 3D view.

## 4. 3D view (B2.2)

- **A `Viewer` protocol** (ADR 0006, decision 4):
  - `show_system(elements, positions_nm, bonds, cell)`;
  - `update_positions(positions_nm)`, for playback;
  - `highlight(atoms)`;
  - `on_pick(callback)`;
  - `screenshot(path)`.

  `PyVistaViewer` implements it with a `QtInteractor`. Another viewer, for example a web or
  Rust one, can implement the same protocol later.
- **Scene:**
  - element colours from Jmol's CPK table (as in spike S3), with the source cited in
    `gui/elements.py`;
  - radii: RDKit's van der Waals radii × 0.3;
  - bonds as lines from the package bonds; the cell as a wireframe; periodic images as a
    toggle (3×3×3, faded);
  - geometric glyphs up to 20 000 atoms, impostor spheres above (ADR 0006, decision 3).
- **Display only:** molecules are made whole and shown with their centre in the cell. The
  package keeps its unwrapped positions.
- **Picking:** a picked atom fills the properties panel with element, atom type, charge, σ, ε
  and molecule.

## 5. Liquid workflow with library molecules (B2.3, liquid part)

- **Add component:** pick a force-field set, then a molecule from `ucmd-build library` (for
  example EC, EMC, Li, PF6 of `opls-aa-carbonates`).
  - Fields: component name, and charge scale ζ for ions (default 1.0).
  - The recipe stores `molecule = { library = "…" }`.
- **Composition dialog:** the fields of `[composition]`:
  - salt cation and anion, chosen from the components;
  - solvents with fractions, on a mass or mole basis;
  - molarity and number of solvent molecules;
  - density, with value and source, or a fixed box length.
  - A live preview calls `compose()`: counts, box length and achieved concentration, as
    `ucmd-build compose` prints them. A placeholder density is shown as a warning.
- **Build:**
  - `build(recipe, progress=…, cancel=…)` runs in a `QThread` worker. Progress lines go to
    the log; Cancel sets the flag that `build` already polls.
  - The packing method comes from the recipe: Packmol from the venv or the machine profile,
    or insertion.
  - The result appears in the 3D view.

## 6. Export and open (B2.5, export part)

- **Export:**
  - writes the package with `write_package`, which is validated by `ucmd-spec` before it is
    moved into place;
  - writes the recipe next to it as `<name>.recipe.toml`.
- **Open package (read-only):**
  - reads `system.json` and `positions.npy` through `ucmd_spec`;
  - shows the system, and fills the properties from the force-field block.

## 7. Run preview (B2.6)

- **Dialog,** with the defaults of the M2a protocol:
  - temperature (298.15 K);
  - length (2 ps) and time step (1 fs);
  - thermostat: `nose-hoover-chain` with τ = 0.1 ps, or `csvr`;
  - "minimize first" (on);
  - frame interval (every 100 steps).

  It shows the generated `run.toml` read-only, and the thread count from the machine profile.
- **Run directory:** `<package>.runs/<YYYYmmdd-HHMMSS>/`:
  - `run.toml` with a relative `system` path, so the directory can be moved;
  - `minimized.ucsys/`, if minimization was chosen;
  - `out/` with the thermo table, the H5MD trajectory and the checkpoint.

  The run directory never lives inside the package (packages stay immutable).
- **Process:**
  - `QProcess` runs `ucmd minimize`, then `ucmd run`. Engine stderr goes to the log, and the
    exit status is shown.
  - Without `[executables] ucmd` in the machine profile, the dialog says so. A "Locate ucmd…"
    button writes the entry after the author confirms.
- **Live display:** a timer every 0.5 s reads new lines of `thermo.tsv` by the column names of
  spec/run-config.md. QtCharts plots T(t) with the target line, and E_pot(t), E_total(t) and
  the conserved energy.
- **Trajectory:** playback after the run ends.
  - Frames come from `/particles/all/position` of the H5MD file, read with h5py.
  - A slider and a play button drive `viewer.update_positions`.
  - Live frames are not offered in B2a, because HDF5 files cannot be read safely while another
    process writes them (question 3).
- **Cancel:** `QProcess.terminate()`. The thermo table stays readable. The H5MD file may then be
  incomplete; question 4 proposes a graceful stop in the engine.

## 8. Files

- **ucmd-builder**, all new unless noted:
  - `src/ucmd_builder/gui/`:
    - `__init__.py`, `app.py` (QMainWindow, actions);
    - `document.py` (RecipeDocument, ReplaceRecipe);
    - `components.py`, `properties.py`, `log.py` (docks);
    - `viewer.py` (protocol + PyVista implementation), `elements.py` (colours, radii);
    - `composition.py` (dialog), `build_worker.py`, `export.py`;
    - `run_preview.py` (dialog, QProcess, run directory), `thermo.py` (incremental TSV reader),
      `plots.py` (QtCharts), `trajectory.py` (H5MD frames).
  - Changed: `src/ucmd_builder/cli.py` (the `gui` subcommand), `pyproject.toml` (extras),
    `tests/test_architecture.py`.
  - Tests: `tests/gui/`, and `tests/gui/fake_ucmd.py` (a fake engine).
  - CI: `.github/workflows/ci.yml` gets a GUI job under `xvfb-run`, with VTK offscreen.
- **Umbrella:** this design, `docs/testing.md` §8 (GUI hands-on), and the Gate B2a report.
- **Engine:** only if question 4 is accepted: a graceful stop on SIGINT/SIGTERM.

## 9. Acceptance tests

| Item | Test |
|---|---|
| B2.1 | pytest-qt: open a recipe, change a count, undo, redo, save; the reopened recipe equals the expected one |
| B2.1 | an invalid edit (e.g. a negative count) is refused and logged; the recipe is unchanged |
| B2.2 | offscreen screenshot of a built box is not blank and shows the cell; picking an atom fills the properties |
| B2.3 | composition dialog for 1 M LiPF₆ in EC:EMC 3:7 gives Lehnert's Table S1 counts (as `ucmd-build compose`) |
| B2.3 | building a small box in the worker reports progress; cancel stops it and leaves no package |
| B2.5 | export writes a package that `ucmd-spec validate` accepts, and the recipe next to it; reopening shows the same atoms |
| B2.6 | with `fake_ucmd.py`, which writes thermo lines step by step and then a small H5MD file: start, live plot updates, playback, cancel, and the error display for a non-zero exit |
| B2.6 | the generated `run.toml` passes the spec validator; the run directory is outside the package |
| Gate | the author's hands-on session (testing.md §8): build, export, run 2 ps, watch T, E and the trajectory |

- Screenshots of the main states (empty, built box, run with plots) are made offscreen by
  `validation/b2a/screenshots.py`. The agent checks them as images before the gate, and they
  are attached to the gate report. They are not committed.

## 10. Order of work

1. Extra, architecture test, `gui` subcommand, app shell with document and undo.
2. Viewer and element table; open a package read-only.
3. Components dock, add component, composition dialog, build worker.
4. Export.
5. Run preview: dialog, run directory, QProcess, thermo plots, H5MD playback, fake-engine
   tests.
6. CI GUI job, screenshots, testing.md §8, Gate B2a report.

## 11. Questions for the author

1. **The extra `[gui]`:**
   - PySide6, pyvista, pyvistaqt, and `ucmd-spec[trajectory]` (h5py);
   - QtCharts for the plots (no plotting library);
   - pytest-qt for tests.

   OK?
2. **Preview defaults:** 298.15 K, NHC τ = 0.1 ps, 1 fs, 2 ps, FIRE first, cutoff 1.4 nm.
   - **Small boxes:** the cutoff plus the 0.2 nm skin must fit in half the box, so 1.4 nm
     needs L ≥ 3.2 nm. At 1 M that is about 210 solvent molecules; Lehnert's 500 give 4.28 nm.
     For smaller boxes I propose cutoff = min(1.4 nm, L/2 − 0.2 nm), rounded down to 0.05 nm,
     with a visible warning that this is a preview setting.
   - This is a physical parameter, so it needs your choice. The alternative is to refuse
     boxes that are too small.
3. **Trajectory:** playback after the run ends, for B2a. Live frames would need a second,
   append-only trajectory output in the engine, e.g. XYZ every n steps. That is an engine
   option for later. OK?
4. **Graceful stop:**
   - On SIGINT/SIGTERM, `ucmd run` would finish the current step, write a checkpoint, close
     the H5MD file, and exit with a distinct status.
   - Then Cancel keeps a readable trajectory, and Ctrl-C in a terminal behaves the same way.
   - A small engine task with a small pure-Rust dependency (`ctrlc` or `signal-hook`). Do it
     now, with B2a?
5. **`ucmd` path:** from `[executables] ucmd` in the machine profile; the GUI may write it
   after confirmation ("Locate ucmd…"). OK?
