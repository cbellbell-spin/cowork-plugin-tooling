#!/bin/bash
# sync-shared-refs.sh
#
# Inline shared reference docs into each plugin's references/ directory. Cowork
# zips don't preserve symlinks, so this must run before zip-and-publish to make
# shared files appear as regular files inside the zip.
#
# Files are mapped per-plugin, not broadcast to all of them: a training coach has
# no use for a PM operating manual, and shipping it wastes 30 KB of the upload
# budget and confuses the model about scope.
#
# WARNING: this REPLACES symlinks with regular files in the target repos. Plugin
# repos keep symlinks into shared/ for local development, so running this against
# a working clone dirties it (git shows a typechange). Run it against disposable
# checkouts only — CI, or a build copy — not against ~/projects/<plugin>.
#
# build-plugin.sh does not need this locally: zip dereferences symlinks on its own.
# It is needed in CI, where the absolute dev symlinks do not resolve.
#
# Idempotent. Safe to run repeatedly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_ROOT="${1:-$(dirname "$SCRIPT_DIR")}"

# shared/ lives inside this repo so CI can reach it. Locally ~/projects/shared is
# a symlink here, which keeps the plugins' absolute dev symlinks resolving.
SHARED_DIR="$SCRIPT_DIR/shared"
[ -d "$SHARED_DIR" ] || SHARED_DIR="$PROJECTS_ROOT/shared"

if [ ! -d "$SHARED_DIR" ]; then
  echo "Error: canonical source not found at $SHARED_DIR" >&2
  exit 1
fi

# WORKSPACE.md is canonical in Drive, not in shared/. Refresh the shared/ copy
# from the mirror first so plugins never ship a stale folder-ID registry.
WORKSPACE_SRC="$HOME/My Drive/claude-workspace/WORKSPACE.md"
if [ -f "$WORKSPACE_SRC" ]; then
  cp "$WORKSPACE_SRC" "$SHARED_DIR/WORKSPACE.md"
  echo "refreshed shared/WORKSPACE.md from Drive mirror"
else
  echo "! Drive mirror unavailable — shared/WORKSPACE.md may be stale" >&2
fi

# plugin:file[,file...] — which shared docs each plugin actually needs.
# WORKSPACE.md goes to every plugin that reads or writes workspace data.
# The PM docs go only to the PM coaching plugins.
MAPPINGS=(
  "coach-cadence:WORKSPACE.md"
  "kate-career-coach:WORKSPACE.md"
  "sdlc-system:WORKSPACE.md"
  "product-dev-coach:WORKSPACE.md"
  "product-ic-coach:WORKSPACE.md,pm-operating-manual.md,working-with-me.md"
  "product-leadership-coach:pm-operating-manual.md,working-with-me.md"
)

for mapping in "${MAPPINGS[@]}"; do
  plugin="${mapping%%:*}"
  files="${mapping#*:}"

  plugin_refs="$PROJECTS_ROOT/$plugin/references"
  # Some plugins nest references under a skill (skills/<name>/references/).
  if [ ! -d "$plugin_refs" ]; then
    for nested in "$PROJECTS_ROOT/$plugin/skills/$plugin/references" \
                  "$PROJECTS_ROOT/$plugin/skills/$plugin-skill/references"; do
      if [ -d "$nested" ]; then plugin_refs="$nested"; break; fi
    done
  fi

  if [ ! -d "$plugin_refs" ]; then
    echo "skipping $plugin (no references/ found)"
    continue
  fi

  IFS=',' read -ra file_list <<< "$files"
  for file in "${file_list[@]}"; do
    src="$SHARED_DIR/$file"
    if [ ! -f "$src" ]; then
      echo "  ! $file not in shared/, skipping" >&2
      continue
    fi
    # Remove any symlink first so we replace it with a regular file rather than
    # writing through the symlink into the canonical source.
    rm -f "$plugin_refs/$file"
    cp "$src" "$plugin_refs/$file"
    echo "  + $plugin: $file"
  done
done

echo "Done."
