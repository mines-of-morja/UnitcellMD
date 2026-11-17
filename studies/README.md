# Studies

A **study** answers one question with many simulations: a scan over temperatures, a parameter
tuning series, a convergence test. Every study has the same layout, so that months later each
run can be found and its origin is clear (ADR 0011).

- [CATALOG.md](CATALOG.md) lists all studies with their progress (generated).
- Each study's `INDEX.md` shows what is inside and how far it is (generated).
- The driver is `tools/study/ucmd_study.py`.

## Layout of one study

```
studies/
├── README.md                          this file
├── CATALOG.md                         one line per study (generated)
└── YYYY-MM-DD_<short-name>/           one question; the date it was planned
    ├── study.toml                     the plan: systems, conditions, protocol    (git)
    ├── README.md                      the question, the protocol, the caveats    (git)
    ├── INDEX.md, index.json           contents, progress, key numbers (generated)
    ├── systems/<system>/              each system once: recipe.toml (copy), built.ucsys,
    │                                  minimize.toml, minimized.ucsys, logs, status.json
    ├── runs/<system>/<condition>/     each run: run.toml, run.log, status.json, out/
    ├── views/<view>/…                 symbolic links into runs/, sorted another way
    └── logs/driver.log                what the driver did, with times
```

- **One run lives in exactly one place:** `runs/<system>/<condition>/`. Everything else points
  there.
- **`views/` holds only symbolic links**, for example `views/by-temperature/T20C/<system>`. They
  are rebuilt from scratch by every `status`. Deleting `views/` loses nothing.
- **`status.json`** in every system and run folder records the state (`pending`, `running`,
  `stopped`, `done`, `failed`), the engine version, seed, wall time, and a summary of the
  thermo table.
- **Provenance** is in the files themselves: `run.toml` is the exact input, and the engine
  writes versions, the resolved configuration and the package hash into its outputs.

## Rules

1. **New question, new study.** Do not add conditions to a finished study; copy its
   `study.toml` into a new folder instead.
2. **The plan is fixed once runs exist.** If `study.toml` changes the input of an existing run,
   the driver refuses that run rather than mix two protocols in one folder.
3. **Git holds the plans, not the data.** `study.toml` and `README.md` are committed; systems,
   runs, views, logs and the generated indexes stay local (`.gitignore`). When a study is
   finished, its conclusions go into a report under `docs/` or `<repo>/validation/`, with the
   numbers.
4. **Names:** systems are recipe names (`ec-emc_3-7w_1.0M`); conditions are short labels
   (`T-10C`, `T20C`). Exact values (e.g. 263.15 K) are in `run.toml` and `status.json`.
5. **Never edit inside `runs/` by hand.** Re-run with the driver. A run that must be repeated
   goes into a new study, or is deleted completely first.
