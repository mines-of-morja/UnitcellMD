# Pure-solvent densities, tail correction on (2026-11-17), research plan level 1

- **Same question as `2026-11-17_pure-solvent-densities`,** with the agreed protocol:
  - the LJ tail correction is on (ADR 0009 amendment, 2026-11-17);
  - the barostat tries a move every 25 steps;
  - mixed precision on the GPU if ADR 0012's check passed (`ucmd-engine/validation/e37-precision`),
    otherwise double.
- **Reference:** manufacturer densities from Lehnert 2025 SI Table S2: EC 1.321 (liquid; compared
  at 40 °C), EMC 1.006, DMC 1.069, PC 1.204, MP 0.915 g/cm³ (assumed 25 °C).
- **The earlier study (tail off)** stays as the comparison for the tail effect. EMC: 1.0278 ±
  0.0011 g/cm³ at 25 °C without the tail correction.
