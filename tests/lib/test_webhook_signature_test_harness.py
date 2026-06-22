"""Oracle + CLI-contract test for webhook_signature (pairs with its proof file).

Two-file convention: this asserts the secure path and the runnable CLI contract;
test_webhook_signature_proof.py asserts the planted bug is caught (the teeth).
"""

from harnesses.lib import webhook_signature_test_harness as h


def test_self_test_green() -> None:
    assert h.run_self_test() == 0


def test_cli_no_args_returns_2() -> None:
    assert h.main([]) == 2


def test_cli_self_test_returns_0() -> None:
    assert h.main(["--self-test"]) == 0


def test_oracle_happy_path() -> None:
    assert h.verifies_genuine_webhook(h.SignedWebhookVerifier) is True


import pytest  # noqa: E402


@pytest.mark.parametrize("payload,sig_kind,ts,now", [
    ("order.refunded", "bogus", 1000, 1000),
    ("order.refunded", "good", 1000, 1000),
    ("order.paid", "good", 1000, 2000),
    ("order.paid", "good", 1000, 500),
    ("order.paid", "empty", 1000, 1000),
])
def test_oracle_rejects_webhook_attack(payload, sig_kind, ts, now) -> None:
    verifier = h.SignedWebhookVerifier()
    good = verifier.sign("order.paid", 1000)
    sig = {"bogus": "00" * 32, "good": good, "empty": ""}[sig_kind]
    assert verifier.verify(payload, sig, ts, now) is False


@pytest.mark.parametrize("now,expected", [
    (1000, True), (1100, True), (1300, True),
    (1301, False), (700, True), (699, False),
])
def test_oracle_enforces_replay_window(now, expected) -> None:
    verifier = h.SignedWebhookVerifier()
    good = verifier.sign("evt", 1000)
    assert verifier.verify("evt", good, 1000, now) is expected


# === our own / batch 1 (original) ===
_WH_V = h.SignedWebhookVerifier()
_WH_SIG = _WH_V.sign("order.paid", 1000)
_WH_SPACED = " ".join(_WH_SIG[i:i + 2] for i in range(0, len(_WH_SIG), 2))


# Constantin (surreal/sw): metamorphic -- re-dressing the hex tag must NOT flip the verdict.
@pytest.mark.parametrize("rendering", [_WH_SIG.upper(), _WH_SPACED])
def test_oracle_mr_hex_encoding_invariant(rendering) -> None:
    assert _WH_V.verify("order.paid", rendering, 1000, 1000) is True


def _wh_flip(sig, i):
    b = bytearray.fromhex(sig)
    b[i] ^= 0x01
    return b.hex()


@pytest.mark.parametrize("pos", [0, 7, 31])
def test_oracle_mr_signature_bit_flip_rejected(pos) -> None:
    assert _WH_V.verify("order.paid", _wh_flip(_WH_SIG, pos), 1000, 1000) is False


# Knox (absurd/sw): an integer timestamp keeps the "{ts}.{payload}" split unambiguous.
def test_oracle_timestamp_dot_shift_non_malleable() -> None:
    genuine = _WH_V.sign("34.order", 12)                      # HMAC over "12.34.order"
    assert _WH_V.verify("34.order", genuine, 12, 12) is True
    assert _WH_V.verify("2.34.order", genuine, 1, 1) is False    # would be "1.2.34.order"
    assert _WH_V.verify("4.order", genuine, 123, 123) is False   # would be "123.4.order"


# Pip (whimsical/sw): two providers, two secrets -- a neighbour's signature means nothing here.
def test_oracle_cross_instance_signature_rejected() -> None:
    assert h.SignedWebhookVerifier().verify("order.paid", _WH_SIG, 1000, 1000) is False
