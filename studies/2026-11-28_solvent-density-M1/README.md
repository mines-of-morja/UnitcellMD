# V-4: density of the salt-free M1 solvent at 20 °C

- **Label:** measurement, exploration under publication.md rule 1 (engine and bridge are not tagged releases). The plan,
  the reading and `analyze.py` with its tests were committed before the first run.
- **Question:** what is the density ρ0 of the M1 solvent (EC:EMC 3:7 w:w, no salt) at 20 °C and 1 atm? SC-4 has no salt-free
  point. Its intercept, 1.1249 g/cm³ (+3.15 % against the Landesfeind fit at c = 0), is extrapolated from 0.1–3 M. The apparent
  molar volume of the salt depends on ρ0 steeply: 0.5 % in ρ0 moves V_φ by 50 cm³/mol at 0.1 M, 4.6 at 1 M and 1.3 at 3 M
  (Jo's feedback §3a; checked in `test_analyze.py`).
- **Requested by:** task V-4 (`docs/tasks.toml`), from Jo's feedback §3a. Planned by the agent finite-size under the author's
  delegation of 2026-11-28.

## Runs

| System | Box | Seeds |
|---|---|---|
| `m1_solvent_s1..s3` | 168 EC (OPLS-AA, Caleman 2012) + 332 EMC (LigParGen), 6660 atoms, packed at 4.30 nm | packing seeds 20261181–83; velocity seeds from `[protocol] seed` |

- The force field is exactly SC-4's and T2 M1's (recipes copied from T2, without the Li and PF₆ components).
- **Protocol: SC-4's, unchanged** (`study.toml`). NPT 1 atm, 20 °C, **0.5 fs**, Nosé–Hoover τ 0.1 ps, C-rescale (on the GPU the
  Monte Carlo barostat, every 50 steps), 1.4 nm, PME 10⁻⁵, LJ tail, HIP mixed. The queue's `gpu-hip-mixed` tag runs the same
  engine as SC-4 (`ucmd` 2ea7e82, scan profile). 3 ns per run, the first 1 ns skipped.
- **Why 3 ns:** SC-4 measured settling within 0.1 % after 0.25–0.5 ns at 0.5 fs, for the 1 M box and for pure EMC. A salt-free
  liquid relaxes faster than the salt boxes. Keeping SC-4's length keeps the point comparable.
- **Cost:** about 1.3 h of GPU per run (7036 atoms ran 1180–1290 steps/s at 0.5 fs in SC-1; 6000000 steps). Three runs, about
  4 h, or about 5.5 h with the GPU-hang margin. One queue job per seed, so that each job stays under 2 h.

### Decisions (agent finite-size, under the author's delegation)

