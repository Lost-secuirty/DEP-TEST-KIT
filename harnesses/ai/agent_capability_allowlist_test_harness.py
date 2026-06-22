#!/usr/bin/env python3
"""Agent capability / object-scope authorization harness (Hypothesis).

OWASP Top 10 for Agentic Applications 2026 -- ASI03 Agent Identity & Privilege Abuse
(the Least-Agency principle).

WHY: The 2026 failure that role-based checks miss: "RBAC controls which TABLES the agent
can touch, but not the ROWS within those tables." An agent granted a `read_file` tool for
its own task files can be steered to read ANY file -- the tool is in scope, the OBJECT is
not. A test that checks "is the tool allowed?" passes; only object-scoped authorization
catches it. Hypothesis is the right oracle: it generates thousands of (tool, object) pairs
and finds the one out-of-scope object the broker wrongly authorizes -- an example test never
would.

HOW: `CapabilityBroker` is the ORACLE -- `authorize(grant, tool, obj)` returns True only
when the tool is granted AND the object is inside that tool's grant. `RbacOnlyBroker` is the
planted defect -- it authorizes on the TOOL alone, ignoring the object scope.
`find_authz_bypass` runs a Hypothesis property ("an out-of-scope object is never
authorized") and returns True when the property is falsified -- the oracle holds, the buggy
broker is falsified (object-level bypass).

WHERE: ai/ -- in-process, deterministic. Adds `hypothesis` to the `ai` extra (already
declared for the ai lane).

Self-test:
    python harnesses/ai/agent_capability_allowlist_test_harness.py --self-test
"""

from __future__ import annotations

import argparse
import sys

from hypothesis import given, settings
from hypothesis import strategies as st

# Symbol the vacuous-green meta-gate (tools/vacuity_gate.py) neuters to confirm teeth.
VACUITY_TARGETS = ["CapabilityBroker.authorize"]

DOSSIER = {
    "name": "agent_capability_allowlist",
    "path": "harnesses/ai/agent_capability_allowlist_test_harness.py",
    "flavor": "ai",
    "dependency": "hypothesis",
    "standard": (
        "OWASP Top 10 for Agentic Applications 2026 — ASI03 Identity & Privilege Abuse (Least- "
        "Agency)"
    ),
    "failure_class": (
        "Object/row-level authorization bypass — in-scope tool used on an out-of-scope object"
    ),
    "oracle": "CapabilityBroker.authorize — tool AND object must be inside the task grant",
    "buggy": "RbacOnlyBroker.authorize — authorizes on the tool alone (ignores object scope)",
    "planted_mutant": "Hypothesis finds an out-of-scope object the RBAC-only broker authorizes",
    "proof_file": "tests/ai/test_agent_capability_allowlist_proof.py",
    "vacuity_targets": ["CapabilityBroker.authorize"],
    "commands": ["python harnesses/ai/agent_capability_allowlist_test_harness.py --self-test"],
    "known_limits": "static example grant; real systems bind grants to per-request task context",
    "related": ["excessive_agency (LLM06)", "agent_tool_manifest (ASI04)"],
}

# A per-task grant: each tool maps to the exact objects it may touch.
GRANT = {
    "read_file": {"reports/q1.txt", "reports/q2.txt"},
    "search": {"public-index"},
}


class CapabilityBroker:
    """ORACLE: authorize only when the tool is granted AND the object is in scope."""

    def authorize(self, grant: dict, tool: str, obj: str) -> bool:
        return tool in grant and obj in grant[tool]


class RbacOnlyBroker:
    """BUGGY: authorize on the tool alone -- object scope is ignored."""

    def authorize(self, grant: dict, tool: str, obj: str) -> bool:
        return tool in grant  # BUG: any object passes once the tool is granted


def authorizes_in_scope(broker) -> bool:
    """Legitimate in-scope access must succeed."""
    return broker.authorize(GRANT, "read_file", "reports/q1.txt")


def find_authz_bypass(broker) -> bool:
    """True == Hypothesis found an out-of-scope object the broker authorized (a bypass)."""
    @settings(max_examples=200)
    @given(tool=st.sampled_from(sorted(GRANT)), obj=st.text(min_size=1, max_size=40))
    def prop(tool: str, obj: str) -> None:
        if obj not in GRANT[tool]:                      # an out-of-scope object
            assert broker.authorize(GRANT, tool, obj) is False

    try:
        prop()
    except AssertionError:
        return True
    return False


def run_self_test() -> int:
    failures = 0
    if not authorizes_in_scope(CapabilityBroker()):
        failures += 1
        print("FAIL: oracle denied legitimate in-scope access", file=sys.stderr)
    if find_authz_bypass(CapabilityBroker()):
        failures += 1
        print("FAIL: oracle authorized an out-of-scope object", file=sys.stderr)
    if not find_authz_bypass(RbacOnlyBroker()):
        failures += 1  # the planted bug must be caught -- else vacuous green
        print("FAIL: RBAC-only object bypass was NOT caught", file=sys.stderr)
    if failures:
        print(f"self-test: {failures} failure(s)", file=sys.stderr)
        return 1
    print(
        "self-test: OK (object-scoped broker has no bypass; RBAC-only bypass caught by Hypothesis)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Agent capability/object-scope authorization harness"
    )
    parser.add_argument("--self-test", action="store_true", help="run the planted-bug self-test")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help(sys.stderr)
        return 2
    return run_self_test()


if __name__ == "__main__":
    sys.exit(main())
