# 0018 — Spec releases: when a version is tagged, what goes into it, what CI pins

- **Status:** accepted 2026-11-28 by agent decisions, under the author's delegation of that day
  ("let agents make the decision"). To be reviewed by the author, who tags every release.
- **Context:**
  - **Tags:** `spec-v0.1.0` (Gate 0) and `spec-v0.1.2` (2026-11-25, approved by the author). The
    latter contains 0.1.1, which was never tagged on its own.
  - **0.1.3** (molecular pressure column, `nan` in pressure rows) was approved on 2026-11-25. It is
    implemented in engine `main` and validator 0.1.3, and is still untagged.
  - **Pins:** the engine CI reads the umbrella at commit `0e7befc`, which holds 0.1.3 and the
    oracle references. The builder pins `spec-v0.1.2`.
  - **Undocumented behaviour:** the profile's `[backend]`, the exit codes of a graceful stop, the
    restart records and the XYZ trajectory are engine behaviour the spec does not describe
    (E3.7 Q3, gate-b2a.md §6 Q3).
  - **Stale text:** the CHANGELOG still calls 0.1.1 and 0.1.2 "not yet tagged".
- **Decision:**
  1. **When to tag:** a version is tagged once the author has approved its content and at least
     one component implements it with tests. The tag is `spec-vX.Y.Z` on a pushed umbrella
     commit. Tagging is the author's action.
  2. **One name, one content.**
     - A tagged version never changes.
     - An untagged version may still change until a component pins it (CI, a dependency, a
       validator release). After that, new content goes into the next version.
     - So 0.1.3 is closed.
  3. **0.1.1 gets no tag of its own.** It is contained in `spec-v0.1.2`, and every 0.1.1 file is
     valid under 0.1.2. The 0.1.4 CHANGELOG says so.
  4. **Tag `spec-v0.1.3` at `0e7befc`.** Its `spec/` equals umbrella `main` of 2026-11-28, and it is
     the engine CI's present pin. In one coordinated update afterwards:
     - engine `UMBRELLA_REF` names the tag (same commit, so CI reads the same bytes);
     - the builder's validator dependency and CI move from `spec-v0.1.2` to `spec-v0.1.3`.
  5. **0.1.4 documents existing behaviour only**, with no new keys or semantics: the four items
     listed in [E3.7.md](../design/E3.7.md) Q3, plus the CHANGELOG correction.
     - An agent drafts it on a branch and checks it against the code.
     - The author approves it and tags it.
  6. **CI pins:**
     - A component's CI pins a spec tag.
     - It may pin an untagged, pushed umbrella commit only when it needs fixtures or oracle
       references before the next tag. That move goes in the same coordinated update as the
       tests that need it, and the pin returns to a tag once one exists.
     - A pin never names an unpushed commit.
- **Consequences:**
  - A version string in any output names exactly one text.
  - Each release costs one tag and one pin update per component.
  - The next new content, if V-1 or SC-3 need any, goes into 0.1.5 or later, even if 0.1.4 is
    not tagged yet.
  - Reversible: tags not yet made can be skipped, and the documentation items can be held for
    0.2.