- **Decided 2026-11-28 by agent finite-size under the author's delegation: the 1 M box's solvent counts (168 EC + 332 EMC),
  not the 0.1 M box's (336 + 664).** Reason: half the cost per seed; the density's seed spread at this size is 0.045 % (SC-1,
  1 M), far below what V_φ needs; and the 1 M point, the one the ζ estimate uses, then has the same solvent counts. With a 1.4 nm
  cutoff and the LJ tail, the box-size effect on the density is expected to be below this spread (not measured here). What would
  change it: a finite-size effect on the density seen elsewhere (e.g. in V-2's box-size series).
- **Decided 2026-11-28 by agent finite-size under the author's delegation: three independent packings, not three velocity seeds
  of one packing.** Reason: publication.md rule 2 (errors from independent starts). What would change it: nothing in this study.
- **Decided 2026-11-28 by agent finite-size under the author's delegation: V_φ from now on uses ρ0 and the salt densities at the
  same time step (0.5 fs).** Reason: the ζ estimate of the 26 November summary (ζ ≈ 0.98 at 1 M; Jo's §5 asks which V_φ) combined
  the 1 fs density of scan run `base_s1` (V_φ = 72.4 cm³/mol, `docs/research/density-c-T/v_phi_zeta.json`) with the 0.5 fs
  intercept. The 0.5 fs density of SC-1 (three seeds) gives V_φ = 70.6 and hence ζ ≈ 0.95, the number Jo found. The 1 fs
  ζ probes are kept only for the slope dV_φ/dζ, where the time step cancels to first order. What would change it: a ζ series at
  0.5 fs.

## Reading, fixed before the runs

1. **Settling:** a seed whose two halves of the analysed window (1–3 ns) differ by more than 0.3 % (SC-4 criterion 3) is not
   settled and is left out. With fewer than two settled seeds the result is *unresolved*. No run is extended after looking.
2. **ρ0** = mean of the settled seeds; its error is the SE over the seeds.
3. **Is SC-4's straight line right down to c = 0?** Compare ρ0 with the line's intercept (least squares through the four 20 °C,
   0.5 fs points: SC-4's 0.1, 2 and 3 M, SC-1's 1 M; intercept SE from the residuals, now 0.0017 g/cm³). *Consistent* if they
   differ by at most 2 combined SE. Otherwise the model's ρ(c) bends below 0.1 M, and V_φ at low c changes as computed in step 5.
4. **Against the reference and against ideal mixing (reported, not judged):**
   - the Landesfeind fit at c = 0, 20 °C: 1.0905 g/cm³ (ledger `landesfeind2019_density_fit_ec_emc_3_7`; stated for 0.1–3 M,
     good to about ±0.6 %; Fig. S1 has markers at 0 M, read in `docs/research/landesfeind-density/README.md`, not yet in the
     ledger);
   - ideal mixing of the model's pure-solvent errors: M1 EC at 39 °C (1 fs, `2026-11-20_ec-opls-test`) against 1.3214 g/cm³
     (ledger `caleman2012_ec_oplsaa`), and LigParGen EMC at 25 °C (0.5 fs, SC-1) against 1.00688 g/cm³ (ledger
     `density_dmc_emc_ec_fluid2018`). `analyze.py` gives **+2.22 %** with these inputs (+1.99 % with EMC at 1 fs). It assumes
     temperature-independent relative errors and equal excess volumes in model and reality. The difference between measured and
     predicted is then the model's excess volume of mixing minus the real one, plus the reference's own error. There is no
     criterion: neither excess volume is known.
5. **V_φ at 0.1, 1, 2 and 3 M** with the measured ρ0 (`apparent_volume.py`'s formula, each box's own concentration). The error
   combines the SE of ρ0 and of each point's density. The 1 M point has three seeds (SE). The single runs at 0.1, 2 and 3 M get
   the per-run SD of the three 1 M seeds, an assumption. Shown next to V_φ with the extrapolated intercept (now 84.5, 70.6, 71.3,
   72.3 cm³/mol) and to Landesfeind's 55.7.
6. **ζ estimate at 1 M** (the third decision above): ζ* = 0.75 + (55.7 − V_φ(1 M, 0.5 fs)) / (dV_φ/dζ), with dV_φ/dζ from the
   scan's ζ 0.65 and 0.85 probes, all with the measured ρ0. Reported, not adopted: ζ is not chosen from a density without the
   author.

**Prediction (before the runs):** ρ0 about 2.2 % above the fit, i.e. about 1.115 g/cm³, which is 0.010 g/cm³ (about 6 intercept
SE) below the extrapolated intercept. Then V_φ at 1 M falls from 70.6 to about 62 cm³/mol, and the 0.1 M point becomes
meaningless (its V_φ changes sign within ±0.2 % of ρ0). If instead ρ0 matches the intercept, ideal mixing fails by about 0.9 %.

**Already seen:** SC-4's four points and their line (`docs/research/density-c-T/sc4.json`, `apparent_volume.json`). No
salt-free M1 run exists.

## Running it

    python3 tools/queue/ucmd_queue.py submit study 2026-11-28_solvent-density-M1 --needs gpu-hip-mixed \
        --runs m1_solvent_sN/T20C --priority 2 --as agent-finite-size      # one job per seed, N = 1, 2, 3

Then, from the workspace root: `python3 studies/2026-11-28_solvent-density-M1/analyze.py docs/research/density-c-T/v4.json`.
