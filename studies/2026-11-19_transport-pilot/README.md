# Transport pilot (2026-11-19)

- **Question:** does the whole transport chain work on real data, and how large are the error
  bars? The chain is a 20 ns NVT production on the GPU, then `ucmd-analyze transport`: self- and
  collective MSDs → D, Onsager L_ij → κ, t₊ (COM frame), ionicity.
- **System:** 1 M LiPF₆ in EC:EMC 3:7 at 20 °C. The start is the end of the 3 ns NPT run
  (`2026-11-17_electrolyte-npt-gpu`), scaled to the mean volume of its last 500 ps (Lehnert 2025
  SI S1.1).
- **Caveat:** the force field is the current LigParGen set. Its Li⁺ shells exclude EC
  (docs/research/reproduction-plan.md), so κ, t₊ and D are **not** expected to match Lehnert or
  Landesfeind. This run tests the method and the noise, not the force field. ζ = 0.75 is
  Lehnert's value for his own force field.
- **Protocol:** Lehnert 2025 settings (1 fs, Nosé–Hoover, PME, tail correction on); mixed
  precision (ADR 0012); a frame every 2 ps; checkpoint every 0.5 ns.
