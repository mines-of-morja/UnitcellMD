# 0005 — OpenMM as the validation oracle, installed from PyPI

- **Status:** accepted 2026-11-12 by the agent, based on spike S2 (`tools/oracle/`). To be
  reviewed at Gate 0.
- **Context:**
  - PLAN.md D10 makes OpenMM the reference for every classical term.
  - The question was whether it installs cleanly for Python 3.13, which is the system Python
    (Debian; conda is not available), and whether its results can be trusted as a reference.
- **Results:**
  - `pip install openmm` gives **OpenMM 8.6.1** with the **Reference** and **CPU** platforms.
    There is no OpenCL platform in this build.
  - A spec-package → OpenMM converter (`oracle.py`) builds LJ via `CustomNonbondedForce`. This
    gives exact control over the mixing rule and the cutoff mode; `NonbondedForce` only knows
    Lorentz–Berthelot.
  - Cross-check with an independent NumPy brute force on `argon-864` (rc = 0.85 nm):
    - energies agree to 10⁻¹⁰ relative and forces to 10⁻⁹ relative, for both `truncate` and
      `potential-shift`;
    - the finite-difference strain derivative of the OpenMM energy equals the analytic virial
      Σ r_ij·F_ij to 10⁻⁵, which confirms the spec's W = −∂E/∂ε convention numerically;
    - OpenMM's dispersion correction equals the analytic formula to 10⁻⁹.
  - Reference results for E1.7 are committed in `tools/oracle/reference/argon-864/`:
    E(truncate) = −5598.770429 kJ/mol, E(potential-shift) = −5218.991948 kJ/mol, plus forces
    and the virial tensor.
- **Decision:**
  - `tools/oracle` uses its own venv with pinned versions (`requirements.txt`) and the Reference
    platform in double precision. References are files in the repo, so the engine's tests
    don't need OpenMM.
  - Extend the converter in E2: bonded OPLS terms, exclusions and 1-4 pairs, PME with explicitly
    matched parameters; OPLS's geometric mixing needs custom forces or exceptions.
- **Consequences:**
  - The engine tests compare against committed numbers, so CI needs no OpenMM.
  - "OpenMM as a GPU provider" (E3.7) needs an OpenCL-enabled OpenMM build (conda-forge or a
    source build) and an OpenCL driver for the AMD GPUs. The pip wheel used here has no
    OpenCL; decide when E3.7 starts.
