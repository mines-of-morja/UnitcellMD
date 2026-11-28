# Queue controls with interruptions (not a result)

- **Label:** exploration; a test of the queue.
- **Why:** `2026-11-27_queue-controls-test` ran through on `soricel-pc` (6 threads, 735.8 s, `done`) without anyone
  using the controls, so its checks 2 and 3 were not exercised. This is the same plan and seed, interrupted on purpose.
- **Actions** (command line, by the workstation session): free the computer and use it again; stop the job and continue
  it; set 3 threads and back to 6.
- **Check, fixed before the run:**
  1. After each action the job reaches the expected state, and while freed or stopped the step count does not move.
  2. Every restart continues from a checkpoint and the job ends `done`.
  3. `thermo.tsv`, one row per step, equals that of the uninterrupted run (bit-identical, also across restarts and thread
     counts). A difference is reported, not explained away.

## Result (2026-11-27): all three checks passed

| Action | Reached after | While not running |
|---|---|---|
| free | 15 s (released at step 3 400) | step unchanged for 60 s |
| use again | continued from the checkpoint | |
| stop | 15 s (held at step 6 800) | step unchanged for 60 s |
| continue | continued from the checkpoint | |
| 3 threads, then 6 | restarted with each count (`run.log`) | |

- Four stops and restarts (after steps 3 424, 6 859, 9 111, 10 470), job `done`.
- `thermo.tsv` is byte-identical to the uninterrupted run: 201 rows, SHA-256
  `8308835dfd7f97c4a42fe6078520c1f872cdf5f651e7c4b8f2d098020378b63b` for both.
- Kill was not exercised on a running job.
