#!/bin/bash
# build-plugin.sh — build a Cowork-uploadable plugin zip from a plugin repo.
#
# Usage:  build-plugin.sh [plugin-repo-dir]   (defaults to cwd)
#
# Produces <name>-<version>.zip in the repo root, with files at the ARCHIVE ROOT
# (no wrapper directory) and LF line endings — both required by Cowork.
#
# Does not validate. Run validate-cowork-plugin.py and test_plugin.py on the
# result before uploading; see README.md.

set -euo pipefail

REPO="${1:-$PWD}"
cd "$REPO"

MANIFEST=".claude-plugin/plugin.json"
[ -f "$MANIFEST" ] || { echo "Error: no $MANIFEST in $REPO" >&2; exit 1; }

NAME=$(python3 -c "import json;print(json.load(open('$MANIFEST'))['name'])")
VERSION=$(python3 -c "import json;print(json.load(open('$MANIFEST'))['version'])")
ZIP="$NAME-$VERSION.zip"

# Cowork rejects CRLF. Normalise in place before packaging.
find . -type f \( -name '*.md' -o -name '*.json' \) \
  -not -path './.git/*' -not -path './node_modules/*' \
  -exec perl -pi -e 's/\r$//' {} +

# zip dereferences symlinks (-y omitted on purpose), which means a DANGLING
# symlink is silently skipped and the archive is built without it — exit 0, no
# warning. That is exactly what happens in CI, where absolute dev symlinks into
# ~/projects/shared/ do not resolve. Fail loudly instead.
dangling=$(find . -type l ! -path './.git/*' ! -path './node_modules/*' \
  -exec test ! -e {} \; -print 2>/dev/null)
if [ -n "$dangling" ]; then
  echo "ERROR: dangling symlinks — these would be silently omitted from the zip:" >&2
  echo "$dangling" >&2
  echo "Run sync-shared-refs.sh first, or fix the link targets." >&2
  exit 1
fi

rm -f "$ZIP"

# -x patterns keep the archive clean; symlinks are dereferenced (-y omitted on
# purpose) because Cowork rejects archives containing them.
# .tooling/* is where CI checks out cowork-plugin-tooling itself — it must not
# end up inside the plugin archive.
zip -rq "$ZIP" . \
  -x '.git/*' '.github/*' 'node_modules/*' '*.zip' '*.plugin' \
     '.DS_Store' '*/.DS_Store' '.env*' '.vercel/*' '.tooling/*'

SIZE_MB=$(( $(wc -c < "$ZIP") / 1048576 ))
echo "Built $ZIP (${SIZE_MB} MB)"
[ "$SIZE_MB" -lt 50 ] || echo "WARNING: over Cowork's ~50 MB limit" >&2

if unzip -l "$ZIP" | grep -qE ' [a-zA-Z0-9_-]+/\.claude-plugin/'; then
  echo "ERROR: files are nested under a wrapper directory — Cowork will reject this" >&2
  exit 1
fi
