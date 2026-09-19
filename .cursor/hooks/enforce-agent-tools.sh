#!/usr/bin/env bash
# preToolUse: deny tools not allowed for the active Shinobu workflow agent.
set -euo pipefail

PERMISSIONS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agent-permissions.json"

allow() { printf '%s\n' '{"permission":"allow"}'; }

deny() {
  jq -n \
    --arg agent "$1" \
    --arg tool_key "$2" \
    --arg tool_name "$3" \
    '{
      permission: "deny",
      user_message: ("Blocked " + $tool_name + " for " + $agent + "."),
      agent_message: ("Tool " + $tool_name + " (" + $tool_key + ") is denied for " + $agent + ". Shinobu sends sheep for disk work.")
    }'
}

normalize_agent() {
  local raw="${1:-}"
  raw="${raw//_/-}"
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  case "$raw" in
    generalpurpose|general-purpose|general_purpose|explore|shell) printf '%s' "" ;;
    *) printf '%s' "$raw" ;;
  esac
}

map_tool() {
  case "${1:-}" in
    Read) printf '%s' "read" ;;
    Write|StrReplace|EditNotebook) printf '%s' "write" ;;
    Delete) printf '%s' "delete" ;;
    Shell) printf '%s' "shell" ;;
    Grep) printf '%s' "grep" ;;
    Glob) printf '%s' "glob" ;;
    SemanticSearch|semantic_search|codebase_search) printf '%s' "semantic_search" ;;
    Task) printf '%s' "task" ;;
    WebSearch) printf '%s' "web_search" ;;
    WebFetch) printf '%s' "web_fetch" ;;
    AskQuestion) printf '%s' "ask_question" ;;
    TodoWrite) printf '%s' "todo_write" ;;
    GenerateImage) printf '%s' "generate_image" ;;
    SwitchMode) printf '%s' "switch_mode" ;;
    MCP:*|mcp:*) printf '%s' "mcp" ;;
    *) printf '%s' "" ;;
  esac
}

resolve_agent() {
  local input="$1"
  local agent

  # Only trust explicit agent identity from Cursor — never match task/description
  # text (e.g. "shinobu" in a prompt falsely resolves to the shinobu orchestrator).
  for field in subagent_type agent_type; do
    agent="$(normalize_agent "$(printf '%s' "$input" | jq -r --arg f "$field" '.[$f] // empty')")"
    if [[ -n "$agent" ]] && jq -e --arg a "$agent" 'has($a)' "$PERMISSIONS" >/dev/null; then
      printf '%s' "$agent"
      return 0
    fi
  done

  printf '%s' ""
}

input="$(cat)"

if ! command -v jq >/dev/null 2>&1 || [[ ! -f "$PERMISSIONS" ]]; then
  allow
  exit 0
fi

tool_name="$(printf '%s' "$input" | jq -r '.tool_name // empty')"
tool_key="$(map_tool "$tool_name")"
agent="$(resolve_agent "$input")"

if [[ -z "$agent" || -z "$tool_key" ]]; then
  allow
  exit 0
fi

if jq -e --arg a "$agent" --arg t "$tool_key" '.[$a][$t] == true' "$PERMISSIONS" >/dev/null; then
  allow
  exit 0
fi

deny "$agent" "$tool_key" "$tool_name"
exit 0
