"""Proof: object-scoped authorization catches the bypass RBAC misses. Hypothesis
falsifies the RBAC-only broker (an out-of-scope object is authorized) but not the
object-scoped broker."""

from harnesses.ai import agent_capability_allowlist_test_harness as h


def test_proof_rbac_only_has_object_bypass() -> None:
    assert h.find_authz_bypass(h.RbacOnlyBroker()) is True


def test_proof_capability_broker_no_bypass() -> None:
    assert h.find_authz_bypass(h.CapabilityBroker()) is False


def test_proof_capability_broker_allows_in_scope() -> None:
    assert h.authorizes_in_scope(h.CapabilityBroker()) is True


# --- scenario coverage: the RBAC-only broker authorizes out-of-scope objects ---
def test_proof_rbac_only_authorizes_out_of_scope() -> None:
    broker = h.RbacOnlyBroker()
    for tool in h.GRANT:
        assert broker.authorize(h.GRANT, tool, "etc/shadow") is True, tool


import pytest  # noqa: E402

# RbacOnlyBroker ignores object scope, so any GRANTED tool authorizes an out-of-scope object.
_GRANTED_OUT_OF_SCOPE = [
    ("read_file", "reports/q3.txt"),
    ("read_file", "/etc/passwd"),
    ("read_file", "reports/q1.txt.evil"),
    ("read_file", ""),
    ("read_file", "../q1.txt"),
    ("search", "private-index"),
    ("search", "secrets"),
    ("search", ""), ("read_file", "reports/Q1.txt"), ("read_file", "reports/q1"),
    ("read_file", "reports/q2.txt.bak"),
]


@pytest.mark.parametrize("tool,obj", _GRANTED_OUT_OF_SCOPE)
def test_proof_rbac_authorizes_out_of_scope_corpus(tool, obj) -> None:
    assert h.RbacOnlyBroker().authorize(h.GRANT, tool, obj) is True, (tool, obj)
