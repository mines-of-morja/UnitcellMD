# 2026-11-20 — rung W engine check: the CPU water run repeated on the GPU

Same recipe, seed and settings as `2026-11-20_water-spcfw-cpu`, run with the OpenMM backend.
Pass: the densities agree within the combined block uncertainty.

## Result (2026-11-21): PASS

HIP, double precision (profile `machine-gpu-double-identity.toml`, bridge of `e25-constraints`
afbc3b2: LJ tail counted as the engine counts it). Conformance with the engine: energy 4.1·10⁻⁸,
forces 7.6·10⁻⁸. 250 ps in 381 s (56.7 ns/day, alone on the GPU), 0 label corrections, no hang.
Averages over 50–250 ps, 5 blocks:

| | ρ (g/cm³) | U/N (kJ/mol) | ⟨T⟩ (K) |
|---|---|---|---|
| engine, CPU | 1.0079 ± 0.0012 | −42.687 ± 0.020 | 298.17 |
| OpenMM-HIP, double | 1.0089 ± 0.0011 | −42.701 ± 0.059 | 298.14 |

The densities differ by 0.0010, the combined uncertainty is 0.0016; the energies agree within
0.3σ. The two backends sample the same ensemble.

**History:** the first attempts (mixed precision, 2026-11-20) were refused by the conformance
check at 4.1·10⁻⁶ (limit 1·10⁻⁶). The cause was OpenMM's count of the LJ long-range correction,
not precision; see `docs/STATUS.md`, 2026-11-21.
