"""Proof: the harness has teeth — the oracle catches a hallucinated VERSION of a real,
installed package that the naive name-only checker misses; the oracle stays clean on real pins."""

from harnesses.lib import hallucinated_dependency_test_harness as h


def test_proof_oracle_catches_hallucinated_pins() -> None:
    found = set(h.hallucinated_pins(h.HALLUCINATED_PINS))
    assert set(h.HALLUCINATED_PINS) <= found


def test_proof_naive_checker_misses_hallucinated_version_of_real_package() -> None:
    # The naive checker only verifies the package NAME is installed, so a fake version of a real
    # package slips through (it still catches the entirely-absent typosquat — not the teeth gap).
    found = set(h.buggy_hallucinated_pins(h.HALLUCINATED_PINS))
    assert h.HALLUCINATED_VERSION_OF_REAL_PKG not in found


def test_proof_oracle_clean_on_real_pins() -> None:
    assert h.hallucinated_pins(h.REAL_PINS) == []
