# 0002 — Local-first, cluster-capable execution

- **Status:** accepted 2026-11-11 by the author ("make the chain modular, so easy local MD can
  run as well as a cluster with more complex stuff"). Cluster details are deferred.
- **Context:** the same system must run both as a quick local job and as a large cluster
  campaign with expensive external force providers, without forking the code paths.
- **Decision:**
  1. A classical run needs only the `ucmd` binary, a system package and a `run.toml`. No
     scheduler, MPI, network, external programs or Python.
  2. Everything heavier is opt-in and composes from the same pieces: external force providers
     (bridge processes, also on other nodes over TCP), GPU-backed providers, heavy output
     backends.
  3. Running many jobs is a separate thin execution layer, `ucmd-launch` (planned in A2.2),
     with pluggable executors: `local` first, `slurm` later. Scheduler-specific code lives only
     there, never in the engine, builder or analysis.
  4. Inputs are location-independent. A package plus `run.toml` gives the same result on a
     laptop and on the cluster. Machine-specific settings (executable paths, scratch
     directories, core counts) live in a per-machine profile, never in packages or `run.toml`.
- **Consequences:**
  - Spike S1 must show a way to build `ucmd` without a system HDF5 installation (e.g. a
    bundled static build), or provide a fallback trajectory format.
  - External program paths (ORCA, Gaussian, Packmol) come from the machine profile.
  - SLURM and module questions wait until A2.2.
