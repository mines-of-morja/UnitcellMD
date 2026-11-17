# 0012 — Precision tiers for GPU backends (amends ADR 0010 §3)

- **Status:** accepted 2026-11-17 by the author ("make the best decision", on a proposal for a
  tiered policy with statistical validation).
- **Context:**
  - ADR 0010 admits other backends through a start-up single point within 1e-6 (energy) and 1e-5
    (forces, relative).
  - On the Radeon VII, OpenCL mixed precision runs 77 ns/day against 34 in double for the
    7036-atom electrolyte. Its single-precision forces differ by 5.5e-5 relative, so the run
    would be refused.
  - For equilibrium sampling (NVT/NPT), what matters is ensemble equivalence, not pointwise force
    agreement (ADR 0010 §4).
- **Decision:**
  1. **Tiers:**
     - mixed precision (single-precision forces, double-precision integration and accumulation)
       for thermostatted production runs;
     - double for NVE, validation runs and conformance comparisons;
     - minimization runs on the CPU reference backend anyway.
     The OpenMM backend refuses mixed or single precision without a thermostat.
  2. **Model identity stays pointwise,** with a precision-specific force tolerance. The start-up
     single point must agree within 1e-6 in energy for every precision. Forces must agree within
     1e-5 in double and 2e-4 in mixed precision. A wrong parameter changes energies and forces by
     orders of magnitude more, so the check still guards the model.
  3. **Mixed precision is admitted by a statistical comparison with double** on the same
     hardware and software stack (`ucmd-engine/validation/e37-precision`). Criteria:
     - NPT averages of ρ, U, T and P agree within 3 combined standard errors;
     - the first-peak height of a structural RDF agrees within 3 combined standard errors;
     - the drift of the conserved energy in NVT is at most 2× that of double, plus 1 kJ/mol/ps.

     An absolute drift bound such as 1e-4 kJ/mol/ns/atom was considered and rejected: flexible
     C–H bonds at 1 fs drift by about 0.3 kJ/mol/ns/atom even in double precision on the CPU.
     The comparison is repeated when the stack changes (GPU, ROCm, OpenMM or image).
  4. **Environment pinning:** every output records the GPU (device name, architecture), the
     OpenCL platform, the ROCm SDK version, the OpenMM version, the container image and its ID,
     and the precision (H5MD `/parameters/ucmd/backend`).
  5. **Hardware on the author's workstation:**
     - the Vega 20 card (Radeon VII, gfx906; MI50 class) is the compute device;
     - the RX 580 drives the display and has no compute role.
     The software keeps the ability to use other or several devices: the profile's
     `[backend] device` and the wrapper's `UCMD_OPENMM_DEVICES`.
- **Consequences:**
  - The production default becomes mixed once the comparison passes. Until then it stays double.
  - Bitwise reproducibility stays a property of the CPU reference backend only (ADR 0010 §2).
    GPU runs reproduce within the same pinned stack.
