# Hands-on testing

What you can try yourself now, with the expected results. Every command and number below
was checked on the workstation on 2026-11-12 (engine branch `e1`, builder branch `b1`).

**When something looks wrong**, report it in chat or as a GitHub issue in the repo concerned.
Include:
- the command and any change you made to `run.toml`;
- the full output, including the `ucmd 0.0.0 (<git hash>)` line;
- what you expected instead.

## 0. Set up once

```sh
cd ucmd-engine                       # inside the UnitcellMD workspace
git switch e1                        # the engine under review (Gate E1)
. "$HOME/.cargo/env"                 # only if `cargo` is not found
cargo build --release                # ~2 min the first time (it also builds HDF5)
alias ucmd="$PWD/target/release/ucmd"
```

## 1. Automated checks (about 2 minutes)

```sh
UCMD_REQUIRE_SPEC=1 cargo test --workspace
```

- **Expected:** every test passes ("test result: ok" for each crate, `0 failed`).
- `UCMD_REQUIRE_SPEC=1` makes the contract tests fail instead of skip when the spec fixtures in
  `../spec` are missing.

## 2. First run: liquid argon, 20 ps (about 10 seconds)

```sh
ucmd check examples/argon-quickstart/run.toml
ucmd run   examples/argon-quickstart/run.toml
```

**Expected output:**
- `OK` from the check;
- `done: 5000 steps in ~10 s (~180 ns/day), final T = 88.94 K`. The final T is exactly this
  value: same seed, same result.

The outputs land in `examples/argon-quickstart/out/` (ignored by git).

**`thermo.tsv`** is a tab-separated table: step, time_ps, potential, kinetic, total, conserved
(kJ/mol), temperature_K, pressure_bar, volume_nm3. Open it in LibreOffice or gnuplot, or view
it with `column -t out/thermo.tsv | less`. What to look for:
- the potential energy rises from −5595 kJ/mol (the fixture starts from a lattice) to about
  −4690 within a few ps, as the crystal melts;
- the temperature fluctuates around 94.4 K (CSVR thermostat);
- `conserved_kjmol` stays at −4578.7, changing by only ~0.04 kJ/mol over the run. This is the
  integrator plus thermostat bookkeeping.

**`trajectory.xyz`** is extended XYZ in Å. Open it in OVITO, VMD, Jmol or `ase gui`. Positions
are unwrapped, so atoms gradually leave the box. That is intended: molecules always stay whole
(PLAN.md D11).

**`checkpoint.ucchk`** is the restart file, written every 2500 steps.

## 3. Restart: a run continues bitwise

Inside `examples/argon-quickstart/`:

```sh
cd examples/argon-quickstart
sed -i 's/^steps = .*/steps = 7500/' run.toml
ucmd run run.toml && cp out/thermo.tsv /tmp/thermo-straight.tsv     # 7500 steps in one go
sed -i 's/^steps = .*/steps = 5000/' run.toml && rm -rf out
ucmd run run.toml                                                    # 5000 steps …
sed -i 's/^steps = .*/steps = 7500/' run.toml
ucmd run run.toml --restart out/checkpoint.ucchk                     # … plus 2500 after a restart
cmp out/thermo.tsv /tmp/thermo-straight.tsv && echo "bitwise identical"
git checkout run.toml
```

- **Expected:** the restart prints `steps 5000..7500 … (restart)`, and `cmp` reports nothing
  except `bitwise identical`.
- Changing anything other than `steps` makes the restart refuse, unless you pass `--force`.

## 4. Single point and export

```sh
ucmd singlepoint run.toml                 # JSON: energy, virial, max force of the initial state
ucmd export run.toml --checkpoint out/checkpoint.ucchk --out /tmp/argon-30ps.ucsys
ucmd check /tmp/argon-30ps.ucsys          # the exported package is a valid system package
```

