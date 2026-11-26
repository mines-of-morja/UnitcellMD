# Queue a compute job (for agents and people)

The queue decides when and where compute runs, so that two jobs never meet on one GPU and the
author can see the whole plan on the dashboard ({{SERVER_URL}}). **Do not start GPU work by hand:
submit a job.** A job is data (a study, or a command); the machine that takes it runs it with its
own tools.

*Not to be confused with* `docs/tasks.toml`: a *task* describes work for a person or agent to do;
a *job* is compute that a worker runs. A task may end in submitting jobs.

## Look first

    python3 tools/queue/ucmd_queue.py jobs          # what is queued and running
    python3 tools/queue/ucmd_queue.py state         # the dashboard state as JSON (resources, runs)

## Submit

    # all open runs of a study (it must exist with study.toml and its plan must be final)
    python3 tools/queue/ucmd_queue.py submit study 2026-11-25_my-study --needs gpu-hip-mixed --as <your session name>

    # only some runs of it
    python3 tools/queue/ucmd_queue.py submit study 2026-11-25_my-study --needs cpu --runs base_s1/T20C base_s2/T20C

    # one command (a validation script, an analysis): only workers that are set up to allow it run these
    python3 tools/queue/ucmd_queue.py submit command --needs gpu-hip-double --title "pressure check" -- \
        ucmd-engine-constraints/validation/openmm-pressure/run.sh studies/x/runs/y/T1/run.toml

Options: `--priority N` (larger goes first, default 0), `--first` (before everything queued; ask the
author, say why in `--note`), `--after JOB...` (start only after those are *done*; a failed
predecessor never releases the job), `--title`, `--note`. Commands run in the repository root.

`--needs` is the resource tag, never a machine: `gpu-hip-mixed` (OpenMM HIP, mixed precision),
`gpu-hip-double` (double precision, e.g. the water pressure work), `cpu`, `cpu-light` (a short CPU job for the second
computer, so that it does not wait behind long `cpu` jobs). The dashboard (tab Queue)
lists which workers provide which tags.

## Rules

1. One GPU job at a time per GPU: the queue guarantees it only if everything goes through it.
   While a hand-written queue script (`gpu-queue*.sh`) is alive, the GPU worker waits for it.
2. One job per study at a time (the study driver has one lock per study).
3. Do not change `study.toml`, the recipes or the packages of a study once jobs are queued for it.
4. A job on this machine's studies writes into `studies/<study>/runs/...` exactly as a manual
   `ucmd_study.py run` would. Logs: `studies/<study>/logs/worker-<job>.log`, commands:
   `queue/logs/<job>.log`.
5. New physical parameters need the author (CLAUDE.md). Queueing is not approval.

## Watch, change, cancel

    python3 tools/queue/ucmd_queue.py jobs --all              # including finished ones
    python3 tools/queue/ucmd_queue.py priority JOB 5          # only queued jobs
    python3 tools/queue/ucmd_queue.py stop JOB                # checkpoint, then wait
    python3 tools/queue/ucmd_queue.py continue JOB
    python3 tools/queue/ucmd_queue.py cancel JOB              # ends for good (the dashboard's Kill)
    python3 tools/queue/ucmd_queue.py worker NAME --free      # its owner needs the computer
    python3 tools/queue/ucmd_queue.py worker NAME --use --threads 6

States: `queued` → `claimed`/`running` (a worker holds it; it sends a heartbeat every 15 s) →
`done` | `failed` | `cancelled`. A worker that stops answering for two minutes loses its job: it is
queued again (`requeued` counts) and continues from the last checkpoint. A stopped or freed *command*
job starts again from its beginning (only study jobs continue from checkpoints). A job is released back to
the queue when the machine is needed otherwise (the game pause).

## From another computer

On a machine that is not the server, put this in `~/.config/ucmd/queue.toml` and use the same
commands (they go over HTTP with the token):

    [client]
    server = "{{SERVER_URL}}"
    token = "<the LAN token>"

Without `[client]` the commands write into this machine's spool (`queue/`), which only the server's
workers read.

**A computer that is somebody's own** (a worker set to share it): its user comes first. Do not take
"freed" off a worker you did not free, and do not raise its threads without being asked.
