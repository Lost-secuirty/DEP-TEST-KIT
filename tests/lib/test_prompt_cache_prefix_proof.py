"""Proof: the harness has teeth — the oracle catches a cache-busting volatile token in the
cached prefix that the naive "a breakpoint exists" checker passes; the oracle clears a stable one."""

from harnesses.lib import prompt_cache_prefix_test_harness as h


def test_proof_oracle_catches_volatile_prefix() -> None:
    assert h.prefix_is_stable(h.buggy_prompt()) is False
    assert h.cache_busting_blocks(h.buggy_prompt()) != []


def test_proof_naive_check_misses_volatile_prefix() -> None:
    # The naive check only confirms a breakpoint is configured, so it passes the buggy prompt.
    assert h.naive_prefix_check(h.buggy_prompt()) is True


def test_proof_oracle_clean_on_stable_prompt() -> None:
    assert h.prefix_is_stable(h.stable_prompt()) is True
