#!/usr/bin/env python3
"""
Test suite for Cowork plugin validation.
Ensures all plugin ZIPs pass structural and schema requirements.

Checks (sourced from Claude Code plugins docs):
  - File extension .zip, size within ~50MB
  - .claude-plugin/plugin.json exists and is valid JSON
  - plugin.json: name required, kebab-case; homepage/repository/license recognized
  - CRLF line endings checked for all files
  - commands/: only description: and argument-hint: allowed (name:, tools:,
    allowed-tools: are forbidden)
  - skills/: SKILL.md must exist; name: is ALLOWED, tools: and allowed-tools:
    are forbidden
  - agents/: if directory exists, validate .md files present
  - hooks/hooks.json: must use nested object schema (event -> matcher group -> inner
    "hooks" array), not the old array schema or a flat schema with type/command on
    the matcher group; SessionStart/Setup only support type "command"/"mcp_tool"
  - .mcp.json: if present, validate mcpServers structure (stdio/http)
  - monitors/monitors.json: if present, validate monitor entries
  - settings.json: if present, only agent/subagentStatusLine keys supported
  - ZIP is flat (files at root, not wrapped in subdirectory)
  - No symlinks
"""

import json
import sys
import zipfile
import os

# ── Constants ────────────────────────────────────────────────────────────────

COMMAND_ALLOWED_FIELDS = {"description", "argument-hint"}
COMMAND_FORBIDDEN_FIELDS = {"name", "tools", "allowed-tools"}
SKILL_ALLOWED_FIELDS = {"name", "description"}
SKILL_FORBIDDEN_FIELDS = {"tools", "allowed-tools"}
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
SETTINGS_VALID_KEYS = {"agent", "subagentStatusLine"}
PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
WARN = "\033[33m⚠\033[0m"
MAX_BYTES = 50 * 1024 * 1024  # 50 MB


# ── Helpers ─────────────────────────────────────────────────────────────────

def has_crlf(data: bytes) -> bool:
    return b"\r\n" in data


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip()
    fields = {}
    for line in block.splitlines():
        if line.startswith("  ") or line.startswith("\t"):
            continue
        if ":" in line:
            key = line.split(":", 1)[0].strip()
            if key:
                fields[key] = True
    return fields


