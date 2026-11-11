# Checkpoints (spec v0.1)

A checkpoint lets the engine continue a run so that the continuation is **bitwise identical** to
an uninterrupted run (single thread, deterministic providers). The format is private to the
engine: only `ucmd` reads and writes it. Its required content is fixed here.

## Required content

1. **Magic and version:** the ASCII magic `UCMDCHK\0`, then the checkpoint format version
   (u32), the spec version, and the engine version + git hash.
2. **Identity:**
   - SHA-256 of the `system.json` and of the fully resolved run configuration.
   - A restart refuses a mismatch with `E_RESTART_MISMATCH`, unless `--force` is given; the
     override is recorded in the trajectory provenance.
3. **Time:** step (u64) and time (ps).
4. **State:** positions, velocities and cell, as f64 in canonical order. An emergency
   checkpoint stores the last *completed* step.
5. **Dynamics state:**
   - every operator's internal variables (thermostat chain positions and momenta, barostat
     state, the accumulated bath energy);
   - the RNG state of every random stream.
6. **Provider state** (from E3.4): an opaque blob per provider, e.g. the path and hash of an SCF
   wavefunction file.
7. **Output bookkeeping:** for every output, the last step written. On restart, outputs are
   truncated to the checkpoint step and appended.

## Rules

- **Atomic writes:** write to `<file>.tmp`, flush, then rename. A crash never leaves a corrupt
  checkpoint.
- **Emergency checkpoints:** when a provider fails, the engine writes `<file>.emergency` with
  the last good state, then exits with a non-zero status.
- **Encoding:** a little-endian binary layout, chosen in the E1.10 design, documented in
  `ucmd-engine`, and versioned by the format version above.
