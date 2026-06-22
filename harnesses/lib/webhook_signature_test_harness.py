#!/usr/bin/env python3
"""Webhook-signature harness (cryptography): verify HMAC + timestamp, reject forgeries.

OWASP Top 10:2025 A08 Software and Data Integrity Failures (unverified webhook).

WHY: An endpoint that acts on inbound webhooks without verifying the provider's signature
will act on anything an attacker POSTs -- forged 'payment succeeded' / 'refund' events. The
provider signs `timestamp.payload` (Stripe/GitHub style); the receiver must recompute the HMAC
in constant time and reject stale timestamps (replay).

HOW: `SignedWebhookVerifier` is the ORACLE -- HMAC over `timestamp.payload` with a shared
secret, constant-time, plus a replay window. `UnverifiedWebhook` is the planted defect -- it
accepts anything. `accepts_forged_webhook` submits an attacker payload with a bogus signature
and reports whether it was acted on.

WHERE: lib/ -- dependency-backed (`cryptography` HMAC-SHA256), in-process.

Self-test:
    python harnesses/lib/webhook_signature_test_harness.py --self-test
"""

from __future__ import annotations

import argparse
import secrets
import sys
from typing import Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, hmac

# Symbol the vacuous-green meta-gate (tools/vacuity_gate.py) neuters to confirm teeth.
VACUITY_TARGETS = ["accepts_forged_webhook"]

DOSSIER = {
    "name": "webhook_signature",
    "path": "harnesses/lib/webhook_signature_test_harness.py",
    "flavor": "lib",
    "dependency": "cryptography",
    "standard": "OWASP Top 10:2025 A08 Integrity Failures - webhook signature verification",
    "failure_class": "Acting on an inbound webhook without verifying the provider HMAC signature",
    "oracle": "SignedWebhookVerifier.verify - HMAC over timestamp.payload + replay window",
    "buggy": "UnverifiedWebhook.verify - accept anything",
    "planted_mutant": "an attacker payload with a bogus signature is acted on",
    "proof_file": "tests/lib/test_webhook_signature_proof.py",
    "vacuity_targets": ["accepts_forged_webhook"],
    "commands": ["python harnesses/lib/webhook_signature_test_harness.py --self-test"],
    "known_limits": "HMAC + timestamp window; not provider key-rotation or idempotency keys",
    "related": ["agent_message_auth", "provenance_attestation", "oauth_pkce"],
}

_WINDOW = 300


class SignedWebhookVerifier:
    """ORACLE: HMAC over timestamp.payload, constant-time, with a replay window."""

    def __init__(self) -> None:
        self._secret = secrets.token_bytes(32)

    def sign(self, payload: str, timestamp: int) -> str:
        mac = hmac.HMAC(self._secret, hashes.SHA256())
        mac.update(f"{timestamp}.{payload}".encode())
        return mac.finalize().hex()

    def verify(self, payload: str, signature: str, timestamp: int, now: int) -> bool:
        if abs(now - timestamp) > _WINDOW:
            return False
        mac = hmac.HMAC(self._secret, hashes.SHA256())
        mac.update(f"{timestamp}.{payload}".encode())
        try:
            mac.verify(bytes.fromhex(signature))
            return True
        except (InvalidSignature, ValueError):
            return False


class UnverifiedWebhook:
    """BUGGY: act on any inbound webhook."""

    def sign(self, payload: str, timestamp: int) -> str:
        return "sig"

    def verify(self, payload: str, signature: str, timestamp: int, now: int) -> bool:
        return True  # BUG: no signature verification


def verifies_genuine_webhook(make_verifier: Callable[[], object]) -> bool:
    verifier = make_verifier()
    sig = verifier.sign("order.paid", 1000)
    return verifier.verify("order.paid", sig, 1000, 1000)


def accepts_forged_webhook(make_verifier: Callable[[], object]) -> bool:
    """True == an attacker payload with a bogus signature was acted on (the bug)."""
    verifier = make_verifier()
    return verifier.verify("order.refunded;amount=9999", "00" * 32, 1000, 1000)


def run_self_test() -> int:
    failures = 0
    if not verifies_genuine_webhook(SignedWebhookVerifier):
        failures += 1
        print("FAIL: oracle rejected a genuine signed webhook", file=sys.stderr)
    if accepts_forged_webhook(SignedWebhookVerifier):
        failures += 1
        print("FAIL: oracle accepted a forged webhook", file=sys.stderr)
    if not accepts_forged_webhook(UnverifiedWebhook):
        failures += 1  # the planted bug must be caught -- else vacuous green
        print("FAIL: unverified webhook forgery was NOT caught", file=sys.stderr)
    if failures:
        print(f"self-test: {failures} failure(s)", file=sys.stderr)
        return 1
    print("self-test: OK (HMAC rejects the forged webhook; unverified one accepts -- caught)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Webhook-signature harness")
    parser.add_argument("--self-test", action="store_true", help="run the planted-bug self-test")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help(sys.stderr)
        return 2
    return run_self_test()


if __name__ == "__main__":
    sys.exit(main())
