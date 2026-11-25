# Connect another computer to this queue

The server is this workstation ({{SERVER_URL}}, token {{TOKEN_STATE}}). A client is any computer
on the same network that runs a **worker**. The worker asks the server for a job, runs it with its
own installed tools and reports back. The server never sends it a command, only a job (a study and
which of its runs).

How results get home: **the client mounts the server's `studies/` folder** and the study driver
writes the runs there. Nothing else is copied. (A copy-based mode for machines without a shared
folder is in the design, `docs/design/queue.md`, and not built.)

## On the server (once)

1. In `~/.config/ucmd/queue.toml` (without a token the server stays on 127.0.0.1 and refuses to
   listen on the network):

       [server]
       bind  = "0.0.0.0"          # or this machine's LAN address
       token = "<a long random string>"      # python3 -c "import secrets; print(secrets.token_urlsafe(32))"
2. Restart: `python3 tools/queue/ucmd_queue.py serve`. Allow the port (8765) for the LAN only.
3. The client needs SSH access (a key) to this machine to mount the studies folder.

## On the client (once)

1. Clone: `UnitcellMD`, `ucmd-engine`, `ucmd-builder` from github.com/mines-of-morja into one
   folder, exactly like on the server.
2. Build the engine (`cd ucmd-engine && cargo build --release`) and the builder
   (`cd ucmd-builder && python3 -m venv .venv && .venv/bin/pip install -e .`). The study driver
   needs both programs, also for studies that start from ready packages. GPU clients also need the
   OpenMM bridge image (`ucmd-engine/bridge/README.md`).
3. Machine profile: `~/.config/ucmd/machine.toml` with the executable paths of *this* computer
   (see the profile on the server for the keys; never copy the server's paths).
4. Mount the server's studies folder **over** `UnitcellMD/studies` of the clone (the relative paths
   of the study plans must keep working), and do not commit in that clone:

       sshfs <user>@<server>:<path to UnitcellMD>/studies <clone>/studies

5. `~/.config/ucmd/queue.toml` on the client:

       [[worker]]
       name     = "office-pc"
       server   = "{{SERVER_URL}}"
       token    = "<the LAN token>"
       provides = ["cpu"]            # tags this machine can serve: cpu, gpu-hip-mixed, ...
       nice     = 10
       # allow_command = true        # only on machines you trust: runs argv lists from jobs

       [worker.tags.cpu]
       profile = "~/.config/ucmd/machine.toml"
       ucmd    = "<clone>/ucmd-engine/target/release/ucmd"

6. Start: `python3 tools/queue/ucmd_queue.py work`. The machine appears in tab Queue within 15 s.
   To stop it gracefully press Ctrl-C: the running study checkpoints and the job goes back to the
   queue.

## Notes

- Replicas of one study should run on one machine type: results are reproducible per machine, not
  across different CPUs (CLAUDE.md invariant 8).
- Heavy output (trajectories) is written over the network mount. A 1 Gbit wired LAN is fine for
  the current runs; the copy-based mode is the answer if it is not.
- A worker can serve one job at a time; start a second `work --worker NAME` with another
  `[[worker]]` for a second slot (not for a GPU).
- Check the connection: the dashboard shows the worker as online with its last contact. A worker
  that cannot reach the server prints the error and keeps trying.
