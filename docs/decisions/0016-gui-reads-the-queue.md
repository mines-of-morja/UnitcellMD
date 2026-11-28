# 0016 — The GUI reads the queue's state over HTTP, read-only

- **Status:** accepted by the author on 2026-11-25 ("Read-only page", docs/design/B2d.md §5).
- **Context:** the compute queue (`tools/queue`) shows its state only in the browser. Components
  talk to each other through spec'd files and the provider protocol (invariant 2); the queue is
  neither.
- **Decision:**
  1. The GUI may fetch `GET <url>/api/state` (schema 1, docs/design/queue.md §3) and show it. It
     sends no other request, no token and no data.
  2. The address is `queue_url` in the GUI's per-user settings (`~/.config/ucmd/gui.json`), never in a
     package or a run (invariant 11), and not in the machine profile, whose keys the spec defines.
     Without it the GUI fetches nothing.
  3. The GUI imports nothing from `tools/queue` and works without a server. Another schema is
     refused with a message, never guessed.
  4. What comes from the server is text to show. A study or run name is used as a path only inside
     the chosen workspace's `studies/` folder.
- **Consequences:** a change of the state document's schema number has to be followed in the GUI.
  Submitting or cancelling from the GUI would need a new decision.
