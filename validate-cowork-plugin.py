#!/usr/bin/env python3
"""
Cowork Plugin Validator
=======================
Validates a Cowork plugin archive against all known client-side and structural
validation rules before attempting to upload via the Cowork desktop app.

Usage:
    python3 ~/.claude/scripts/validate-cowork-plugin.py <path-to-plugin.zip>

What it checks (sourced from app.asar index.js client-side validation + docs):
  - File extension must be .zip (Cowork UI only accepts .zip)
  - File size within limit (~50MB)
  - .claude-plugin/plugin.json exists and is valid JSON
  - plugin.json: name is required and must be kebab-case
  - plugin.json: homepage, repository, license recognized as valid
  - CRLF line endings (cause YAML parsing failures)
  - Command frontmatter: only 'description:' and optionally 'argument-hint:' allowed
    (name:, tools:, allowed-tools: all cause upload failure)
  - Skill SKILL.md: 'name:' is ALLOWED, but tools: and allowed-tools: are forbidden
  - ZIP is flat (files at root, not wrapped in a subdirectory)
  - No symlinks (app skips symlinked manifests)
  - agents/: if directory exists, validate .md files present
  - hooks/hooks.json: must use nested object schema (event -> matcher group -> inner
    "hooks" array), not the old array schema or a flat schema with type/command on
    the matcher group; SessionStart/Setup only support type "command"/"mcp_tool"
  - .mcp.json: if present, validate mcpServers structure
  - monitors/monitors.json: if present, validate monitor entries
  - settings.json: if present, validate supported keys
"""

import sys
import os
import re
import zipfile
import json

# ── constants ──────────────────────────────────────────────────────────────────
MAX_BYTES = 50 * 1024 * 1024          # 50 MB
KEBAB_RE  = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

# Fields known to be valid in command frontmatter
COMMAND_ALLOWED_FIELDS = {"description", "argument-hint"}
# Fields known to CAUSE upload failure in command frontmatter
COMMAND_FORBIDDEN_FIELDS = {"name", "tools", "allowed-tools"}

# Fields valid in skill SKILL.md frontmatter
SKILL_ALLOWED_FIELDS = {"name", "description"}
SKILL_FORBIDDEN_FIELDS = {"tools", "allowed-tools"}

# Valid hook event names
VALID_HOOK_EVENTS = {
    "SessionStart", "Setup", "UserPromptSubmit", "PreToolUse", "PermissionRequest",
    "PermissionDenied", "PostToolUse", "PostToolUseFailure", "Notification",
    "SubagentStart", "SubagentStop", "TaskCreated", "TaskCompleted",
    "Stop", "StopFailure", "TeammateIdle", "InstructionsLoaded",
    "ConfigChange", "CwdChanged", "FileChanged", "WorktreeCreate",
    "WorktreeRemove", "PreCompact", "PostCompact", "Elicitation",
    "ElicitationResult", "SessionEnd"
}
VALID_HOOK_TYPES = {"command", "http", "prompt", "agent", "mcp_tool"}

# Events restricted to a subset of hook types (per official docs)
RESTRICTED_HOOK_TYPE_EVENTS = {
    "SessionStart": {"command", "mcp_tool"},
    "Setup": {"command", "mcp_tool"},
}

# Valid plugin.json fields (unknown ones trigger warnings)
PLUGIN_KNOWN_FIELDS = {
    "name", "version", "description", "author", "keywords",
    "commands", "skills", "agents", "hooks", "mcpServers",
    "oauth", "confirm", "homepage", "repository", "license"
}

# Valid settings.json keys
SETTINGS_VALID_KEYS = {"agent", "subagentStatusLine"}

PASS  = "\033[32m✓\033[0m"
FAIL  = "\033[31m✗\033[0m"
WARN  = "\033[33m⚠\033[0m"

errors   = []
warnings = []
passed   = []

