from harnesses.lib import hallucinated_dependency_test_harness as h


def test_self_test_passes() -> None:
    assert h.run_self_test() == 0


def test_oracle_clean_on_real_pins() -> None:
    assert h.hallucinated_pins(h.REAL_PINS) == []


def test_pin_resolves_matches_live_environment() -> None:
    import pydantic

    assert h.pin_resolves(f"pydantic=={pydantic.VERSION}") is True  # the installed version
    assert h.pin_resolves("pydantic==99.99.99") is False             # real package, fake version
    assert h.pin_resolves("nonexistent-typosquat-pkg-xyz==1.0.0") is False  # absent package
