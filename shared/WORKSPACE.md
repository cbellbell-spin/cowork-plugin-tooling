# Workspace Resolution

Canonical location for plugin data across Claude Code (desktop), Cowork desktop,
Cowork web, and Cowork mobile.

Copy this file into each plugin's `references/` at build time via
`sync-shared-refs.sh`. Skills must follow it instead of hardcoding paths.

## Why

Skills previously addressed files by POSIX path (`~/Cowork/Projects/...`,
`~/Documents/pm-coach/...`). Web and mobile have no filesystem, so those
instructions fail there even though the bytes are reachable via the Drive
connector. Two plugins were writing to paths that never existed at all.

## Resolution procedure

Before reading or writing plugin data:

1. **If filesystem tools are available** (Read / Write / Glob / Edit), use:
   `~/My Drive/claude-workspace/<folder>/`
   That is Drive for Desktop's mirror root — real local files, not placeholders.
   `~/Google Drive/My Drive/claude-workspace/` resolves to the same content via
   the CloudStorage symlink; either works, prefer the first.
2. **Otherwise** — Cowork web or mobile — use the Google Drive connector.
   Scope with `search_files` using the folder id below, then
   `read_file_content` / `update_file` by file id.
3. **If neither is available**, say so and stop. Never invent a path, never
   write to a guessed location, never fall back to a local temp directory.

## Folder registry

| Folder | Drive ID | Owner plugin |
|---|---|---|
| `claude-workspace` (root) | `1zPwmT9AYyVDBmQcANjeyc1sDVHDkY08U` | — |
| `kate` | `1orwo7k-m9Q6Fys1j6wIqhfvrDOlqqAjO` | kate-career-coach |
| `training` | `1rxpLmkxjl91BoHx4k5snINkkddH2W5KM` | coach-cadence, adaptive-training-coach |
| `nhc` | `1v7YoaKL-v8S9np2aVsoTw_TRF2AF3JOo` | nhc-supply-chain (project data, not a plugin) |
| `pm-coach` | `1xz6wYzIitZ4oHzA1DlBCapNxwrBBuDys` | product-ic-coach, sdlc-system (read-only), product-dev-coach |

Example connector lookup:

```
search_files: "title contains 'source-of-truth' and parentId = '1rxpLmkxjl91BoHx4k5snINkkddH2W5KM'"
read_file_content: <returned id>
```

## Append-heavy files

Never append to a single growing file. Three surfaces writing concurrently makes
Drive fork it (`session-log (1).md`), and a skill reading the wrong fork gives
wrong answers with no error.

Write dated entries into a directory instead:

```
training/session-log/2026-09-05.md     not     training/session-log.md
```

Read by globbing or listing the directory and sorting by name.

## Prohibited

- `~/Cowork/...` and `~/Documents/...` — resolve on one machine only
- The Drive "Computers" backup root — bound to a single device; a second machine
  creates a second divergent copy
- Any absolute path outside `claude-workspace`