def ok(msg):
    passed.append(msg)
    print(f"  {PASS} {msg}")

def fail(msg):
    errors.append(msg)
    print(f"  {FAIL} {msg}")

def warn(msg):
    warnings.append(msg)
    print(f"  {WARN} {msg}")

def section(title):
    print(f"\n{title}")
    print("─" * len(title))

# ── helpers ────────────────────────────────────────────────────────────────────

def parse_frontmatter(text):
    """Return dict of frontmatter fields, or None if no frontmatter."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip()
    fields = {}
    for line in block.splitlines():
        if line.startswith("  ") or line.startswith("\t"):
            continue  # skip list items / indented values
        if ":" in line:
            key = line.split(":", 1)[0].strip()
            if key:
                fields[key] = True
    return fields

def has_crlf(data: bytes) -> bool:
    return b"\r\n" in data


def validate_hooks_schema(hooks_json, label="hooks/hooks.json"):
    """Validate hooks.json against the documented object schema."""
    errors_local = []

    if not isinstance(hooks_json, dict):
        return [f"{label}: must be a JSON object (not array)"]

    if "hooks" not in hooks_json:
        return [f"{label}: missing 'hooks' key"]

    hooks = hooks_json["hooks"]

    if isinstance(hooks, list):
        return [
            f"{label}: hooks is an array — this is the old deprecated schema. "
            f"Cowork expects hooks as an object keyed by event name, e.g. "
            f'{{"hooks":{{"SessionStart":[{{"hooks":[{{"type":"command","command":"..."}}]}}]}}}}'
        ]

    if not isinstance(hooks, dict):
        return [f"{label}: hooks must be a JSON object keyed by event name"]

    for event_name, matcher_groups in hooks.items():
        if event_name not in VALID_HOOK_EVENTS:
            errors_local.append(
                f"{label}: unknown hook event '{event_name}' — "
                f"valid: {', '.join(sorted(VALID_HOOK_EVENTS))}"
            )

        if not isinstance(matcher_groups, list):
            errors_local.append(f"{label}: hook handlers for '{event_name}' must be a list")
            continue

        for gi, group in enumerate(matcher_groups):
            if not isinstance(group, dict):
                errors_local.append(f"{label}: hook group [{gi}] for '{event_name}' must be an object")
                continue

            flat_fields = {"type", "command", "prompt", "url"} & group.keys()
            if flat_fields:
                errors_local.append(
                    f"{label}: hook group [{gi}] for '{event_name}' has {sorted(flat_fields)} "
                    f"directly on it — this is the old/incorrect flat schema. Handler fields "
                    f"(type, command, prompt, url) must be nested inside an inner 'hooks' array: "
                    f'{{"hooks":[{{"type":"...","command":"..."}}]}}'
                )
                continue

            if "hooks" not in group:
                errors_local.append(f"{label}: hook group [{gi}] for '{event_name}' missing required inner 'hooks' array")
                continue

            inner_hooks = group["hooks"]
            if not isinstance(inner_hooks, list):
                errors_local.append(f"{label}: hook group [{gi}] for '{event_name}' inner 'hooks' must be a list")
                continue

            for i, handler in enumerate(inner_hooks):
                if not isinstance(handler, dict):
                    errors_local.append(f"{label}: hook[{gi}][{i}] for '{event_name}' must be an object")
                    continue

                if "type" not in handler:
                    errors_local.append(f"{label}: hook[{gi}][{i}] for '{event_name}' missing required 'type' field")
                elif handler["type"] not in VALID_HOOK_TYPES:
                    errors_local.append(
                        f"{label}: hook[{gi}][{i}] for '{event_name}' has invalid type "
                        f"'{handler['type']}' — must be one of {VALID_HOOK_TYPES}"
                    )

                htype = handler.get("type")

                restricted = RESTRICTED_HOOK_TYPE_EVENTS.get(event_name)
                if restricted is not None and htype is not None and htype not in restricted:
                    errors_local.append(
                        f"{label}: hook[{gi}][{i}] ({event_name}) has type '{htype}' — "
                        f"'{event_name}' only supports {sorted(restricted)}"
                    )

                if htype == "command":
                    if "command" not in handler:
                        errors_local.append(f"{label}: hook[{gi}][{i}] ({event_name}, type=command) missing required 'command' field")
                elif htype == "http":
                    if "url" not in handler:
                        errors_local.append(f"{label}: hook[{gi}][{i}] ({event_name}, type=http) missing required 'url' field")
                elif htype == "prompt":
                    if "prompt" not in handler:
                        errors_local.append(f"{label}: hook[{gi}][{i}] ({event_name}, type=prompt) missing required 'prompt' field")
                elif htype == "agent":
                    if "prompt" not in handler:
                        errors_local.append(f"{label}: hook[{gi}][{i}] ({event_name}, type=agent) missing required 'prompt' field")

    return errors_local


def validate_mcp_json(mcp_json, label=".mcp.json"):
    """Validate .mcp.json structure (mcpServers object with stdio or http entries)."""
    errors_local = []

    if not isinstance(mcp_json, dict):
        return [f"{label}: must be a JSON object"]

    if "mcpServers" not in mcp_json:
        return [f"{label}: missing 'mcpServers' key"]

    servers = mcp_json["mcpServers"]
    if not isinstance(servers, dict):
        return [f"{label}: 'mcpServers' must be an object"]

    for server_name, server_config in servers.items():
        if not isinstance(server_config, dict):
            errors_local.append(f"{label}: server '{server_name}' must be an object")
            continue

        if "type" not in server_config:
            errors_local.append(f"{label}: server '{server_name}' missing required 'type' field")
            continue

        server_type = server_config.get("type")
        if server_type == "stdio":
            if "command" not in server_config:
                errors_local.append(f"{label}: server '{server_name}' (type=stdio) missing required 'command' field")
            if "args" not in server_config:
                errors_local.append(f"{label}: server '{server_name}' (type=stdio) missing required 'args' field")
        elif server_type == "http":
            if "url" not in server_config:
                errors_local.append(f"{label}: server '{server_name}' (type=http) missing required 'url' field")
        else:
            errors_local.append(
                f"{label}: server '{server_name}' has unknown type '{server_type}' "
                f"(expected 'stdio' or 'http')"
            )

    return errors_local


def validate_monitors_json(monitors_json, label="monitors/monitors.json"):
    """Validate monitors/monitors.json structure (array of monitor entries)."""
    errors_local = []

    if not isinstance(monitors_json, list):
        return [f"{label}: must be a JSON array of monitor entries"]

    for i, entry in enumerate(monitors_json):
        if not isinstance(entry, dict):
            errors_local.append(f"{label}[{i}]: entry must be an object")
            continue

        for required in ("name", "command", "description"):
            if required not in entry:
                errors_local.append(f"{label}[{i}]: entry missing required '{required}' field")

    return errors_local


def validate_settings_json(settings_json, label="settings.json"):
    """Validate settings.json structure (object with agent/subagentStatusLine keys only)."""
    errors_local = []

    if not isinstance(settings_json, dict):
        return [f"{label}: must be a JSON object"]

    unknown = set(settings_json.keys()) - SETTINGS_VALID_KEYS
    if unknown:
        errors_local.append(
            f"{label}: contains unsupported keys: {unknown} "
            f"(only 'agent' and 'subagentStatusLine' are supported)"
        )

    return errors_local


# ── main validation ────────────────────────────────────────────────────────────

def validate(path: str):
    print(f"\nCowork Plugin Validator")
    print(f"=======================")
    print(f"File: {path}\n")

    # ── 1. File-level checks ───────────────────────────────────────────────────
    section("1. File checks")

    if not os.path.exists(path):
        fail(f"File not found: {path}")
        return

    basename = os.path.basename(path)
    ext = os.path.splitext(basename)[1].lower()
    if ext == ".zip":
        ok(f"Extension is .zip (required by Cowork upload UI)")
    elif ext == ".plugin":
        fail("Extension is .plugin — Cowork upload UI only accepts .zip files. Rename to .zip before uploading.")
    else:
        fail(f"Extension '{ext}' not accepted. Must be .zip.")

    size = os.path.getsize(path)
    if size > MAX_BYTES:
        fail(f"File size {size/1024/1024:.1f} MB exceeds {MAX_BYTES/1024/1024:.0f} MB limit.")
    else:
        ok(f"File size {size/1024:.1f} KB is within limit.")

    if not zipfile.is_zipfile(path):
        fail("File is not a valid ZIP archive.")
        return
    else:
        ok("Valid ZIP archive.")

    # ── 2. Archive structure ───────────────────────────────────────────────────
    section("2. Archive structure")

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()

        # Check for top-level wrapping directory
        top_dirs = set()
        for n in names:
            parts = n.split("/")
            if parts[0]:
                top_dirs.add(parts[0])
        non_meta = {d for d in top_dirs if not d.startswith(".")}
        expected_top = {"commands", "skills", "agents", "hooks", "README.md", ".claude-plugin"}
        has_wrapper = (
            len(non_meta) == 1
            and list(non_meta)[0] not in expected_top
            and not any(n.startswith(".claude-plugin/") for n in names)
        )
        if has_wrapper:
            wrapper = list(non_meta)[0]
            fail(f"Archive appears to be wrapped in a subdirectory '{wrapper}/'. "
                 f"Files must be at the archive root.")
        else:
            ok("Files are at archive root (no wrapper directory).")

        # Check for .claude-plugin/plugin.json
        if ".claude-plugin/plugin.json" in names:
            ok(".claude-plugin/plugin.json exists.")
        else:
            fail(".claude-plugin/plugin.json is missing. This is required.")

        # Check for symlinks (app skips them)
        symlinks = [n for n in names if zf.getinfo(n).external_attr >> 16 == 0o120777]
        if symlinks:
            warn(f"Archive contains symlinks (app will skip them): {symlinks}")
        else:
            ok("No symlinks.")

        # ── 3. plugin.json validation ──────────────────────────────────────────
        section("3. plugin.json")

        if ".claude-plugin/plugin.json" in names:
            raw = zf.read(".claude-plugin/plugin.json")

            if has_crlf(raw):
                fail("plugin.json has CRLF line endings. Convert to LF.")
            else:
                ok("plugin.json uses LF line endings.")

            try:
                manifest = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                fail(f"plugin.json is not valid JSON: {e}")
                manifest = None

            if manifest is not None:
                if not isinstance(manifest, dict):
                    fail("plugin.json must be a JSON object.")
                else:
                    name = manifest.get("name")
                    if not name:
                        fail("plugin.json: 'name' field is required.")
                    elif not isinstance(name, str) or not name.strip():
                        fail("plugin.json: 'name' must be a non-empty string.")
                    elif not KEBAB_RE.match(name):
                        fail(f"plugin.json: name '{name}' must be kebab-case "
                             f"(lowercase letters, numbers, hyphens only).")
                    else:
                        ok(f"plugin.json name '{name}' is valid kebab-case.")

                    if "version" in manifest:
                        ok(f"plugin.json version: {manifest['version']}")
                    else:
                        warn("plugin.json: no 'version' field (will default to '0.0.0').")

                    if "description" in manifest:
                        ok("plugin.json has description.")
                    else:
                        warn("plugin.json: no 'description' field.")

                    if "author" in manifest:
                        ok("plugin.json has author.")

                    # Check for unexpected fields that could cause security errors
                    known_fields = PLUGIN_KNOWN_FIELDS
                    unknown = set(manifest.keys()) - known_fields
                    if unknown:
                        warn(f"plugin.json has unknown fields: {unknown} "
                             f"(may be ignored or cause issues).")

        # ── 4. Commands ────────────────────────────────────────────────────────
        section("4. Commands")

        command_files = [n for n in names if n.startswith("commands/") and n.endswith(".md")]
        if not command_files:
            warn("No command files found in commands/.")
        else:
            ok(f"Found {len(command_files)} command file(s): "
               f"{[os.path.basename(n) for n in command_files]}")

        for cmd_path in command_files:
            raw = zf.read(cmd_path)
            label = os.path.basename(cmd_path)

            if has_crlf(raw):
                fail(f"{label}: CRLF line endings detected. Convert to LF.")

            text = raw.decode("utf-8", errors="replace")
            fields = parse_frontmatter(text)

            if fields is None:
                warn(f"{label}: no YAML frontmatter found (--- block).")
                continue

            # Check for forbidden fields
            for bad in COMMAND_FORBIDDEN_FIELDS:
                if bad in fields:
                    fail(f"{label}: frontmatter has forbidden field '{bad}:' — "
                         f"only 'description:' (and optionally 'argument-hint:') are accepted.")

            # Check description exists
            if "description" not in fields:
                fail(f"{label}: frontmatter missing required 'description:' field.")
            else:
                ok(f"{label}: frontmatter OK (description present, no forbidden fields).")

            # Warn about unknown fields
            unknown_cmd = set(fields.keys()) - COMMAND_ALLOWED_FIELDS - COMMAND_FORBIDDEN_FIELDS
            if unknown_cmd:
                warn(f"{label}: unrecognized frontmatter fields: {unknown_cmd}")

        # ── 4a. Agents ────────────────────────────────────────────────────────────
        section("4a. Agents")

        agent_dirs = set()
        for n in names:
            if n.startswith("agents/") and n.endswith(".md") and "/" in n[len("agents/"):]:
                continue
            if n.startswith("agents/") and "/" in n[len("agents/"):]:
                agent_name = n[len("agents/"):].split("/")[0]
                if agent_name:
                    agent_dirs.add(agent_name)

        agent_md_files = [n for n in names if n.startswith("agents/") and n.endswith(".md")]

        if not agent_dirs and not agent_md_files:
            note = "No agents/ directory found (optional — OK)"
        else:
            if agent_md_files:
                ok(f"Found {len(agent_md_files)} agent definition file(s): {[os.path.basename(n) for n in agent_md_files]}")
            for agent in sorted(agent_dirs):
                agent_md_path = f"agents/{agent}.md"
                if agent_md_path not in names:
                    fail(f"agents/{agent}.md is missing (agent definition requires .md file)")

        # ── 5. Skills ──────────────────────────────────────────────────────────
        section("5. Skills")

        skill_dirs = set()
        for n in names:
            if n.startswith("skills/") and "/" in n[len("skills/"):]:
                skill_name = n[len("skills/"):].split("/")[0]
                if skill_name:
                    skill_dirs.add(skill_name)

        if not skill_dirs:
            warn("No skill directories found under skills/.")
        else:
            ok(f"Found {len(skill_dirs)} skill(s): {sorted(skill_dirs)}")

        for skill in sorted(skill_dirs):
            skill_md_path = f"skills/{skill}/SKILL.md"
            if skill_md_path not in names:
                fail(f"skills/{skill}/SKILL.md is missing.")
                continue

            raw = zf.read(skill_md_path)
            label = f"{skill}/SKILL.md"

            if has_crlf(raw):
                fail(f"{label}: CRLF line endings. Convert to LF.")

            text = raw.decode("utf-8", errors="replace")
            fields = parse_frontmatter(text)

            if fields is None:
                warn(f"{label}: no YAML frontmatter found.")
            else:
                if "description" not in fields:
                    warn(f"{label}: no 'description:' in frontmatter.")

                # Skills: name: is ALLOWED, but tools: and allowed-tools: are forbidden
                for bad in SKILL_FORBIDDEN_FIELDS:
                    if bad in fields:
                        fail(f"{label}: forbidden frontmatter field '{bad}:' — "
                             f"skills allow 'name:' and 'description:' but not 'tools:' or 'allowed-tools:'")

                unknown_skill = set(fields.keys()) - SKILL_ALLOWED_FIELDS - SKILL_FORBIDDEN_FIELDS
                if unknown_skill:
                    warn(f"{label}: unrecognized frontmatter fields: {unknown_skill}")

                ok(f"{label}: frontmatter OK.")

        # ── 6. hooks/hooks.json ──────────────────────────────────────────────────
        section("6. hooks/hooks.json")

        if "hooks/hooks.json" in names:
            raw = zf.read("hooks/hooks.json")
            if has_crlf(raw):
                fail("hooks/hooks.json: CRLF line endings. Convert to LF.")
            try:
                hooks_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                fail(f"hooks/hooks.json: not valid JSON: {e}")
            else:
                hook_errors = validate_hooks_schema(hooks_data)
                for e in hook_errors:
                    fail(e)
                if not hook_errors:
                    ok("hooks/hooks.json: valid object schema.")
        else:
            note = "hooks/hooks.json not present (optional)."

        # ── 7. .mcp.json ────────────────────────────────────────────────────────
        section("7. .mcp.json")

        if ".mcp.json" in names:
            raw = zf.read(".mcp.json")
            if has_crlf(raw):
                fail(".mcp.json: CRLF line endings. Convert to LF.")
            try:
                mcp_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                fail(f".mcp.json: not valid JSON: {e}")
            else:
                mcp_errors = validate_mcp_json(mcp_data)
                for e in mcp_errors:
                    fail(e)
                if not mcp_errors:
                    ok(".mcp.json: valid mcpServers structure.")
        else:
            note = ".mcp.json not present (optional)."

        # ── 8. monitors/monitors.json ───────────────────────────────────────────
        section("8. monitors/monitors.json")

        if "monitors/monitors.json" in names:
            raw = zf.read("monitors/monitors.json")
            if has_crlf(raw):
                fail("monitors/monitors.json: CRLF line endings. Convert to LF.")
            try:
                monitors_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                fail(f"monitors/monitors.json: not valid JSON: {e}")
            else:
                monitor_errors = validate_monitors_json(monitors_data)
                for e in monitor_errors:
                    fail(e)
                if not monitor_errors:
                    ok("monitors/monitors.json: valid monitors array.")
        else:
            note = "monitors/monitors.json not present (optional)."

        # ── 9. settings.json ────────────────────────────────────────────────────
        section("9. settings.json")

        if "settings.json" in names:
            raw = zf.read("settings.json")
            if has_crlf(raw):
                fail("settings.json: CRLF line endings. Convert to LF.")
            try:
                settings_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                fail(f"settings.json: not valid JSON: {e}")
            else:
                settings_errors = validate_settings_json(settings_data)
                for e in settings_errors:
                    fail(e)
                if not settings_errors:
                    ok("settings.json: valid settings object.")
        else:
            note = "settings.json not present (optional)."

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*40}")
    print(f"SUMMARY")
    print(f"{'='*40}")
    print(f"  Passed:   {len(passed)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Errors:   {len(errors)}")
    print()

    if errors:
        print(f"\033[31mFAILED — fix {len(errors)} error(s) before uploading:\033[0m")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    elif warnings:
        print(f"\033[33mPASSED with warnings — upload should work but review warnings above.\033[0m")
        sys.exit(0)
    else:
        print(f"\033[32mPASSED — plugin looks good to upload.\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <path-to-plugin.zip>")
        sys.exit(1)
    validate(sys.argv[1])
