# cowork-plugin-tooling

Shared build and validation tooling for the Cowork plugins under
`github.com/cbellbell-spin`. Previously these scripts lived only in
`~/.claude/scripts/` on one machine — unversioned, unbacked-up, and unreachable
from CI.

## Contents

| File | Purpose |
|---|---|
| `validate-cowork-plugin.py` | Primary validator. Checks manifest, frontmatter, hooks schema, archive structure. |
| `test_plugin.py` | Secondary validator. Exercises skill/command loading. |
| `build-plugin.sh` | Builds an upload-ready zip: files at archive root, LF endings, correct exclusions. |
| `sync-shared-refs.sh` | Inlines shared reference docs into plugin `references/` dirs (Cowork zips don't preserve symlinks). |

## Required flow for any plugin change

Both validators are mandatory. They catch different failures, and Cowork
rejects uploads silently enough that skipping them costs more time than
running them.

```bash
# from the plugin repo root
~/projects/cowork-plugin-tooling/build-plugin.sh
python3 ~/projects/cowork-plugin-tooling/validate-cowork-plugin.py <name>-<version>.zip
python3 ~/projects/cowork-plugin-tooling/test_plugin.py <name>-<version>.zip
```

Bump `version` in `.claude-plugin/plugin.json` before building. Cowork keys on
version; uploading twice at the same version makes "which build is running?"
unanswerable.

## Consuming from CI

```yaml
- name: Fetch tooling
  run: gh repo clone cbellbell-spin/cowork-plugin-tooling tooling
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

- name: Build and validate
  run: |
    tooling/build-plugin.sh
    ZIP=$(ls -t *.zip | head -1)
    python3 tooling/validate-cowork-plugin.py "$ZIP"
    python3 tooling/test_plugin.py "$ZIP"
```

## Known Cowork upload failures

These pass naive inspection but cause rejection:

- **`commands/*.md` frontmatter** — only `description:` and `argument-hint:` are
  permitted. `name:`, `tools:`, `allowed-tools:` are rejected.
- **`hooks/hooks.json`** — must use the nested object schema. The flat schema
  passes casual validation and is rejected on upload.
- **Archive structure** — files at zip root, no wrapper directory, no symlinks.
- **Line endings** — LF, not CRLF.
- **Size** — roughly 50 MB ceiling.

## Related

- Plugin operations flow: `~/.claude/CLAUDE.md`, mirrored to
  `claude-workspace/PLUGIN-OPS.md` in Drive for Cowork sessions.
- Plan of record: `~/projects/docs/ai/plugin-workspace-plan.md`
