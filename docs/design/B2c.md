# B2c design — looking at results in the GUI: molecules, optimizations, studies

- **Status:** written 2026-11-25 at the author's request ("where can I visualize the computations …
  if not we should add the ability"); **steps 1–3 and the trend tables (step 5) approved the same
  day** and built on branch `b2c` of ucmd-builder (from `b2a`). Step 4 is not approved. Outside the
  PLAN.md order (it extends B2.2 and B2.6; B2b stays as it is).
  - **2026-11-28:** step 4 deferred by the agent under the author's delegation (§3).
- **The author's answers (§5):** 1. in the builder GUI. 2. `analyze.py` may write tables without a
  spec change; "add notebooks to the GUI that work like tabs, there trend tables should get a
  notebook passed". Read as a tabbed area (as `ttk.Notebook`), one page per table, not as Jupyter
  notebooks. 3. and 4. as proposed.
- **Evidence:** `validation/b2c/REPORT.md` of ucmd-builder. DFT results come in through
  `tools/qm/cluster_xyz.py`.

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

   **Decided 2026-11-28 by agent decisions under the author's delegation: deferred, not
   rejected.**
   - Reason:
     - Its use was the five T6 clusters. After the sensitivity scan, T6 became a side result,
       and its ωB97M-V energies stay off until the author decides T6.
     - Step 1 already shows the five clusters one after another (the list above *Play*), so
       they can be compared now.
     - The author has not yet run the hands-on tests of steps 1–3 and of B2d (testing.md §9a,
       §9b). Those tests should decide the next GUI work.
     - The research tasks V-1 to V-4 come first.
   - What would change it: the author asks for it after §9a, or T6 resumes with a structural
     comparison of the clusters as a deliverable. Then step 4 is built on `main` of
     ucmd-builder, in the one-window layout of B2d, with a screenshot for the author.
5. **Study trends:** the middle of the window is a notebook. Its first page is the 3D view; every
   result table gets a page (`gui/notebook.py`): the table, its notes, and points of chosen
   columns. The analysis writes the tables with `tools/study/ucmd_table.py` into `<study>/tables/`
   (git-ignored; not `views/`, which holds only links and is rebuilt, as an earlier draft said).
   The format is one file, `# ucmd-table 1` in the first line, so a thermo table is never taken
   for one. No fit is computed or drawn.

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
