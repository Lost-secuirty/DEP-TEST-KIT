from harnesses.lib import prompt_cache_prefix_test_harness as h


def test_self_test_passes() -> None:
    assert h.run_self_test() == 0


def test_oracle_stable_on_good_prompt() -> None:
    assert h.prefix_is_stable(h.stable_prompt()) is True


def test_prefix_is_stable_detects_volatile_in_prefix() -> None:
    # Volatile token AFTER the breakpoint is fine (dynamic suffix); inside the prefix is not.
    assert h.prefix_is_stable(h.stable_prompt()) is True
    assert h.prefix_is_stable(h.buggy_prompt()) is False
