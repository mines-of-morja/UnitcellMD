# Queue and dashboard — what runs, what waits, what comes next

- **Status:** draft 2026-11-24, written at the author's request ("a queuing system to optimize the
  usage … a lightweight dashboard to see what is in the queue, what is currently running and what
  should be computed next … later maybe larger clusters or another computer to send side tasks").
  **Step 1 (the read-only dashboard) is built with this draft; steps 2–4 wait for the author's
  review.** This is outside the PLAN.md phase order (it prepares A2.2, `ucmd-launch`), done at the
  author's explicit request.
- **Why:** today "the queue" is a set of hand-written shell scripts (`gpu-queue3.sh` … `11.sh`)
  that wait for each other with `pgrep`, plus the study driver's own run order, plus a pause when
  the author starts a game. Nothing shows the whole picture; on 2026-11-24 a validation job and a
  queued scan met on the one GPU because the scripts do not know about ad-hoc jobs.

## 1. Model (the same for every step)

Three nouns, all file-based, none tied to a scheduler (ADR 0002):

| Noun | Is | Where its state lives today |
|---|---|---|
| **Job** | one unit of work: a run (`runs/<system>/<T>/`), a whole study, or a command | `status.json` per run (ADR 0011); study `index.json` |
| **Resource** | something that can do a job: `gpu0`, `cpu`, later `node-b:gpu0`, a SLURM partition | profile (`~/.config/ucmd/machine-*.toml`), telemetry file, `docker ps` |
| **Node** | one machine that has resources and jobs and answers `GET /api/state` | the dashboard process on that machine |

A job needs a resource *kind* (`gpu-hip-mixed`, `cpu`), never a host. A node that runs the
dashboard agent publishes its state as one JSON document (§3). The dashboard of the workstation
shows its own node and any number of remote nodes (fetched from their `/api/state`). Inputs stay
location-independent (ADR 0002.4): a job is a package plus `run.toml`; a remote node gets it by
copy (`rsync`/`scp`) and returns the output folder, so a remote node needs no shared file system.

## 2. Steps

1. **Read-only dashboard (built).** Collects the state of this machine from files and processes,
   shows it in one page, serves JSON. Changes nothing, starts nothing.
2. **Spool and scheduler (needs approval).** A `queue/` folder of job files (`id`, `kind`,
   `needs`, `priority`, `after`, `state`) and one small scheduler process that starts the
   highest-priority job whose resource is free, respects the game pause, and replaces the
   hand-written queue scripts. Submitting = writing a file (`ucmd-queue submit …`), cancelling =
   `ucmd-queue stop` (graceful: checkpoint, as the study driver does today). The study driver
   remains the thing that runs one study; the scheduler decides which study/run goes to which
   resource and when.
3. **Second node (needs approval).** The same agent on another computer; the scheduler on the
   workstation hands it jobs over SSH (`rsync` the package, run `ucmd`, pull the result). Transport
   is SSH only: no new daemon with open ports; the dashboard of a remote node is reached through
   `ssh -L`.
4. **Cluster executor (needs approval, A2.2).** `slurm` executor in `ucmd-launch` that turns a job
   into `sbatch`; the dashboard reads `squeue`. Scheduler-specific code stays in that layer.

## 3. The state document (step 1, `GET /api/state`, schema 1)

```
{ "schema": 1, "node": "workstation", "time": "…Z",
  "resources": [ {name, kind, state: busy|idle|paused|unknown, detail, telemetry{…}, holders[…]} ],
  "running":   [ {study, run, step, steps, fraction, ps_per_h, eta_s, state, driver_pid, orphan} ],
  "queues":    [ {name, pid, state: active|waiting, description, studies[…]} ],
  "next":      [ {rank, study, run, why} ],
  "studies":   [ {name, question, counts{}, total, driver_pid, scheduled_by[…], unscheduled} ],
  "events":    [ last lines of the resume log ] }
```

- *running* comes from `status.json` + the driver's `driver.pid` + the last row of `thermo.tsv`.
  A run whose `status.json` says `running` but whose driver is gone is reported as **orphaned**.
- *next* is rule-based until step 2 gives jobs a priority: the remaining runs of the running
  study in plan order, then the waiting queue scripts in number order. Studies with open runs
  that nothing will start are listed as **not scheduled**, never in *next*.
- ETA = progress over the last ~10 minutes of polls; not shown during the first minute.

## 4. Files

- `tools/queue/ucmd_queue.py` (standard library only, Python ≥ 3.11), `dashboard.html`,
  `test_ucmd_queue.py`, `queue.example.toml`.
- Machine-specific settings (telemetry file, queue-script folder, the process whose presence
  pauses the GPU, remote nodes) in `~/.config/ucmd/queue.toml`, never in the repo.
- Run: `python3 tools/queue/ucmd_queue.py serve [--port 8765]`, then open `http://127.0.0.1:8765`.
  `state` prints the JSON once. Binds to 127.0.0.1; no request starts, stops or writes anything.

## 5. Acceptance tests (step 1)

- Fixture studies with pending, running, orphaned, done runs give the expected `running`,
  `next` and `studies` entries; progress and fraction from a fixture `thermo.tsv`.
- A missing telemetry file, no docker, no config, an unreadable `status.json`: the page still
  renders, the fault is reported in the document (`errors`), never replaced by zeros.
- A remote node that does not answer shows as unreachable; the local node is unaffected.
- No request path writes or executes anything (test: `POST` is refused).

## 6. Open questions for the author

1. **Priority:** who sets it? Proposal: `priority` in the job file (default: submit order), the
   author overrides in the dashboard later; urgent = `ucmd-queue submit --first`.
2. **Ad-hoc jobs** (a 5-min validation) while a long scan runs: wait, or preempt the scan (it stops
   gracefully and resumes from its checkpoint, as with the game pause)? Proposal: wait unless the
   job says `--preempt`.
3. **Second computer:** which machine, which GPU/CPU, is SSH with a key available? Step 3 waits
   for this.
4. **Where it lives:** `tools/queue/` now; moves into `ucmd-launch` when A2.2 starts (ADR 0002.3).
