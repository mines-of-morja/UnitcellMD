# 0011 — Studies: one folder per question, one place per run, views as links

- **Status:** accepted 2026-11-17 by the author, who asked for "a proper file structure, so we
  won't get lost" and "a symbolic archive that shows what is inside each folder" for scans
  such as the EC temperature scan, and many more to come.
- **Context:**
  - Scans multiply quickly: 35 systems × 7 temperatures are already 245 runs, and tuning
    series will add more.
  - Ad-hoc run folders (`<package>.runs/<date-time>` from the GUI, `examples/EC/runs/`) are fine
    for single runs, but they do not show which question a run belongs to.
- **Decision:**
  - `studies/YYYY-MM-DD_<name>/` in the umbrella workspace, one folder per question:
    - `study.toml`: the plan (systems, conditions, protocol templates);
    - `systems/<system>/`: each system built and minimized once;
    - `runs/<system>/<condition>/`: each run in exactly one place;
    - `views/`: symbolic links that sort the same runs by other keys;
    - generated `INDEX.md` / `index.json` per study and `studies/CATALOG.md` across studies.
  - The driver `tools/study/ucmd_study.py` orchestrates only:
    - it calls `ucmd-build` and `ucmd` as programs and reads only spec'd files;
    - it is resumable and stops gracefully;
    - every run gets a seed fixed by the study seed and its id.
  - Git holds `study.toml` and `README.md`; the data and the generated files stay local.
  - Rules are in `studies/README.md`. The main one: new question, new study; the plan is fixed
    once runs exist.
- **Consequences:**
  - The study driver is not `ucmd-launch` (ADR 0002). It runs locally and sequentially.
    Cluster submission belongs in the execution layer when it exists, and can read the same
    `study.toml`.
  - Run summaries in INDEX.md are bookkeeping (means over the second half); interpretation
    stays with ucmd-analysis.
