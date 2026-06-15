#!/usr/bin/env python3
"""Prompt-cache prefix-stability harness (volatile content in the cached prefix; pydantic).

WHY:   LLM prompt caching (e.g. Anthropic `cache_control` breakpoints) only pays off if the
       cached PREFIX is byte-stable across calls: the provider reuses the prefill of every block
       up to the last cache breakpoint. If a developer interpolates volatile content — a
       timestamp, a request id, a uuid — into a block that sits in that prefix, the prefix
       changes every call, every cache read misses, and the "caching" silently bills full price
       and full latency. A naive check ("did we set a cache_control breakpoint?") passes: the
       breakpoint exists; it just protects nothing.

HOW:   Model the prompt as ordered content blocks (a pydantic-validated `Block`, mirroring the
       real LLM-client content-block + `cache_control` shape). The cached prefix is every block
       up to and including the last breakpoint. The ORACLE `prefix_is_stable` returns False if
       any prefix block contains a volatile token (ISO timestamp / uuid / explicit request-id
       marker); the BUGGY `naive_prefix_check` only checks that a breakpoint EXISTS, so a
       timestamp baked into the system prompt is invisible. `buggy_prompt` builds exactly that
       mistake (a session timestamp in the cached system block); `stable_prompt` keeps volatile
       content in the dynamic suffix, after the breakpoint.

WHERE: lib/ — dependency-backed (pydantic, already in the `lib` extra) and fully in-process, no
       live LLM and no API key. DESIGN CALL: a pure-stdlib string scanner would belong in the
       stdlib `testing-kits` repo; here pydantic does load-bearing work — validating the
       content-block schema (role / non-empty text / breakpoint) the cache contract is defined
       over — so the harness fits DEP-TEST-KIT's dependency-backed charter. The volatile token is
       a fixed literal (not a real clock) so the self-test is deterministic; in real code it
       would be an interpolated `datetime.now()` / `uuid4()`.

Self-test:
  python harnesses/lib/prompt_cache_prefix_test_harness.py --self-test
"""

from __future__ import annotations

import argparse
import re
import sys

from pydantic import BaseModel, field_validator  # validates the cached content-block contract

# Symbol the vacuous-green meta-gate (tools/vacuity_gate.py) neuters to confirm teeth.
VACUITY_TARGETS = ["prefix_is_stable"]

# Volatile tokens that bust a cached prefix: ISO-8601 timestamps, uuids, explicit id/epoch markers.
_VOLATILE_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"                       # ISO-8601 timestamp
    r"|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"  # uuid
    r"|\b(?:request[_-]?id|trace[_-]?id|epoch|timestamp)\s*[=:]",  # explicit volatile markers
)
_ROLES = {"system", "user", "assistant"}


class Block(BaseModel):
    """A prompt content block. `cache_control=True` marks a cache breakpoint (prefix boundary)."""

    role: str
    text: str
    cache_control: bool = False

    @field_validator("role")
    @classmethod
    def _role_known(cls, v: str) -> str:
        if v not in _ROLES:
            raise ValueError(f"unknown role {v!r} (expected one of {sorted(_ROLES)})")
        return v

    @field_validator("text")
    @classmethod
    def _text_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("block text must be non-empty")
        return v


def _cached_prefix(blocks: list[Block]) -> list[Block]:
    """Blocks up to and including the last cache breakpoint — the bytes the provider caches."""
    last = max((i for i, b in enumerate(blocks) if b.cache_control), default=-1)
    return blocks[: last + 1]


def cache_busting_blocks(blocks: list[Block]) -> list[int]:
    """ORACLE detail: indices of cached-prefix blocks that contain a volatile (cache-busting) token."""
    return [i for i, b in enumerate(_cached_prefix(blocks)) if _VOLATILE_RE.search(b.text)]


def prefix_is_stable(blocks: list[Block]) -> bool:
    """ORACLE: True iff the cached prefix carries no volatile token (so cache reads actually hit)."""
    return not cache_busting_blocks(blocks)


def naive_prefix_check(blocks: list[Block]) -> bool:
    """BUGGY: trusts that configuring ANY cache breakpoint means caching works; never inspects
    whether the prefix is byte-stable, so volatile content baked into the prefix is invisible."""
    return any(b.cache_control for b in blocks)


def stable_prompt() -> list[Block]:
    """ORACLE assembly: static system instructions in the cached prefix; volatile content
    (the session timestamp) lives in the dynamic suffix AFTER the breakpoint."""
    return [
        Block(role="system", text="You are a helpful coding assistant. Follow the house style.",
              cache_control=True),
        Block(role="user", text="Session started 2026-06-15T09:00:00Z. Summarize the diff."),
    ]


def buggy_prompt() -> list[Block]:
    """BUGGY assembly: a session timestamp is interpolated INTO the cached system block (in real
    code this would be f\"... {datetime.now()}\"), so the cached prefix changes every call."""
    return [
        Block(role="system",
              text="You are a helpful coding assistant. Session started 2026-06-15T09:00:00Z.",
              cache_control=True),
        Block(role="user", text="Summarize the diff."),
    ]


def run_self_test() -> int:
    failures = 0

    if prefix_is_stable(stable_prompt()) is not True:
        failures += 1
        print("FAIL: oracle flagged a stable prompt (false positive)", file=sys.stderr)

    if prefix_is_stable(buggy_prompt()) is not False:
        failures += 1
        print("FAIL: oracle missed volatile content in the cached prefix", file=sys.stderr)

    # The teeth gap: the naive check only confirms a breakpoint exists, so it passes the buggy
    # prompt (which DOES have a breakpoint) despite the cache-busting timestamp in the prefix.
    if naive_prefix_check(buggy_prompt()) is not True:
        failures += 1
        print("FAIL: naive check did not pass the buggy prompt — no teeth gap", file=sys.stderr)

    if failures:
        print(f"self-test: {failures} failure(s)", file=sys.stderr)
        return 1
    print("self-test: OK (oracle catches a cache-busting timestamp in the prefix the naive "
          "breakpoint-exists check misses)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prompt-cache prefix-stability harness")
    parser.add_argument("--self-test", action="store_true", help="run the planted-bug self-test")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help(sys.stderr)
        return 2
    return run_self_test()


if __name__ == "__main__":
    sys.exit(main())
