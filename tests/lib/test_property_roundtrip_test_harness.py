from hypothesis import given, settings
from hypothesis import strategies as st

from harnesses.lib import property_roundtrip_test_harness as h


@settings(max_examples=300)
@given(st.text())
def test_roundtrip_holds_for_oracle(s: str) -> None:
    assert h.rle_decode(h.rle_encode(s)) == s


def test_self_test_passes() -> None:
    assert h.run_self_test() == 0
