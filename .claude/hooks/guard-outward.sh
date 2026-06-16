#!/bin/bash
# PreToolUse hook: gate OUTWARD-FACING repo mutations so they cannot fire silently
# against the operator's intent (the 2026-06-16 auto-PR incident; ADR-0008).
#
#   merge / enable auto-merge   -> DENY  (WA #6 / GR: the operator owns every merge)
#   other GitHub MCP mutations  -> ASK   (create/update PR, contents write, push,
#                                          delete, subscribe, comment) — legitimate
#                                          ONLY as the operator's explicit request
#   read-only / everything else -> defer to normal permission flow (no output)
#
# CAVEAT (verified 2026-06-16): PreToolUse permissionDecision is NOT reliably honored
# for MCP tool calls on current Claude Code (anthropics/claude-code #33106, #37210;
# deny-rule fall-through #27547). Treat this as best-effort defense-in-depth. The
# RELIABLY-firing teeth is the UserPromptSubmit re-injection (inject-invariants.sh);
# the durable backstop for merges is GitHub branch protection (operator-only). This
# hook ships --self-test so its LOGIC is provable even where the harness ignores the
# decision (no vacuous green).
set -euo pipefail

gate() { # $1 = tool name -> echoes "deny" | "ask" | "" (defer)
  case "$1" in
    mcp__github__merge_pull_request|mcp__github__enable_pr_auto_merge) echo deny ;;
    mcp__github__create_pull_request|mcp__github__update_pull_request|mcp__github__create_or_update_file|mcp__github__push_files|mcp__github__delete_file|mcp__github__subscribe_pr_activity|mcp__github__add_issue_comment|mcp__github__add_comment_to_pending_review|mcp__github__pull_request_review_write) echo ask ;;
    *) echo "" ;;
  esac
}

reason() { # $1 = decision
  case "$1" in
    deny) echo "Merges and auto-merge are the operator's alone (WA #6). Never merge." ;;
    ask)  echo "Outward-facing repo mutation: confirm this is the operator's explicit, current request before proceeding (ADR-0008). A generic 'just do it' does not override session-specific intent." ;;
  esac
}

emit() { # $1 = decision, $2 = reason
  jq -n --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
}

if [ "${1:-}" = "--self-test" ]; then
  f=0
  ck() { g=$(gate "$1"); [ "$g" = "$2" ] || { echo "FAIL: $1 -> '$g' (want '$2')"; f=$((f + 1)); }; }
  ck mcp__github__merge_pull_request deny
  ck mcp__github__enable_pr_auto_merge deny
  ck mcp__github__create_pull_request ask
  ck mcp__github__subscribe_pr_activity ask
  ck mcp__github__push_files ask
  ck mcp__github__create_or_update_file ask
  ck mcp__github__get_file_contents ""
  ck mcp__github__list_pull_requests ""
  ck Bash ""
  if [ "$f" -ne 0 ]; then echo "guard-outward self-test: $f failure(s)"; exit 1; fi
  echo "guard-outward self-test: OK"
  exit 0
fi

input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null || true)
[ -z "${tool:-}" ] && exit 0
d=$(gate "$tool")
[ -z "$d" ] && exit 0
emit "$d" "$(reason "$d")"
exit 0
