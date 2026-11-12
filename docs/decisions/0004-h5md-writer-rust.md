# 0004 — H5MD trajectories from Rust: `hdf5-metno` with bundled static HDF5

- **Status:** accepted by the author at Gate 0 (2026-11-12). Originally accepted 2026-11-12 by the
  agent, based on spike S1 (`spikes/s1-h5md-rust/`).
- **Context:**
  - The engine must write H5MD trajectories (spec/trajectory-h5md.md) that h5py and MDAnalysis
    read.
  - ADR 0002 requires a way to build `ucmd` without a system HDF5 installation. Here
    `libhdf5-dev` is not installed, and installing it needs sudo.
  - Candidates were `hdf5-metno` 0.15.1 (maintained fork of the `hdf5` crate; C library, optionally
    built from bundled sources) and the pure-Rust `hdf5-pure` 0.48.0. Both are MIT OR Apache-2.0.
- **Results** (Rust 1.99.1, 16-core workstation, local disk):

  | Check | `hdf5-metno` + feature `static` | `hdf5-pure` |
  |---|---|---|
  | build without system HDF5 | ✅ bundled HDF5 built by cmake once: 61 s wall, 0.44 GB RSS; afterwards cached | ✅ no C at all |
  | resulting binary | 5.6 MB, no dynamic HDF5/zlib dependency | — |
  | appending frames to a 3-D `[n, N, 3]` dataset | ✅ resizable chunked datasets | ❌ appends only for rank-1 datasets (compatibility matrix, v0.48) |
  | write 1000 frames × 10 000 atoms, float64 (240 MB) | 0.25 s (≈ 970 MB/s, page cache), file 240.5 MB | not attempted (blocked by the line above) |
  | `ucmd-spec validate-trajectory` | ✅ OK | — |
  | h5py: exact values of frames 0, 1, 999 | ✅ | — |
  | MDAnalysis 2.11 H5MD reader | ✅ 1000 frames, nm→Å conversion correct, time correct; full pass 1.9 s | — |
  | triclinic `box/edges` (rows = a, b, c) | ✅ MDAnalysis reports a = 50 Å, b = 51.54 Å, γ = 75.96° for b = (1.25, 5, 0) nm, i.e. it reads rows as lattice vectors, as the spec says | — |

- **Decision:**
  - The engine's trajectory writer uses `hdf5-metno` with features `static` and `zlib`, in the
    crate `ucmd-io` behind a default-on cargo feature `h5md`.
  - Building needs a C compiler and cmake, but no HDF5 installation.
  - The spec's box convention (rows = lattice vectors) stands as written.
  - The `ndarray` version must match the one `hdf5-metno` uses (0.17 at 0.15.1).
- **Consequences:**
  - `ucmd-io` depends on `hdf5-metno` and `ndarray`. The first build of the engine takes about
    a minute longer.
  - The minimum Rust version stays at 1.85; `hdf5-metno` needs 1.85.1.
  - On the cluster (later, A2.2): either the bundled build (needs `module load cmake`) or a
    feature `h5md-system` linking the cluster's HDF5 module.
  - `cargo build --no-default-features` keeps a lightweight engine without HDF5. It writes only
    the extended-XYZ debug trajectory, for "easy local MD" without any build tooling (ADR 0002).
  - `hdf5-pure` is worth re-evaluating once it supports appends to N-dimensional datasets: it
    would remove the C build entirely.
