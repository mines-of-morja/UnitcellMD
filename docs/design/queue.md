# Queue and dashboard — what runs, what waits, what comes next

- **Status:** draft 2026-11-24, written at the author's request ("a queuing system to optimize the
  usage … a lightweight dashboard to see what is in the queue, what is currently running and what
  should be computed next … later maybe larger clusters or another computer to send side tasks").
  **Built 2026-11-25: step 1 (dashboard), step 2 (spool, scheduler, CLI) and step 3 in its first form
  (workers on the LAN with the studies folder mounted, §8). Step 4 (SLURM) waits.** The open
  questions of §6 are answered with defaults (§8); the author may overrule them. Direction given 2026-11-24: this workstation becomes the **server**, and clients on the
  same local network take tasks from it (§1a). This is outside the PLAN.md phase order (it prepares A2.2, `ucmd-launch`), done at the
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

## 1a. Server and clients (direction of 2026-11-24)

- **Server** = this workstation. It owns the job list, the studies and the results, and serves the
  dashboard. **Client** (worker) = any machine on the LAN that runs one small program,
  `ucmd-queue work --server URL`.
- **Pull, not push.** The client calls the server, never the other way round: it registers
  (name, cores, GPU kind, engine version and git hash, free disk), sends a heartbeat every ~15 s,
  asks "a job for me?", and the server hands out the best job whose `needs` the client meets. A
  client that is switched off simply stops appearing; its job goes back to *pending* after a missed
  heartbeat timeout and continues from its last checkpoint if one was uploaded. No firewall rules or
  SSH access to the clients are needed; the server needs one open port in the LAN.
- **A job is data, never a command.** `kind = run`: a package, a `run.toml`, an optional checkpoint;
  other kinds (`build`, `minimize`, `analyze`) are fixed verbs. The client runs only its own
  locally installed `ucmd`/`ucmd-build` on that data, with paths from its own machine profile. The
  server cannot make a client execute arbitrary shell, so a stolen token cannot either.
- **Transfer:** the client downloads the package and `run.toml` over HTTP, runs, uploads
  `thermo.tsv` and the checkpoint periodically and the trajectory at the end (resumable, streamed;
  trajectories are hundreds of MB). The server stores the result exactly where a local run
  would put it (`runs/<system>/<T>/out/`), so the study layout (ADR 0011) does not change.
- **Trust:** one shared secret per LAN in the machine profile (`Authorization: Bearer`), the server
  binds to the LAN address only when a secret is set (without one it stays on 127.0.0.1), no
  internet exposure, TLS left to the network (WireGuard/SSH tunnel if ever needed).
- **Reproducibility:** every output already records tool version and git hash (invariant 9). A job
  may pin an engine hash; clients with another build are skipped. Bitwise identity across different
  CPUs is not promised (invariant 8 is per machine), so replicas of one study should preferably run
  on one machine type; the dashboard shows where each run ran.
- **The local scheduler and the clients use the same code path.** The workstation's own GPU and CPU
  are two clients that happen to live on the server (`work --server http://127.0.0.1`). Then
  there is one way to start work, not a local and a remote one.

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
3. **Clients on the LAN (needs approval).** The server API (`register`, `heartbeat`, `claim`,
   `progress`, `upload`, `finish`; JSON over HTTP, token) and the `work` program of §1a. The
   dashboard shows every client as a resource with its heartbeat, the job it holds and its ETA;
   the `[[remote]]` list of step 1 is then not needed.
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
3. **The clients:** how many, which operating systems (Linux assumed), which hardware (CPU only?
   GPU of which kind?), and can each build or copy `ucmd` and the bridge image? Large outputs:
   is the LAN wired (1 Gbit)? Step 3 waits for this.
5. **Always on?** Should the server run as a systemd user service started at login, and should
   clients be allowed to take work while someone uses the client machine (a `nice`-level and a
   "pause when busy" rule like the game pause)?
4. **Where it lives:** `tools/queue/` now; moves into `ucmd-launch` when A2.2 starts (ADR 0002.3).

## 7. Tasks (added 2026-11-24 at the author's request)

`docs/tasks.toml` lists work that no queue will start by itself, for people and agents to take
(goal, acceptance, what it waits for). The dashboard shows it read-only as `tasks` in the state
document; claiming is an edit of the file. It is not the spool of step 2: a task is a description,
never a command, and nothing is started from it. Tasks for outside contributors stay GitHub issues
(CONTRIBUTING.md).

## 8. What is built (2026-11-25) and what is not

- **Spool** (`qjobs.py`): `queue/jobs/<id>.json`, one `flock`, atomic writes. States `queued →
  claimed/running → done | failed | cancelled`; priority (larger first, then submit order),
  `--first`, `--after` (needs *done*), one study job per study at a time, silent worker (two
  minutes without heartbeat) → job back to `queued` with its place, release on pause.
- **Server** (`qserver.py`, in `ucmd_queue.py serve`): page and state as before; `/api/jobs`,
  `claim`, `heartbeat`, `finish`, `release`, `cancel`, `priority`. GET: this machine without token,
  others with; POST: token and `application/json` always; without a token configured every POST
  is refused and the server will not listen beyond 127.0.0.1. Docs for the tabs are served from
  `tools/queue/docs/`.
- **Worker** (`qworker.py`, `ucmd_queue.py work`): pull model of §1a. Job kinds: `study` (this
  clone's study driver, `--only` the named runs, machine profile and engine per resource tag from
  the worker's own config) and `command` (an argv list, only if the worker config allows it).
  Local guard before taking a job (a container of the GPU image, a live hand-written queue
  script), pause process (the game): graceful stop and release. Cancel: graceful stop, reported
  `cancelled`.
- **Clients** (first form): the client mounts the server's `studies/` folder over its own clone's
  and the driver writes there, so no transfer protocol exists yet. **Not built:** copy-based
  clients (package and checkpoint down, results up) for machines without a shared folder; pinning
  an engine hash per job; per-job profile choice beyond the resource tag; HTTP upload of results;
  submit and cancel buttons in the page (the page only shows; the CLI and HTTP API change things).
- **Answers used for §6 until the author says otherwise:** priority = integer in the job, set at
  submit, changed with `priority`; no preemption except cancel and the game pause (an urgent job
  waits for the running one, or the author cancels it); second computer unknown, the client setup
  is written for a Linux machine with SSH to the server; the server and workers are started by
  hand, with example systemd user units in `tools/queue/systemd/` that nothing installs.
- **Known limits:** a worker that dies leaves its study driver running (it holds the study lock;
  the next worker removes a stale lock file only after the server has requeued the job, so check
  for a leftover driver); `command` jobs trust whoever has the token, so enable `allow_command`
  only on machines you trust; a job cannot be edited, only cancelled and resubmitted.
