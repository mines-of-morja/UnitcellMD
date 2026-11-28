# 0019 — Queue clients: trust levels, what each may touch, how their results are checked

- **Status:** accepted 2026-11-28 by agent decisions, under the author's delegation of that day.
  To be reviewed by the author. The SSH, token and machine-config steps are the author's own.
- **Context:**
  - **The design:** [queue.md](../design/queue.md) §10 proposed a client-security order and left
    it open.
  - **The client today:** the second computer, `soricel-pc`, mounts `studies/` over SFTP with a
    key that can read and write every file of the account.
  - **The token:**
    - one shared token lets every holder stop, kill and submit study jobs;
    - command jobs are refused over HTTP since 2026-11-27;
    - the token appeared once in an agent's tool output.
  - **Evidence for result checks:**
    - CPU runs are byte-identical on both machines (ADR 0010; `studies/2026-11-25_queue-client-test`);
    - the e37 mixed-against-double comparison passed on the client's CUDA stack (2026-11-26).
- **Decision:**
  1. **Levels:**
     - **Server** (the workstation): the author's token, any job kind.
     - **Mounted LAN client** (only `soricel-pc`). Its SSH key is limited by:
       - `restrict` and `from="<its address>"`;
       - a forced `sftp-server` inside `bwrap` that shows `studies/` and nothing else.

       It takes study jobs only.
     - **Every other client:** copy-based only (job bundle down, results up), with no file
       system access. The server accepts only the files of that client's job, with size limits.
  2. **Integrity guard on the server.** Before the workstation runs a script or an analysis of a
     study that a client wrote into, `git status` of that study must show no changed tracked
     file. It must also show no untracked file outside `runs/` and the generated index files.
  3. **Tokens:** one per client, naming the client. A client token may:
     - claim jobs for its tags;
     - report on its own jobs;
     - free or throttle its own worker.

     Only the author's token, which stays on the workstation, may submit, cancel, reprioritise
     or control other workers.
  4. **Internet:** only through a VPN (WireGuard or Tailscale); never an open port.
  5. **Result checks:**
     - **CPU:** for each study a client runs, the workstation repeats a prefix of one run (the
       first checkpoint interval, at most 10⁴ steps) and compares `thermo.tsv` byte for byte.
     - **GPU:** client results enter a production set only if one replica of the study is
       repeated on the workstation and agrees by ADR 0012 §3.
     - Any mismatch quarantines that client's results until it is explained.
  6. **GPU tags on clients:** a precision tag such as `gpu-cuda-mixed` is switched on only after
     the comparison of ADR 0012 §3 has passed on that client's stack. It is repeated when the
     GPU, driver, OpenMM or image changes. All replicas of a study run on one machine type;
     results from two GPU stacks are never pooled within a study.
  7. **Order of work:**
     1. rotate the token and limit the SSH key (author);
     2. the guard (2) and the per-client tokens (3), as code with tests;
     3. copy-based clients before any further client.
- **Consequences:**
  - **Soricel:** it keeps working after one remount, and loses access to everything outside
    `studies/`.
  - **Cost:** GPU production sets carry about one extra replica in four; the CPU checks are
    cheap.
  - **Code still to write in `tools/queue`:** the guard, token scopes and copy-based transfer.
  - **Not covered:** a client that returns plausible but wrong numbers on a GPU between repeats.
    The repeat rate bounds that risk; it does not remove it.