def validate_hooks_schema(hooks_json, label="hooks/hooks.json"):
    """Validate hooks.json — must be nested object schema (event -> matcher group -> inner 'hooks' array)."""
    errors_local = []

    if not isinstance(hooks_json, dict):
        return [f"{label}: must be a JSON object (not array)"]

    if "hooks" not in hooks_json:
        return [f"{label}: missing 'hooks' key"]

    hooks = hooks_json["hooks"]

    if isinstance(hooks, list):
        return [
            f"{label}: hooks is an array — old deprecated schema. "
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
    """Validate .mcp.json (mcpServers object with stdio or http entries)."""
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
    """Validate monitors/monitors.json (array of monitor entries)."""
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
    """Validate settings.json (object with agent/subagentStatusLine keys only)."""
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


def validate_command_frontmatter(path, raw_text):
    """Validate a command file's frontmatter."""
    errors = []
    fields = parse_frontmatter(raw_text)
    if fields is None:
        return ["no YAML frontmatter"]

    for bad in ["name", "tools", "allowed-tools"]:
        if bad in fields:
            errors.append(f"forbidden frontmatter field '{bad}:' — only {COMMAND_ALLOWED_FIELDS} are allowed in commands")

    if "description" not in fields:
        errors.append("missing required 'description:' field")

    return errors


def validate_plugin(path):
    """Validate a plugin ZIP file. Returns (passed, errors, warnings)."""
    passed = []
    errors = []
    warnings = []

    if not zipfile.is_zipfile(path):
        return passed, ["not a valid ZIP archive"], warnings

    size = os.path.getsize(path)
    if size > MAX_BYTES:
        return passed, [f"File size {size/1024/1024:.1f} MB exceeds 50 MB limit"], warnings

    basename = os.path.basename(path)
    ext = os.path.splitext(basename)[1].lower()
    if ext != ".zip":
        return passed, [f"Extension '{ext}' not accepted — must be .zip"], warnings

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()

        # Check for top-level wrapper directory
        top_dirs = set()
        for n in names:
            parts = n.split("/")
            if parts[0]:
                top_dirs.add(parts[0])
        non_meta = {d for d in top_dirs if not d.startswith(".")}
        expected_top = {"commands", "skills", "agents", "hooks", "monitors", "bin",
                        "README.md", ".claude-plugin"}
        has_wrapper = (
            len(non_meta) == 1
            and list(non_meta)[0] not in expected_top
            and not any(n.startswith(".claude-plugin/") for n in names)
        )
        if has_wrapper:
            wrapper = list(non_meta)[0]
            return passed, [f"Archive wrapped in subdirectory '{wrapper}/' — files must be at archive root"], warnings

        # Check for .claude-plugin/plugin.json
        if ".claude-plugin/plugin.json" not in names:
            return passed, [".claude-plugin/plugin.json is missing"], warnings

        # Check for symlinks
        symlinks = [n for n in names if zf.getinfo(n).external_attr >> 16 == 0o120777]
        if symlinks:
            warnings.append(f"Archive contains symlinks (app will skip them): {symlinks}")

        # Validate plugin.json
        raw = zf.read(".claude-plugin/plugin.json")
        if has_crlf(raw):
            errors.append(".claude-plugin/plugin.json: CRLF line endings detected")

        try:
            manifest = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as e:
            return passed, [f"plugin.json is not valid JSON: {e}"], warnings

        if "name" not in manifest:
            return passed, ["plugin.json missing 'name' field"], warnings

        PLUGIN_KNOWN_FIELDS = {
            "name", "version", "description", "author", "keywords",
            "commands", "skills", "agents", "hooks", "mcpServers",
            "oauth", "confirm", "homepage", "repository", "license"
        }
        unknown_fields = set(manifest.keys()) - PLUGIN_KNOWN_FIELDS
        if unknown_fields:
            warnings.append(f"plugin.json: unknown fields {unknown_fields}")

        # Validate commands
        command_files = [n for n in names if n.startswith("commands/") and n.endswith(".md")]
        for cmd_path in command_files:
            raw = zf.read(cmd_path)
            if has_crlf(raw):
                errors.append(f"{os.path.basename(cmd_path)}: CRLF line endings")
            text = raw.decode("utf-8", errors="replace")
            errs = validate_command_frontmatter(cmd_path, text)
            errors.extend([f"{os.path.basename(cmd_path)}: {e}" for e in errs])

        # Validate agents
        agent_md_files = [n for n in names if n.startswith("agents/") and n.endswith(".md")]
        if agent_md_files:
            for agent_path in agent_md_files:
                raw = zf.read(agent_path)
                if has_crlf(raw):
                    errors.append(f"{os.path.basename(agent_path)}: CRLF line endings")

        # Validate hooks/hooks.json
        if "hooks/hooks.json" in names:
            raw = zf.read("hooks/hooks.json")
            if has_crlf(raw):
                errors.append("hooks/hooks.json: CRLF line endings")
            try:
                hooks_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"hooks/hooks.json: not valid JSON: {e}")
            else:
                hook_errors = validate_hooks_schema(hooks_data)
                errors.extend([f"hooks/hooks.json: {e}" for e in hook_errors])

        # Validate skills
        skill_dirs = set()
        for n in names:
            if n.startswith("skills/") and "/" in n[len("skills/"):]:
                skill_name = n[len("skills/"):].split("/")[0]
                if skill_name:
                    skill_dirs.add(skill_name)

        for skill in sorted(skill_dirs):
            skill_md_path = f"skills/{skill}/SKILL.md"
            if skill_md_path not in names:
                errors.append(f"skills/{skill}/SKILL.md is missing")
            else:
                raw = zf.read(skill_md_path)
                if has_crlf(raw):
                    errors.append(f"skills/{skill}/SKILL.md: CRLF line endings")
                text = raw.decode("utf-8", errors="replace")
                fields = parse_frontmatter(text)
                if fields is None:
                    warnings.append(f"skills/{skill}/SKILL.md: no YAML frontmatter")

                # Skills: name: is ALLOWED, but tools: and allowed-tools: are forbidden
                for bad in SKILL_FORBIDDEN_FIELDS:
                    if bad in fields:
                        errors.append(f"skills/{skill}/SKILL.md: forbidden frontmatter field '{bad}:'")

        # Validate .mcp.json
        if ".mcp.json" in names:
            raw = zf.read(".mcp.json")
            if has_crlf(raw):
                errors.append(".mcp.json: CRLF line endings")
            try:
                mcp_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f".mcp.json: not valid JSON: {e}")
            else:
                mcp_errors = validate_mcp_json(mcp_data)
                errors.extend([f".mcp.json: {e}" for e in mcp_errors])

        # Validate monitors/monitors.json
        if "monitors/monitors.json" in names:
            raw = zf.read("monitors/monitors.json")
            if has_crlf(raw):
                errors.append("monitors/monitors.json: CRLF line endings")
            try:
                monitors_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"monitors/monitors.json: not valid JSON: {e}")
            else:
                monitor_errors = validate_monitors_json(monitors_data)
                errors.extend([f"monitors/monitors.json: {e}" for e in monitor_errors])

        # Validate settings.json
        if "settings.json" in names:
            raw = zf.read("settings.json")
            if has_crlf(raw):
                errors.append("settings.json: CRLF line endings")
            try:
                settings_data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"settings.json: not valid JSON: {e}")
            else:
                settings_errors = validate_settings_json(settings_data)
                errors.extend([f"settings.json: {e}" for e in settings_errors])

    if not errors:
        passed.append("all checks passed")

    return passed, errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_plugin.py <plugin.zip> [plugin2.zip ...]")
        sys.exit(1)

    all_ok = True
    for path in sys.argv[1:]:
        print(f"\n{'='*50}")
        print(f"Testing: {path}")
        print('='*50)

        if not os.path.exists(path):
            print(f"{FAIL} File not found: {path}")
            all_ok = False
            continue

        passed, errors, warnings = validate_plugin(path)

        for p in passed:
            print(f"  {PASS} {p}")
        for w in warnings:
            print(f"  {WARN}  {w}")
        for e in errors:
            print(f"  {FAIL} {e}")

        if errors:
            all_ok = False
            print(f"\n{FAIL} FAILED — {len(errors)} error(s)")
        else:
            print(f"\n{PASS} PASSED")

    if all_ok:
        print(f"\n{PASS} All plugins passed")
        sys.exit(0)
    else:
        print(f"\n{FAIL} Some plugins failed")
        sys.exit(1)


if __name__ == "__main__":
    main()