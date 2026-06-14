"""Proof: the harness has teeth — it catches the planted bug and clears the oracle."""

from harnesses.lib import property_roundtrip_test_harness as h


def test_proof_buggy_decoder_is_caught() -> None:
    # The single-run-dropping decoder must be falsified by the property.
    assert h.find_roundtrip_counterexample(h.buggy_rle_decode) is True


def test_proof_oracle_is_not_falsified() -> None:
    assert h.find_roundtrip_counterexample(h.rle_decode) is False


def test_proof_buggy_decoder_concretely_wrong() -> None:
    # Minimal human-visible instance of the bug the property shrinks toward.
    assert h.buggy_rle_decode(h.rle_encode("ab")) != "ab"
