# 2026-11-25 — SC-3 test 2: does the molecular barostat change the NPT density? (water)

- **Label:** confirmatory. Plan, criteria and `analyze.py` are committed before the first run.
- **Question:** the engine's C-rescale barostat used the atomic pressure for flexible molecules, which at 1 fs reads
  about 129 bar too low in water (`docs/design/SC-3-pressure-estimator.md`). Is the CPU density therefore too
  high, does option B remove that, and do CPU and GPU then agree?
- **Three arms, one folder each** (same recipes, settings and seeds; the trajectories separate
  within picoseconds, so the seeds count as independent):

  | Arm | Folder | Engine | Barostat pressure |
  |---|---|---|---|
  | A | `2026-11-25_water-npt-cpu-atomic` | ucmd 2ea7e82 (its Rust code equals c2cc427, the base of B) | atomic |
  | B | this one | ucmd f291a40, branch `sc3-molecular-pressure` | molecular |
  | G | `2026-11-25_water-npt-gpu` | bridge c2cc427, HIP, double | molecular (Monte Carlo) |

- **Settings:** those of `2026-11-20_water-spcfw-wu`: 512 SPC/Fw, 298.16 K, 1 atm, 1 fs, 9 Å + tail, PME 10⁻⁶. 1 ns per run,
  seeds s1–s3 (packing, velocities); the first 0.2 ns are skipped.
- **Cost:** A and B about 9 h per run on 8 threads (2.7 ns/day, measured earlier), 6 runs, 2.2 days; G about 20 min per run.

## Criteria, fixed before the runs

Seeds are the unit of error. s² is the variance between seeds, pooled over the three arms (6 degrees of freedom);
SE of a difference is √(2 s²/3); "differs" means beyond 2.447 SE (95 %, t with 6 degrees of freedom).

1. **Barostat check (B):** the mean of `pressure_molecular_bar` equals 1.013 bar within 4.303 SE of the three seeds
   (95 %, 2 degrees of freedom), and 4.303 SE is below 65 bar (half the bias; otherwise *unresolved*). If not, nothing else is read.
2. **Effect:** ρ_A − ρ_B. Predicted +0.0058 g/cm³ (129 bar × 4.5·10⁻⁵ per bar); 0.0045–0.0078 for a compressibility
   of 3.5–6·10⁻⁵ per bar. *Confirmed* if it differs from zero and lies in that range; *different size* if it differs from zero
   outside it; *not seen* otherwise.
3. **CPU against GPU:** ρ_B − ρ_G. *Consistent* if it does not differ from zero.
4. **Resolution:** if 2.447 SE exceeds 0.0029 g/cm³ (half the predicted effect), 2 and 3 are *unresolved*, whatever
   the means are. No seed is added after looking.
5. A run whose two halves (0.2–0.6 and 0.6–1.0 ns) differ by more than 7 block errors (the block error of 5 blocks, pooled over the
   nine runs; the difference of two halves has 2 of them, so this is 3.5 σ) is reported as drifting, and 2 and 3 are then not judged.

Not judged: the distance to Wu's 1.012 g/cm³ (design note, "Limits of option B"), and the excess temperature at
1 fs, which A, B and G share (SC-1). Whatever the result, B is not reported as removing the whole pressure excess.

## Running it (after the reboot of 2026-11-25)

`bash studies/2026-11-25_water-npt-cpu-molecular/run_cpu.sh` (B and A in turn, seed by seed) and `run_gpu.sh` (G, only when no other
job holds the GPU). Engines: `$SC3_ENGINES/ucmd-atomic`, `ucmd-molecular` (default `~/.cache/ucmd-sc3`). Both scripts may be
started again; finished runs are skipped. Then `python3 analyze.py`.
