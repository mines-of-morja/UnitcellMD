# Decisions taken under the author's delegation, 2026-11-28 (agent "decisions")

The author, 2026-11-28: "can you spawn agents that make all of these decisions with a reasoning in mind? … let agents
make the decision".
- Each decision below is recorded at its question in the design doc, with its reason and what would change it.
- The author may overrule any of them. "Reversible" means that undoing it costs no lost work.
- Not covered here:
  - E2.5 §6 and E2.7 §7 (agent "consistency");
  - V-1 (agent "viscosity");
  - V-2 and V-4 (agent "finite-size");
  - V-5 (agent "literature");
  - SC-7, which the author decided personally on 2026-11-28 ("for SC-7 I take the recommendations").

## 1. The decisions

| Doc | Question | Choice | Reason, in one line | Reversible |
|---|---|---|---|---|
| [A1.5](../design/A1.5.md) §8 | approval to implement | **approved, as built** (PR #4: COM, SOL, VOL); per-solvent frames come with the production runs | ADR 0013 is accepted and the code meets it; the pilot reproduces T1, so no new data is needed | yes |
| [A1.5-green-kubo](../design/A1.5-green-kubo.md) §7 | Q1: A, or also C | **A only** (author, 2026-11-25); C deferred, no spec change | GK is a check of the analysis, not an independent estimate | yes |
| same | Q2: dedicated run | **1 M M1 box, 20 °C, 1 fs; 200 ps NVT (mixed) + 200 ps NVE (double) from one equilibrated state; velocities every 5 fs, float32; bridge from engine `main`**. The same job is SC-2's HIP label check | about 30 min of GPU; tests the thermostat risk; fits in memory | yes |
| same | Q3: cutoff rule | **rule 2 with no default window**, fixed in the README before comparing | a default invites tuning (risk 7) | yes |
| same | Q4: velocities in `Trajectory` | **optional field**, as built (PR #5) | one reader keeps the frames aligned | yes |
| [E2.9](../design/E2.9.md) P8 | CPU speed target | **none; E2.8 stays deferred.** One benchmark measurement before the software paper | the GPU does production; speed work risks ADR 0010 | yes |
| [E3.7](../design/E3.7.md) Q3 | spec text for `[backend]`, exit codes, restart records, XYZ | **new 0.1.4, documentation only, after tagging 0.1.3** ([ADR 0018](0018-spec-releases-and-pins.md)) | 0.1.1 is closed inside `spec-v0.1.2`; 0.1.3 is pinned by CI | yes, until tagged |
| [SC-7](../design/SC-7-emc-refit.md) §5–§6 | Q1–Q7 | **Decided by the author 2026-11-28 ("for SC-7 I take the recommendations"), not delegated.** The orchestrator records it in the design doc. | — | — |
| [queue](../design/queue.md) §6 | defaults of §8 | **confirmed**: integer priority; no automatic preemption (manual by stop/continue); one known client; **no always-on services** for now | the data disk needs a manual check after a crash | yes |
| same | §10: client security | **in order:** token rotation and soricel's key in a `bwrap` SFTP sandbox; a guard for study scripts and per-client tokens; copy-based clients before any further client; VPN only; repeats of client results ([ADR 0019](0019-queue-client-trust.md)) | closes the whole-account access first, the cheapest step | yes |
| same | step 4: SLURM | **deferred** | no cluster account; nothing could test it | yes |
| [B2c](../design/B2c.md) step 4 | compare five molecules | **deferred, not rejected** | T6 is a side result; step 1 already shows the clusters in turn; the author's GUI tests come first | yes |
| housekeeping | spec tags | **no separate 0.1.1 tag; tag `spec-v0.1.3` at `0e7befc`; then 0.1.4** (ADR 0018) | one version name, one content | yes, until tagged |
| housekeeping | merge order | **engine: done** (everything in `main` since 2026-11-27); **umbrella** PR #12 after V-5 commits; **analysis** main fast-forwards to `claude/3-thermodynamic-factor`; **builder** `claude/a17-nacl-spce` after its study (§3) | the branches are linear; the conflicts are known | yes |
| housekeeping | engine `UMBRELLA_REF` | **already moved** to `0e7befc` on 2026-11-27; name the tag `spec-v0.1.3` once it exists; ADR 0018 rule 6 for later moves | same commit, readable name | yes |
| housekeeping | `gpu-cuda-mixed` on soricel | **admit**: ADR 0012 §3 passed on the GTX 1660 SUPER (z ≤ 0.55, drift ok), with conditions (§2 D) | the criteria are met; the two deviations do not touch the NPT runs or the analysis code | yes |
| housekeeping | `run.sh` realpath fix | **fix** `validation/e37-precision/run.sh` line 10: `PY="$PWD/../../bridge/.venv/bin/python"` | `realpath` leaves the venv; the workstation's result is unaffected (its system Python has h5py) | yes |
| housekeeping | queue token | **rotate** at the next idle gap (author, §2 A) | it appeared once in an agent's tool output | — |
| task SC-2 | why blocked | **only the HIP label check is left** (the branch is merged); it runs as part of A1.5-GK Q2 | the GPU block (the scan) ended 2026-11-25; no check was ever submitted | — |

## 2. What the author has to do (outside the repo, or not delegated)

**A. Rotate the queue token.**
- When: at a gap with no running command job; never cancel a running command job (STATUS, 2026-11-25). On
  2026-11-28 the CPU job `…baf5` is done; the GPU runs study jobs, which checkpoint and requeue.
- Steps:
  1. In your own terminal (not an agent session):

         python3 -c "import secrets; print(secrets.token_urlsafe(32))"

  2. Put the new value into `~/.config/ucmd/queue.toml` on the workstation: `[server] token` and the `token` of each
     `[[worker]]`. Do the same in soricel's `~/.config/ucmd/queue.toml`.
  3. Stop the workers with Ctrl-C (a study job checkpoints and goes back to the queue), then the server. Start
     `python3 tools/queue/ucmd_queue.py serve` and the workers (`… work --worker NAME`) again.
  4. In the browser, enter the new token when the page asks.
- Check: a POST with the old token gets 401.
- Never put the token into git, a chat or an agent's command.

**B. Limit soricel's SSH key to `studies/`** (ADR 0019).
- In `~/.ssh/authorized_keys` on the workstation, put these options in front of soricel's key, as one line. `<STUDIES>`
  is the absolute path of `UnitcellMD/studies`, and `<ADDR>` is soricel's LAN address:

      restrict,from="<ADDR>",command="bwrap --unshare-all --die-with-parent --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib64 /lib64 --symlink usr/bin /bin --ro-bind /etc/passwd /etc/passwd --ro-bind /etc/group /etc/group --proc /proc --dev /dev --bind <STUDIES> <STUDIES> --chdir <STUDIES> /usr/lib/openssh/sftp-server -d <STUDIES>" ssh-ed25519 AAAA… (soricel's key as it is)

- Checked here without SSH (2026-11-28): the same `bwrap` arguments hide the home folder and show the studies folder
  (43 entries). `bwrap` 0.12 and `/usr/lib/openssh/sftp-server` are installed. Through `sshd` it is **not tried**.
- Then from soricel:
  1. `sftp` to the workstation; `ls` of the home folder must fail, and `ls <STUDIES>` must work;
  2. soricel's owner unmounts and mounts `studies/` again (sshfs);
  3. run the queue test job once more (`studies/2026-11-25_queue-client-test`).
- To revert: remove the options in front of the key.

**C. Tag spec 0.1.3** (ADR 0018). In the umbrella:

    git tag -a spec-v0.1.3 0e7befca83fa1d649192e6c7475ca8b528b6692f -m "UnitcellMD spec 0.1.3 (molecular pressure, nan rows; includes 0.1.2)"
    git push origin spec-v0.1.3

Then an agent makes one coordinated update, CI green, pushed with your go:
- engine `UMBRELLA_REF: spec-v0.1.3`;
- builder `pyproject.toml` and CI on `spec-v0.1.3`.

Later, approve the 0.1.4 text when it is drafted, and tag it.

**D. `gpu-cuda-mixed` on soricel** (machine config, yours or its owner's). Conditions, in order:
1. An agent commits the e37 report from the shared message folder (`result.txt`, `changes.txt`, both profiles) into
   ucmd-engine `validation/e37-precision/` as a dated report. It names the stack (native bridge c2cc427, CUDA, OpenMM
   version) and both deviations: the native bridge instead of the container, and `PY` set by hand after the NPT runs.
2. Add `"gpu-cuda-mixed"` to soricel's `[[worker]] provides`, with a `[worker.tags.gpu-cuda-mixed]` profile:
   `[backend] kind = "openmm", platform = "CUDA", precision = "mixed", device = "0"`.
3. Send soricel whole studies only: all replicas there, never pooled with HIP replicas. Its double lane (2.7 ns/day
   for 7000 atoms) is for small checks only.

**E. Papers into `../Lit`** (SC-7 Q4):
- needed: Goldberg, Herdegen, Braeuer 2026 (doi 10.1021/acs.jced.6c00429, CC BY) and Oh, Gu, Park 2018 (doi
  10.1016/j.fluid.2018.05.033);
- useful: Dougassa 2014 (doi 10.1016/j.jct.2014.07.004) and Kozlova 2008 (doi 10.1016/j.jct.2008.02.012). Kozlova is
  the DMC reference that DMC's held-out test needs.

**F. Pushes and merges** (each needs your go; §3 gives the order).
- Push umbrella `main`.
- Say "merge the analysis" (PRs #4–#6) and "merge PR #12".
- Push the builder branch `claude/a17-nacl-spce` for review.
- Push the one-line `run.sh` fix.

**G. The GPU worker's engine** (machine config).
- The worker still runs the scan's copy: binary `2ea7e826`, bridge `c2cc427`. That copy ignores trajectory
  velocities and has none of the merges of 2026-11-27.
- At a gap between studies, point `[worker.tags.gpu-hip-*]` at a release build of engine `main` and its bridge
  wrapper.
- A study that started on the old copy finishes on it: V-4's `2026-11-28_solvent-density-M1` (three jobs on
  2026-11-28) and the held NaCl study `…9aef`. Otherwise one study mixes two engines.
- Studies that need velocities (A1.5-GK and SC-2) or the newer bridge must not start before that.

## 3. Merge plan (housekeeping item 2)

- **ucmd-engine:** nothing left to merge. `main` = `origin/main` = `36b2837` contains every local and remote branch.
  - The worktrees on merged branches can go (`git worktree remove`) once their sessions end. Keep two until no job uses
    them:
    - `ucmd-engine-scan`, whose bridge wrapper the GPU profile names;
    - `ucmd-engine-pairs` (`b9f161e`, the engine of A1.7 target 1).
  - Remote branches stay; deleting them is a GitHub action and optional.
- **UnitcellMD (umbrella):**
  - `claude/issues-literature` (PR #12, CI green) holds the A1.7 design, ledger entries, T6 Amendment 6, and the
    STATUS records of the author's approvals of 2026-11-25 (A1.5-GK, A1.7). It conflicts with `main` in
    `docs/STATUS.md` and `docs/research/summary/literature.json`.
  - Merge it after V-5 has committed its `literature.json` work:
    - `literature.json`: the union of entries, with no entry changed silently;
    - STATUS: the branch's two 2026-11-25 log entries go in date order.
- **ucmd-analysis:** `main` holds only the skeleton.
  - `a1` → PR #4 (t₊ frames) → PR #5 (Green–Kubo) → PR #6 (TDF, A1.7 target 1) form one line, all CI green.
  - Fast-forward `main` to `claude/3-thermodynamic-factor` (1045065), or merge the PRs in that order. The result is
    the same.
  - The electrolyte TDF stays refused until the NaCl target passes; that is analysis behaviour, not a merge condition.
- **ucmd-builder:** `main` holds b1, b2a, b2c, b2d and the pair overrides.
  - `claude/a17-nacl-spce` (one commit, local) merges after the NaCl study (job `…9aef`) is analysed, and after a second
    reading of the Joung–Cheatham and SPC/E values against the papers in `../Lit` (ledger rule).

## 4. Gates B1a and B2a: what only the author can do

Both branches are already merged into builder `main` (2026-11-27). The gates now judge what is in `main`, so use `main`
wherever testing.md still says `git switch b1` or `b2a`.

- **B1a** ([gate-b1a.md](../gates/gate-b1a.md)):
  1. testing.md §7 on builder `main`: `pytest`, then the table (`library`, `compose`, `build`, `ucmd check`, `xyz`,
     the "break it" items);
  2. approve or change the deviations of §3, items 1–7. §4 items 1–2 are done: validator 0.1.1, and the Landesfeind SI
     with SC-8;
  3. say "Gate B1a approved", or what to change.
- **B2a** ([gate-b2a.md](../gates/gate-b2a.md)):
  1. testing.md §9 steps 1–11, with engine `main` and `ucmd-builder/start-gui.sh examples/lp57-1M.toml`;
  2. §9a steps 1–5 (results) and §9b steps 1–6 (one window);
  3. feedback on look and workflow (§6 Q1);
  4. §6 Q3 is decided here (spec 0.1.4); overrule it if you want;
  5. §6 Q4: are XYZ frames during a run enough as "live frames", or do you want live H5MD;
  6. say "Gate B2a approved", or what to change.
- Optional, still listed in STATUS: the E2 hands-on testing.md §8 and §8a.

## 5. Not delegated, so still the author's

- **Architecture invariants:** none is changed by these decisions.
- **Pushing, tagging, GitHub posts:** C, F; taking PRs #4–#6 and #12 out of draft.
- **sudo, `~/.ssh`, tokens, machine config:** A, B, D, G.
- **Stopping or cancelling queue jobs:** none is needed.
- **Physical parameters:**
  - No parameter value was chosen here.
  - SC-7 (including its ΔH_vap target) was decided by the author, not under this delegation.
  - Its sources are still unchecked: Goldberg 2026 (raw data read, paper not), Dougassa 2014 (ThermoML only), and
    Kozlova 2008 and Steele 1997 for DMC (NIST WebBook only). See `docs/research/emc-literature/sc7-sources.md`.

## 6. Task changes proposed (for the orchestrator to apply in `docs/tasks.toml`)

- **SC-2:** state `blocked` → `open`. `waits_for` = "the HIP label check, run as part of the A1.5-GK short run
  (A1.5-green-kubo.md §7 Q2); needs the GPU worker on engine main (delegated-2026-11-28.md §2 G)". The merge is done
  (engine `main`, 2026-11-27).
- **SC-7:** decided by the author 2026-11-28 (recommendations). The orchestrator records it, and the task entry is
  the orchestrator's.
