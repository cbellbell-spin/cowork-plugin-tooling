#!/bin/bash
# scripts/sync-shared-refs.sh
#
# Inline shared reference docs from the canonical source (shared/) into each
# plugin's references/ directory. Cowork zips don't preserve symlinks, so this
# must run before zip-and-publish to make the shared files appear as regular
# files inside the zip.
#
# Idempotent. Safe to run repeatedly. After this script runs, the plugin's
# references/ files are regular files. If you want symlinks back for dev,
# re-run the symlink setup (see README in scripts/).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_ROOT="$(dirname "$SCRIPT_DIR")"
SHARED_DIR="$PROJECTS_ROOT/shared"

if [ ! -d "$SHARED_DIR" ]; then
  echo "Error: canonical source not found at $SHARED_DIR" >&2
  exit 1
fi

# The shared files (relative to SHARED_DIR).
SHARED_FILES=(
  "pm-operating-manual.md"
  "working-with-me.md"
)

# Plugins that share the canonical reference docs. Add entries as new plugins
# adopt the shared references. The product-leadership-coach entry is included
# as a no-op until its local source appears; the script will skip missing dirs.
PLUGINS=(
  "product-ic-coach"
  "product-leadership-coach"
)

for plugin in "${PLUGINS[@]}"; do
  plugin_refs="$PROJECTS_ROOT/$plugin/references"
  # Some plugins nest references under a skill (e.g. skills/<name>/references/).
  # If the top-level references/ doesn't exist, try the umbrella-skill path.
  if [ ! -d "$plugin_refs" ]; then
    for nested in "$PROJECTS_ROOT/$plugin/skills/$plugin/references" "$PROJECTS_ROOT/$plugin/skills/$plugin-skill/references"; do
      if [ -d "$nested" ]; then
        plugin_refs="$nested"
        break
      fi
    done
  fi

  if [ ! -d "$plugin_refs" ]; then
    echo "Skipping $plugin (no references/ found)"
    continue
  fi

  for file in "${SHARED_FILES[@]}"; do
    src="$SHARED_DIR/$file"
    dst="$plugin_refs/$file"
    if [ ! -f "$src" ]; then
      echo "  ! $file not in shared/, skipping"
      continue
    fi
    # Remove any symlink first so we replace it with a regular file, not write
    # through the symlink into the canonical source.
    rm -f "$dst"
    cp "$src" "$dst"
    echo "  + $plugin: $file"
  done
done

echo "Done."
