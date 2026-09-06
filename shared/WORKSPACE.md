# Workspace Resolution

Canonical location for plugin data across Claude Code (desktop), Cowork desktop,
Cowork web, and Cowork mobile.

Copy this file into each plugin's `references/` at build time via
`sync-shared-refs.sh`. Skills must follow it instead of hardcoding paths.

## Why

Skills used to hardcode POSIX paths (`~/Cowork/Projects/...`,
`~/Documents/pm-coach/...`) that resolve on exactly one Mac. Two of them pointed
at directories that never existed anywhere.

A hardcoded path is wrong even where a filesystem exists, because it competes
with the folder the session actually connected. That conflict is not theoretical:
on 2026-09-05 a mobile session and the local copy diverged, and seven coaching
decisions were pruned from one copy while today's two entries existed only in the
other. Deferring to the session folder, and keeping that folder inside the Drive
mirror, is what prevents a repeat.

## Resolution procedure

**The folder the session gives you always wins.** A Cowork session names its
connected folder; that overrides anything written here. Only fall through when
there is no session folder.

1. **Session-assigned folder** — use it. Do not second-guess it against this file.
2. **No session folder, filesystem available** — `~/My Drive/claude-workspace/<folder>/`
   (Drive for Desktop's mirror root; real local files, not placeholders).
3. **No filesystem** — Google Drive connector: `search_files` scoped by the folder
   id below, then `read_file_content` / `update_file` by file id.
4. **None of these resolve** — say so and stop. Never invent a path, never write to
   a guessed location, never create a second copy somewhere reachable.

### Why the order matters

A Cowork session on web or mobile reaches local files only while the desktop app
is open on that Mac *and* the session was started on desktop. If the Mac sleeps,
the session keeps running but local access disappears — mid-session.

That is why the connected folder should itself live inside the Drive mirror. Then
route 1 and route 3 address the same bytes, and losing the bridge degrades to the
connector instead of silently forking the data into two locations. A connected
folder outside the mirror is the failure mode: it works until the Mac sleeps, then
writes land somewhere the other surfaces never see.

Applies to plugins that must work away from the desktop — coach-cadence first,
kate-career-coach second. Desktop-only workflows can rely on route 1 alone.

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
