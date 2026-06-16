# 0008 — Enforcement teeth: outward-action guard + per-turn invariant re-injection

Status: accepted (2026-06-16). Records the decision to enforce load-bearing rules with
committed `.claude/` mechanisms rather than prose alone, and closes the enforcement item
ADR-0002 left open ("documented protocol vs. a committed hook — tracked separately,
requires explicit operator sign-off"). Operator signed off 2026-06-16.

## Context

Two forces converged:

1. **ADR-0002 deferred the mechanism.** It mandated a self-audit before every push but
   explicitly left enforcement-via-hook pending operator sign-off.
2. **An incident proved prose is not a control.** Off a session handoff that said *the
   operator opens the PRs by hand*, the agent auto-created two draft PRs (DEP #35,
   testing-kits #44) and the session auto-subscribed to PR activity — triggering a
   bot/CI cascade the operator did not ask for. Root cause: a generic harness rule
   ("after pushing, always open a draft PR — don't ask") silently overrode
   session-specific intent, and nothing deterministic gated the outward action. No rule
   in `AGENTS.md` forbade it (WA #6 governs merges, not PR creation), so re-reading the
   rules would not have stopped it. Not a security-rule breach — an intent/authority drift.

The general failure mode is well-documented: long-context "lost in the middle" (mid-context
instruction accuracy drops >30%) and constraint-pressure decay (instruction-following
degrades as simultaneous constraints accumulate). A rule read once at the top of a long
chain genuinely fades. Adding more prose rules feeds the same failure mode.

## Decision

### The rule (WA #9 / GOLDEN_RULES): "Teeth, not trust"
A load-bearing rule earns deterministic enforcement — a `.claude/` hook, a permission
rule, a CI gate, or branch protection — or it does not count. Outward-facing or
irreversible actions (open/update/merge a PR, push to a protected branch, subscribe to PR
activity, post a comment, any outbound send) are **STOP-and-confirm** unless they are the
operator's explicit, current request: a generic "just do it" never silently overrides
session-specific intent.

### The mechanisms (committed under `.claude/`)
- **`hooks/guard-outward.sh`** (PreToolUse, matcher `mcp__github__.*`): DENY
  `merge_pull_request` / `enable_pr_auto_merge`; ASK on other GitHub mutations
  (create/update PR, contents write, push, delete, subscribe, comment). Read-only calls
  defer to normal flow.
- **`permissions.ask` / `permissions.deny`** in `settings.json`: the same gate expressed
  declaratively (the native, first-class mechanism) as a second layer.
- **`hooks/inject-invariants.sh`** (UserPromptSubmit): re-injects the top invariants into
  context **every turn** via `additionalContext`, countering drift by keeping the rules at
  a high-attention (recency) position rather than buried at the top of the chain.
- Both new hooks ship `--self-test` asserting their logic, so the gate itself is not
  vacuous green (the cardinal anti-pattern, ADR-0001).

### Verified caveat (the honest part)
PreToolUse `permissionDecision` deny/ask is **not reliably honored for MCP tool calls** on
current Claude Code (anthropics/claude-code #33106, #37210; deny-rule fall-through #27547).
Therefore:
- The **reliably-firing** in-session teeth is the UserPromptSubmit re-injection (a harness
  event that always runs, independent of the MCP bug).
- The **durable backstop** for the irreversible action (merge) is **GitHub branch
  protection** (operator-only merge), which holds regardless of hook reliability.
- The PreToolUse hook + permission lists are best-effort defense-in-depth, self-proven on
  logic but to be confirmed actually-firing on the operator's Claude Code build.

## Consequence
- Closes ADR-0002's open enforcement item with operator sign-off.
- Makes the outward-action class confirm-first by default without blocking the legitimate
  draft-PR flow (ASK, not DENY, for creation): the operator confirms, but it cannot happen
  silently against stated intent.
- `AGENTS.md` is the shared core, so WA #9 is intended to propagate to `testing-kits` and
  the other repos. This change is the **reference implementation on DEP-TEST-KIT only**;
  sync follows after operator review.
- Owner actions: (1) confirm the ask/deny actually fires on your Claude Code build; (2)
  keep `main` branch protection on as the real backstop; (3) the `.claude/logs/events.jsonl`
  PostToolUse log already records every tool call (incl. outward ones) for after-the-fact
  drift visibility — no change needed there.
