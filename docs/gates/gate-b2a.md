# Gate report — B2a, the GUI preview

- **Date:** 2026-11-13.
- **Where:** branch `b2a` of ucmd-builder (started from `b1`), of ucmd-engine (the graceful
  stop) and of this repo (this report, testing.md §9).
- **Design:** [design/B2a.md](../design/B2a.md), approved 2026-11-13 with every §11
  recommendation.
- **Gate criterion (PLAN.md):** the author builds a small LiPF₆/EC:EMC box in the GUI, runs it
  for a few picoseconds, and watches temperature, energy and the trajectory without touching a
  file. The steps are in [testing.md](../testing.md) §9.

## 1. Summary

- **`ucmd-build gui [RECIPE]` opens one window:**
  - components on the left, the 3D view in the centre, properties and the run on the right,
    the log below;
  - every action edits the recipe through the recipe parser, with undo and redo.
- **Building:**
  - library molecules, a composition dialog with a live preview of the counts;
  - the build runs in the background with progress and Cancel;
  - export writes a validated package plus its recipe; packages open read-only.
- **3D view:**
  - instanced spheres, so 7000 atoms play at about 60 frames per second;
  - Jmol colours, bonds and the cell; molecules drawn whole in the cell;
  - right-click shows an atom's type, charge, σ and ε; a selected component lights up;
  - periodic images as a toggle.
- **Run preview:**
  - `ucmd minimize` and `ucmd run` as external programs;
  - live plots of T and the energies; the trajectory plays afterwards;
  - Stop is graceful: the engine writes a checkpoint and closes its files.
- **Checked with the real engine** (driven headless through the GUI code), on 1402 atoms:
  build 3.8 s, minimization 2.8 s, 2 ps in 18.5 s, final T 301 K. Stop ends a run with a
  checkpoint and playable frames.
- **State:**
  - ucmd-builder: 110 tests pass; one window test needs a display and runs under Xvfb in CI;
  - ucmd-engine: 91 tests;
  - CI green on both `b2a` branches, including a new GUI job under Xvfb.

## 2. Acceptance tests (design §9)

| Item | Test | Evidence |
|---|---|---|
| B2.1 | open a recipe, change a count, undo, redo, save; the reopened recipe is the expected one | `test_open_edit_undo_redo_save` |
| B2.1 | an invalid edit (a negative count) is refused and logged; the recipe is unchanged | `test_an_invalid_edit_is_refused`, `test_the_table_edits_counts_and_refuses_bad_values` |
| B2.2 | the scene renders off screen (not blank, cell drawn, Jmol red oxygens); picking finds the atom | `test_scene_renders_moves_and_picks`; the real window under Xvfb: `test_the_main_window_with_the_real_viewer` |
| B2.2 | picking fills the properties; a component lights up; periodic images follow playback | `test_picking_and_selection_fill_the_properties`, `test_scene_renders_moves_and_picks` |
| B2.3 | the composition dialog gives Lehnert's Table S1 counts (47 Li, 47 PF6, 168 EC, 332 EMC), also from weights 3 : 7 | `test_composition_dialog_reproduces_lehnert_table_s1` |
| B2.3 | the build reports progress; Cancel stops it and leaves no system | `test_build_export_and_reopen`, `test_cancel_stops_a_build` |
| B2.5 | export writes a package the validator accepts, and the recipe next to it; reopening shows the same atoms | `test_build_export_and_reopen` |
| B2.6 | with a fake engine: start, live plots, playback, Stop (status 143), and the error display for a non-zero exit | `tests/gui/test_run_preview.py` (5 tests) |
| B2.6 | the generated `run.toml` passes the spec validator; the run directory is outside the package | `test_generated_run_files_pass_the_spec_validator`; the GUI also checks every `run.toml` before it starts the engine |
| Gate | the author's hands-on session | testing.md §9, **open** |

- **Screenshots:** `validation/b2a/screenshots.py` takes five states (empty, composition, built,
  run dialog, finished run) without a display. The agent checked them as images. They led to two
  layout fixes: the live charts moved into the right column, and the playback slider got its
  own width. The images are not committed.

## 3. Found and fixed

1. **The locale silently corrupted coordinates.**
   - Qt sets the process locale from the system. With German number formats, C's `strtod` reads
     "0.896716" as 0, and RDKit's XYZ reader returned zeros without an error.
   - The full test run caught it, because the molecule tests ran after the GUI tests in the same
     process.
   - Fix: the GUI resets `LC_NUMERIC` to C. A regression test forces a comma locale, and it fails
     without the fix.
2. **A window test that passed on noise.** Under Qt's offscreen platform the OpenGL widget
   returns GPU noise, which met the old "many coloured pixels" check. The test now also
   requires a mostly white background, and it runs where a display exists: in CI under Xvfb.
3. **Test-suite hangs and teardown errors:**
   - a confirmation dialog at teardown blocked the suite; questions now go through
     `MainWindow.ask`;
   - the undo stack emits a signal while being destroyed; the title update now ignores it.

## 4. Deviations from the design

- **h5py is in the `gui` extra directly,** rather than through `ucmd-spec[trajectory]`. It is the
  same package.
- **pytest-qt is in a separate extra, `gui-test`.** pytest-qt aborts every test run on a machine
  without Qt, so it cannot be in `dev`.
- **The Viewer protocol takes a `Scene`** (elements, positions, bonds, cell, molecules) rather
  than separate arrays, and gained `show_images()`.
- **The composition dialog supports the mass basis only.** Volume fractions need pure-solvent
  densities with their source; that is B2b.
- **One library data set per recipe** in the add dialog. Mixing sets needs compatible
  conventions; that is B2b.
- **Engine (approved with the design):**
  - the graceful stop: status 130/143, a checkpoint, closed outputs;
  - every restart is recorded in the H5MD provenance, not only forced ones.

## 5. Questions for the author

1. **Gate B2a:** please run [testing.md](../testing.md) §9 and tell me what to change in the
   look and the workflow. That feedback is the point of B2a.
2. **Merging:** `b2a` of ucmd-builder contains `b1`, which still waits for Gate B1a. Decide both
   gates together, then merge `b1` and `b2a`?
3. **Spec v0.1.1 (a spec change, so your call):** document the graceful-stop exit codes and the
   `/parameters/ucmd/restarts` record, both now engine behaviour. Together with the validator
   packaging fix (gate-b1a.md §4.1)?
4. **Live frames during a run:** they need either an append-only trajectory format in the spec or
   HDF5's single-writer/multiple-reader mode. Later, after the barostat and the GPU backend?
