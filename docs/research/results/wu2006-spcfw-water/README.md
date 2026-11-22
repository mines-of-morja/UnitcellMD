# wu2006-spcfw-water — SPC/Fw water against Wu, Tepper & Voth (2006)

- **Question:** does UnitcellMD (engine, OpenMM GPU bridge, analysis library) reproduce Table II
  of Wu et al., J. Chem. Phys. 124, 024503 (2006) for SPC/Fw water, with their protocol?
- **Label:** exploration. One 6.5 ns run at one seed; a production set would need independent
  replicas (publication.md, rule 2).
- **Status (2026-11-22):** six of the seven Table II properties agree; the density is 0.47 % low and
  unexplained. The Green–Kubo viscosity agrees with Wu's. Details and caveats in the summary.
- **Summary:** [Wu_et_al_water_summary.pdf](Wu_et_al_water_summary.pdf) (2 pages).

## Inputs (local studies, not in git)

| Study | Used for |
|---|---|
| `studies/2026-11-20_water-spcfw-wu` | the 6.5 ns NPT run: ρ, U/N, ΔH_vap, geometry, ε, D |
| `studies/2026-11-20_water-spcfw-viscosity-cpu` | the 4 ns NVT run at ρ = 1.012, 300.2 K: Green–Kubo η |
| `studies/2026-11-20_water-spcfw-cpu/gas` | gas-phase energy, for Caleman's ΔH_vap definition |
| `studies/2026-11-20_water-spcfw-gpu-twin` | CPU/GPU cross-check (numbers in `data/transcribed.json`) |

Hashes of the files used: `data/manifest.json`. Wu's values and their locations:
`literature.json`.

## Rebuild

```sh
HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python docs/research/results/wu2006-spcfw-water/analyze.py
ucmd-analysis/.venv/bin/python docs/research/results/wu2006-spcfw-water/build.py
```

## Versions

Engine `ucmd 0.0.0`, bridge branch `e25-constraints` at 2ea7e82 (unpushed), OpenMM 8.5.0 with
OpenMM-HIP-7 in `ucmd-openmm:gfx906-hip`, platform HIP, precision double. Analysis:
`ucmd-analysis` at bacb32c. The exact engine hash of each run is in its H5MD provenance
(`data/results.json`, `run.provenance`).

## Known gaps

1. **Density 0.47 % low.** Candidates not yet tested: box size (512 against 216 molecules),
   barostat, PME and long-range correction details. A 216-molecule run is not possible with the
   current cutoff and skin; a cutoff of 0.9 nm with a smaller skin might allow it.
2. **D comparison assumes Wu's D is uncorrected** for the box size (unconfirmed in the text).
3. **Numbers in `data/transcribed.json`** are copied from the study READMEs: the twin runs, the
   conformance values, the 0.5 fs energy. They need analysis scripts of their own.
4. **`literature.json`:** the Yeh–Hummer entry has `checked_vor = false`; the paper was not re-read
   for the ledger.
5. **One seed.** No replica spread.
