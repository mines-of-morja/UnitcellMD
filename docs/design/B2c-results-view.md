# B2c design — looking at results in the GUI: molecules, optimizations, studies

- **Status:** draft 2026-11-25, at the author's request ("where can I visualize the computations …
  if not we should add the ability"). **Not approved, nothing in the GUI is built.** Outside the
  PLAN.md order (it extends B2.2 and B2.6; B2b stays as it is).
- **Built with this draft:** only `tools/qm/cluster_xyz.py` (DFT result → extended XYZ).

## 1. What works today, checked 2026-11-25

| Result | GUI today |
|---|---|
| Finished MD run | yes: Open run; 3D playback, T, energies, conservation, pressure, volume (scan run base_s1: 2501 frames, 2.8 s) |
| Folder of runs or study | yes: Open run on the folder lists the runs |
| Running GPU run | thermo plots; frames only after the end (H5MD is not read while written) |
| DFT cluster, one geometry | **no**: no package, no bonds, no way to open a molecule file |
| DFT optimization path | **no** |
| Trends across a study (`analyze.py`) | **no**: numbers in a JSON, no plots anywhere |
| Queue and progress | `tools/queue` dashboard (http://127.0.0.1:8765), not the GUI |

**Two defects found on the way:**
1. The summary shows ⟨P⟩ = `nan ± nan` for GPU runs. The bridge computes the pressure only on every
   5th thermo row (10 001 of 50 001) and writes `nan` in the others; `thermo.summary` averages all of
   them. Fix: average the rows that have a value, and show how many.
2. The box drawn during playback is the package's. NPT runs change it (`box/edges` in the H5MD is
   time-dependent). Fix: move the cell with the frame, also when wrapping molecules.

## 2. Boundaries

- **The GUI shows, it does not interpret** (the one rule). It draws files; it computes no property
  that enters a result. Distances and angles between picked atoms are a ruler, not a result.
- **Format in:** extended XYZ, which the builder already writes and the engine already streams.
  Psi4 output never enters the GUI: `tools/qm/cluster_xyz.py` converts it outside the components
  (invariant 2).
- **Blinding:** the XYZ of a blinded trial holds coordinates only. The GUI shows energies only from
  files that hold them, so it cannot unblind T6.
- **Bonds of a molecule file are drawn from distances** (display only, labelled "guessed bonds");
  the engine's rule that nothing is guessed is untouched: no such file can be run or exported.

## 3. Steps (each one a branch commit with tests)

1. **Open molecule file** (File → Open molecule…): extended or plain XYZ, one or many frames, no
   cell needed. Frames of different molecules are a list (n = 0 … 4), frames of one molecule a
   path: the slider and Play of the run panel move through it. New `gui/molecule_file.py` and a
   `Scene.from_xyz`; the viewer does not change.
2. **Ruler:** pick two atoms for a distance, three for an angle; a table lists the eight nearest O
   of a picked Li⁺, sorted, with their molecule. No cutoff is involved.
3. **The two defects of §1.**
4. **Compare:** up to five molecule files side by side with linked cameras (for n = 0 … 4).
5. **Study trends:** the GUI plots columns of a table written by the analysis (study folder,
   `views/trends.tsv`, written by `analyze.py`). It computes no fit. Needs question 2.

## 4. Acceptance tests (headless, no display)

- A 61-atom XYZ opens; element, molecule and bond counts match the cluster (4 solvents, Li⁺ unbonded).
- A 172-frame path plays; frame k shows the coordinates of frame k.
- A file with a missing atom line, or a non-numeric coordinate, is refused with a message.
- The ruler's distance equals the one from the coordinates to 1e-6 nm.
- ⟨P⟩ of a thermo file with 80 % `nan` rows equals the mean of the rest.
- In a synthetic NPT trajectory the drawn cell follows `box/edges`.
- Screenshots of steps 1 and 4 in `validation/b2c/`, looked at by the author.

## 5. Questions for the author

1. **Where?** Proposal: the builder GUI (it already shows runs). Alternative: a separate results
   window, so the builder keeps only the initial system. Cost: a second program.
2. **Study trends:** may `analyze.py` write a small table for the GUI (no spec change), or should a
   result-table format go into `spec/` first? Proposal: no spec change until a second study needs it.
3. **Optimization curves** (max force per step): show them? They hold no energies, but reading them
   needs the Psi4 output parsed further. Proposal: later.
4. **Order:** 1, 2, 3 first (enough for the T6 clusters), then 4 and 5.
