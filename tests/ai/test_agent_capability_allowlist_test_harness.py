"""Oracle + CLI-contract test for agent_capability_allowlist (pairs with its proof file).

Two-file convention: this asserts the secure path and the runnable CLI contract;
test_agent_capability_allowlist_proof.py asserts the planted bug is caught (the teeth).
"""

from harnesses.ai import agent_capability_allowlist_test_harness as h


def test_self_test_green() -> None:
    assert h.run_self_test() == 0


def test_cli_no_args_returns_2() -> None:
    assert h.main([]) == 2


def test_cli_self_test_returns_0() -> None:
    assert h.main(["--self-test"]) == 0


def test_oracle_happy_path() -> None:
    assert h.authorizes_in_scope(h.CapabilityBroker()) is True


# --- scenario coverage: object-scope authz across the whole grant ---
def test_oracle_authorizes_every_in_scope_object() -> None:
    broker = h.CapabilityBroker()
    for tool, objects in h.GRANT.items():
        for obj in objects:
            assert broker.authorize(h.GRANT, tool, obj) is True, (tool, obj)


def test_oracle_denies_out_of_scope_object() -> None:
    broker = h.CapabilityBroker()
    for tool in h.GRANT:
        assert broker.authorize(h.GRANT, tool, "etc/shadow") is False, tool


def test_oracle_denies_ungranted_tool() -> None:
    assert h.CapabilityBroker().authorize(h.GRANT, "delete_database", "anything") is False


# --- second pass: empty grant denies all; prefix look-alikes denied ---
def test_oracle_denies_with_empty_grant() -> None:
    assert h.CapabilityBroker().authorize({}, "read_file", "reports/q1.txt") is False


def test_oracle_denies_prefix_lookalike_objects() -> None:
    broker = h.CapabilityBroker()
    for tool, objects in h.GRANT.items():
        for obj in objects:
            assert broker.authorize(h.GRANT, tool, obj + ".evil") is False, (tool, obj)


# --- third pass: garbage tool/object pairs are denied ---
def test_oracle_denies_garbage_tool_and_object() -> None:
    broker = h.CapabilityBroker()
    for tool, obj in [("", ""), ("read_file", ""), ("", "reports/q1.txt"), ("../", "../")]:
        assert broker.authorize(h.GRANT, tool, obj) is False, (tool, obj)


import pytest  # noqa: E402

_OUT_OF_SCOPE = [
    ("read_file", "reports/q3.txt"),
    ("read_file", "/etc/passwd"),
    ("read_file", "reports/q1.txt.evil"),
    ("read_file", ""),
    ("read_file", "../q1.txt"),
    ("search", "private-index"),
    ("search", "secrets"),
    ("search", ""), ("delete_file", "reports/q1.txt"), ("write_file", "reports/q1.txt"),
    ("exec", "whoami"), ("read_file", "reports/Q1.txt"), ("read_file", "reports/q1"),
    ("admin", "*"), ("read_file", "reports/q2.txt.bak"),
]


@pytest.mark.parametrize("tool,obj", _OUT_OF_SCOPE)
def test_oracle_denies_out_of_scope_corpus(tool, obj) -> None:
    assert h.CapabilityBroker().authorize(h.GRANT, tool, obj) is False, (tool, obj)


_OUT_OF_SCOPE_2 = [
    ("read_file", "reports/../../../etc/shadow"),
    ("read_file", "reports/q1.txt%00.png"),
    ("search", "../private"),
    ("read_file", "\\\\server\\share"),
    ("network", "169.254.169.254"),
    ("shell", "ls"),
    ("db", "SELECT *"),
    ("read_file", "reports/q1.txt "),
    ("env", "AWS_SECRET"),
    ("read_file", "reports/Q2.txt"),
]


@pytest.mark.parametrize("tool,obj", _OUT_OF_SCOPE_2)
def test_oracle_denies_out_of_scope_corpus_2(tool, obj) -> None:
    assert h.CapabilityBroker().authorize(h.GRANT, tool, obj) is False, (tool, obj)