- **Expected:** `energy_kjmol` = −5594.75…, the same as step 0 in `thermo.tsv`.
- For `ucmd rerun`, write the trajectory as H5MD: rename `trajectory.xyz` to `trajectory.h5`
  in `run.toml` and run again. Then:

  ```sh
  ucmd rerun run.toml --trajectory out/trajectory.h5 --out /tmp/rerun.tsv
  ```

  This re-evaluates the energies of every frame. They match the ones recorded during the run.

## 5. Things to try, including breaking it

| Change in `run.toml` | What happens |
|---|---|
| `timestep_fs = 40.0` | still runs; the conserved energy now drifts by ~9 kJ/mol over 80 ps instead of ~0.04 |
| `timestep_fs = 100.0` | the dynamics explodes. The engine stops cleanly: `non-finite force on atom …; last good state (step 13) saved to out/checkpoint.emergency.ucchk`, exit code 1. It never continues with bad numbers |
| remove the `[thermostat]` block | NVE: the total energy is conserved, the temperature drifts freely |
| `temperature_K = 120` in both places | hotter liquid, higher pressure |
| `ucmd check ../spec/fixtures/invalid/<name>` (from `ucmd-engine/`) | every broken package gives its error code, e.g. `E_NET_CHARGE`, `E_MOLECULE_SPLIT` |

## 6. Physics validation against OpenMM (about 5 minutes)

This needs the two Python environments once (commands table in `CLAUDE.md`):
`spec/validator/.venv` and `tools/oracle/.venv`. Then:

```sh
validation/argon/run.sh
```

It equilibrates argon, runs 100 ps in ucmd and in OpenMM, and compares energies, temperature,
pressure, g(r), diffusion and drift. **Expected: PASS 8/8**, with numbers close to
`validation/argon/REPORT.md`. Exact values differ from the report (different random start),
but every check must pass.

## 7. The builder: an electrolyte box from a recipe (branch `b1` of ucmd-builder)

```sh
cd ucmd-builder
git switch b1
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'   # once; includes RDKit and Packmol
.venv/bin/pytest -q                                          # expected: 83 passed, about 25 s
```

What to try:

| Command | Expected result |
|---|---|
| `.venv/bin/ucmd-build library` | three data sets: `argon-rahman1964`, `opls-aa-carbonates` (EC, EMC, Li, PF6), `water-spcfw` |
| `.venv/bin/ucmd-build compose examples/lp57-1M.toml` | 47 Li, 47 PF6, 168 EC, 332 EMC; box 4.276 nm; 0.998 M |
| `.venv/bin/ucmd-build build examples/lp57-1M.toml -o /tmp/lp57.ucsys` | about 20 s; `wrote /tmp/lp57.ucsys: 7036 atoms …, closest intermolecular pair 0.220 nm`, and a note that the density is a placeholder |
| `../ucmd-engine/target/release/ucmd check /tmp/lp57.ucsys` | `OK`: the engine reads the builder's package. It cannot run it yet; molecular force fields arrive with E2 |
| `.venv/bin/ucmd-build xyz /tmp/lp57.ucsys -o /tmp/lp57.xyz` | open it in OVITO, VMD or `ase gui`: a periodic 4.3 nm box of whole molecules |

Things to try or break:
- Change `molarity_mol_L` or `solvent` in a copy of the recipe and watch `compose`.
- Set `charge_scale = 1.0`, and see `provenance.transforms` in `system.json` change.
- Add a typo to a key: you get an error that names it.
- Add a component with `molecule = { smiles = "CCO" }` (ethanol): `no template … matches`,
  because the library has no ethanol. A new molecule needs a cited source: a library template,
  or a GROMACS topology through `gromacs-top`.

**Validation against OpenMM** (needs `tools/oracle/.venv`):

```sh
python3 validation/b1-openmm/fetch_ligpargen.py /tmp/lpg && validation/b1-openmm/run.sh /tmp/lpg
```

Expected: `PASS` for EC and EMC, then finite PME energies for the full box. See
`validation/b1-openmm/REPORT.md`.

## Coming next

- **E2:** the engine runs molecular systems (bonded terms, PME), then milestone M2a.
- **The GUI preview (B2a):** after M2a.
