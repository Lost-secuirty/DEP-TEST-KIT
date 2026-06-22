"""Proof: the HMAC verifier rejects the forged webhook the unverified receiver acts on.
A bogus signature fails the constant-time HMAC vs being accepted unconditionally."""

from harnesses.lib import webhook_signature_test_harness as h


def test_proof_buggy_is_flagged() -> None:
    assert h.accepts_forged_webhook(h.UnverifiedWebhook) is True


def test_proof_oracle_not_flagged() -> None:
    assert h.accepts_forged_webhook(h.SignedWebhookVerifier) is False


def test_proof_oracle_happy_path() -> None:
    assert h.verifies_genuine_webhook(h.SignedWebhookVerifier) is True
