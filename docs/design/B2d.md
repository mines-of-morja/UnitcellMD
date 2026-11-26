# B2d design — one window for building, looking at results and following the queue

- **Status:** draft 2026-11-25, at the author's request ("check how the GUIs integrate into each
  other and overhaul it, so all current functionalities build together into a good user
  experience"). **Approved by the author the same day** (§5): one adaptive window, a read-only queue
  page, all five steps. Built on branch `b2d` of ucmd-builder (from `b2c`, where the resizing bugs of
  §1 are fixed); not merged and not pushed before the author has tried it.
- **Built 2026-11-26** (steps 1–5): evidence in ucmd-builder `validation/b2d/REPORT.md`; hands-on in
  `docs/testing.md` §9b. Deviations: the queue address is kept in the GUI settings (§3); the log is
  folded and opens on a warning; the Queue tab stands after the tables.
- **Scope:** layout and connections of what exists. No new physics, no new analysis, no change of
  any file format.

## 1. What was checked (2026-11-25, branch `b2c` at 5009206, real and off-screen 3D widget)

| # | Finding | Measured | State |
|---|---|---|---|
| 1 | The window could not be made small | minimum 874 × 1042 px, 1202 × 1042 with a table; now 600 × 508 and 874 × 508 | fixed |
| 2 | Resizing with a run open was slow: every curve drew 50 001 points | 0.29 s per step, now 0.04 s; opening a run 3.6 s, now 1.2 s | fixed |
| 3 | A closed panel could not be brought back | no menu entry | fixed |
| 4 | Panels do not follow what is shown: *Components* is empty for results, *Run* shows old plots next to a table, *Properties* is empty until a click | all states | open |
| 5 | Four *Open* commands in one menu, two of them missing from the toolbar, one twice; no list of recent files, no drag and drop | menus | open |
| 6 | Nothing leads from a study to its runs and tables, or from a table row (`zeta_0.65`) to that run | — | open |
| 7 | The plots share a narrow panel with the playback; at 1100 px one curve is visible | screenshots | open |
| 8 | Playback belongs to the 3D view, but sits under the plots | — | open |
| 9 | The window title names the recipe even when a run or a molecule is shown | — | open |
| 10 | Sizes and panels are forgotten at every start | — | open |
| 11 | Opening a run stops the window meanwhile; the whole trajectory is in memory as float64 (peak 1.05 GB for 2501 frames of 7036 atoms) | — | open |
| 12 | *Run…* starts the engine on all cores without looking at the queue, where CPU jobs may be running | — | open |
| 13 | The queue is only in the browser; from it no run can be opened | — | open |
| 14 | Axis ticks are odd numbers (0.853, 0.927) | — | open |

The programs today: the builder GUI; the queue dashboard (browser) with its command line; the study
driver and `ucmd-analyze` (command line only).

## 2. Proposal

One window. The notebook in the middle stays and becomes the place for everything large; what is
around it follows the page in front.

```
┌ Open ▾  Save │ Build  Run… │ ◀ what is shown: "base_s1 · 20 °C" ─────────────────┐
├──────────────┬───────────────────────────────────────────────┬─────────────────┤
│ Project      │ 3D view │ Plots │ Sensitivity: runs │ Queue   │ Properties      │
│  Studies     │                                               │ Ruler           │
│   ▸ …-1M     │                                               │                 │
│     runs     │                                               │                 │
│     tables   │                                               │                 │
│  Recent      ├───────────────────────────────────────────────┤                 │
│ Components   │ ▶ ───────●────────── frame 1000/2501, 2000 ps │                 │
├──────────────┴───────────────────────────────────────────────┴─────────────────┤
│ Log (folded, opens on a warning)                                               │
└────────────────────────────────────────────────────────────────────────────────┘
```

1. **Project panel** (left): a folder chosen once (the workspace): studies with their runs (state and
   progress from `status.json`/thermo, as the run list today) and tables, recipes, packages,
   molecule files; and what was opened last. Double click opens.
2. **One *Open*:** a single command and drag and drop; `open_path` already knows every kind.
   *Components* is shown when a recipe is open, else hidden.
3. **Plots page:** the run's plots get a page of the notebook; playback moves under the 3D view. The
   right side keeps *Properties* and *Ruler*.
4. **Links:** a table with a column `run` opens that run by double click (`runs/<run>/…` of the same
   study); a run in the plots page opens its study's tables.
5. **Title and status** name what is shown. Layout and recent files are kept in the user's
   settings (`~/.config/ucmd/gui.json`), never in a package or a run.
6. **Loading** runs and scanning folders happen in a thread; frames are read from the H5MD file when
   shown (float32, a few hundred in memory), so a large run opens at once.
7. **Queue page, read only:** resources, running jobs with progress, waiting jobs, from
   `GET /api/state` of `tools/queue` (schema 1, `docs/design/queue.md` §3); a running study job opens
   its run. Off if no server answers. Nothing is submitted or cancelled from the GUI.
8. ***Run…* warns** when the queue says the CPU is taken; the author decides. (It stays a short local
   preview.)
9. Round axis ticks.

## 3. Boundaries

- The GUI still only shows files and starts the engine by its command line. New is one read-only
  HTTP interface to the queue server (point 7): **an interface between components that is not in
  `spec/`, so it needs the author's yes** (invariant 2). It imports nothing from `tools/queue`.
- The queue's address is machine-specific. It is kept in the GUI's settings file, default off. (The
  draft said the machine profile; that file and its keys are defined in `spec/run-config.md` §4.)
- Viewer, recipe model, run files and all readers stay as they are.

## 4. Order and acceptance (each step one commit with tests, usable on its own)

| Step | Content | Acceptance |
|---|---|---|
| 1 | Plots page, playback under 3D, right side without *Run*; title; round ticks | all B2a and B2c tests; window ≤ 900 × 600 in every state |
| 2 | One *Open*, drag and drop, recent files, kept layout | a path of every kind opens from drop and from *Recent*; a broken settings file is ignored with a message |
| 3 | Project panel, links from tables to runs | the sensitivity study opens runs and tables by double click; a missing run is reported |
| 4 | Loading in a thread, frames on demand | the window answers within 0.1 s while a 5 ns run opens; peak memory below 500 MB |
| 5 | Queue page, warning before *Run…* | fixture state documents; no server, wrong schema and slow server are shown, never block |

## 5. Answered by the author (2026-11-25)

1. Layout: **one adaptive window** (§2), not fixed modes.
2. Queue in the GUI: **read-only page**; nothing is submitted or cancelled (ADR 0016).
3. **All five steps**, each its own commit.
