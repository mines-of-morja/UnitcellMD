# Results: summaries with their data

One folder per **result** — a question answered with numbers, such as "does the engine reproduce
Wu et al. 2006 for SPC/Fw water?". A result holds the summary document, the small data behind it,
and the scripts that turn study data into both. It is the place a future paper takes its
tables, figures and supplementary information from (`docs/research/publication.md`).

How this differs from its neighbours:

| Place | Holds |
|---|---|
| `studies/<date>_<name>/` | the runs of one question (plans in git, data local), ADR 0011 |
| `docs/research/trials/` | planned trials with pass criteria set before the runs |
| `docs/research/summary/` | the held summary PDF for the JMU contacts (decision 12 of publication.md) |
| **`docs/research/results/<name>/`** | **a finished comparison: summary, derived data, scripts** |

## Layout of one result

```
docs/research/results/
├── README.md                       this file
└── <literature-or-topic>-<system>/ e.g. wu2006-spcfw-water
    ├── README.md                   question, label, status, studies used, how to rebuild, gaps
    ├── analyze.py                  study data  → data/            (needs ucmd-analysis)
    ├── build.py                    data/ + literature.json → figures/ and the summary PDF
    ├── literature.json             ledger of every number quoted from a paper (rule 3)
    ├── data/
    │   ├── results.json            every number of the summary, from analyze.py
    │   ├── traces_*.csv            small series behind the figures
    │   ├── transcribed.json        numbers not recomputed here, each with its source (to shrink)
    │   └── manifest.json           the local inputs: path, size, sha256, DOI once archived
    ├── figures/                    PNGs written by build.py
    └── <Name>_summary.pdf          the summary (about two pages)
```

## Rules (they come from `docs/research/publication.md`)

1. **Numbers come from scripts.** The summary reads `data/results.json` and `literature.json`.
   A number typed into `build.py` is a defect. What `analyze.py` cannot yet recompute goes into
   `data/transcribed.json` with its source, so the gap is visible.
2. **Label every result `exploration` or `production`** in its README. Only a production set (its
   question, design and pass criterion written before the first run; independent replicas;
   tagged releases) may feed a paper.
3. **Literature numbers have a ledger entry** (value, table or page, version read, whether it was
   checked against the version of record). Before any submission every entry has
   `checked_vor = true`.
4. **Large data stays out of git.** Trajectories remain in `studies/…/runs/`. `manifest.json`
   records their sha256, so a result can be matched to its inputs and later to an archive with a
   DOI. Never commit copyrighted PDFs.
5. **Negative and unexplained results stay in.** The summary has a section for what is not
   explained; the README keeps the history.
6. **A changed result is rebuilt, not edited.** Re-run `analyze.py` and `build.py`; the PDF is dated
   inside.

## Rebuilding

```sh
HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python docs/research/results/<name>/analyze.py
ucmd-analysis/.venv/bin/python docs/research/results/<name>/build.py
```

`reportlab` is installed in `ucmd-analysis/.venv` by hand (`pip install reportlab`), not declared in
any `pyproject.toml`: it is a build tool of the summaries, not a dependency of the engine, builder or
analysis. A fresh virtualenv needs the same command.

## Index

| Result | Label | Question | Summary |
|---|---|---|---|
| [wu2006-spcfw-water](wu2006-spcfw-water/README.md) | exploration | SPC/Fw water against Wu, Tepper & Voth 2006 (Table II) | [PDF](wu2006-spcfw-water/Wu_et_al_water_summary.pdf) |
