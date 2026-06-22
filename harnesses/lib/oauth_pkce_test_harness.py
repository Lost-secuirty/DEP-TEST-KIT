#!/usr/bin/env python3
"""OAuth 2.1 PKCE binding harness (cryptography SHA-256).

OWASP Top 10:2025 A07 Authentication Failures. As of Jan 2026 (OAuth 2.1 / RFC 9700), PKCE
is MANDATORY for every authorization-code client -- public clients, mobile apps, and AI
agents/MCP servers alike. Without it, an intercepted authorization code is redeemable by
anyone.

WHY: PKCE binds the authorization code to a secret the legitimate client holds: the client
sends `code_challenge = BASE64URL(SHA256(code_verifier))` up front, and must present the
matching `code_verifier` at token exchange. A test that exchanges a code with the RIGHT
verifier passes whether or not the server actually checks PKCE -- the gap only shows when an
attacker presents the intercepted code WITHOUT the verifier. Only enforcing the
challenge/verifier binding catches it.

HOW: `PkceAuthServer` is the ORACLE -- at exchange it recomputes `S256(verifier)` and
constant-time-compares it to the stored challenge, rejecting a mismatch. `NoPkceAuthServer`
is the planted defect -- it redeems the code without checking the verifier.
`accepts_intercepted_code` redeems a stolen code with a wrong verifier: the oracle rejects,
the no-PKCE server issues a token.

WHERE: lib/ -- in-process, deterministic. Uses `cryptography` (SHA-256) + stdlib base64/hmac.

Self-test:
    python harnesses/lib/oauth_pkce_test_harness.py --self-test
"""

from __future__ import annotations

import argparse
import base64
import hmac
import sys
from typing import Callable, Tuple

from cryptography.hazmat.primitives import hashes

# Symbol the vacuous-green meta-gate (tools/vacuity_gate.py) neuters to confirm teeth.
VACUITY_TARGETS = ["accepts_intercepted_code"]

DOSSIER = {
    "name": "oauth_pkce",
    "path": "harnesses/lib/oauth_pkce_test_harness.py",
    "flavor": "lib",
    "dependency": "cryptography (SHA-256)",
    "standard": "OWASP Top 10:2025 A07 + OAuth 2.1 / RFC 9700 (2026): PKCE mandatory",
    "failure_class": (
        "Authorization-code exchange without enforcing the PKCE verifier/challenge binding"
    ),
    "oracle": (
        "PkceAuthServer.exchange — require S256(verifier) == stored challenge (constant-time)"
    ),
    "buggy": "NoPkceAuthServer.exchange — redeem the code without checking the verifier",
    "planted_mutant": (
        "redeem an intercepted code with a wrong verifier; oracle rejects, no-PKCE issues a token"
    ),
    "proof_file": "tests/lib/test_oauth_pkce_proof.py",
    "vacuity_targets": ["accepts_intercepted_code"],
    "commands": ["python harnesses/lib/oauth_pkce_test_harness.py --self-test"],
    "known_limits": (
        "models the S256 binding; not a full RFC 9700 BCP review (nonce, redirect_uri, etc.)"
    ),
    "related": ["keycloak_oidc", "jwt_audience_binding", "agent_join_replay"],
}


def _s256(verifier: str) -> str:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(verifier.encode())
    return base64.urlsafe_b64encode(digest.finalize()).rstrip(b"=").decode()


class PkceAuthServer:
    """ORACLE: enforce the PKCE challenge/verifier binding at token exchange."""

    def __init__(self) -> None:
        self._codes: dict = {}

    def authorize(self, code: str, code_challenge: str) -> None:
        self._codes[code] = code_challenge

    def exchange(self, code: str, code_verifier: str) -> str:
        challenge = self._codes.get(code)
        if challenge is None:
            raise ValueError("unknown authorization code")
        if not hmac.compare_digest(_s256(code_verifier), challenge):
            raise ValueError("PKCE verifier does not match the stored challenge")
        del self._codes[code]
        return "access-token"


class NoPkceAuthServer:
    """BUGGY: redeem the code without verifying the PKCE verifier."""

    def __init__(self) -> None:
        self._codes: dict = {}

    def authorize(self, code: str, code_challenge: str) -> None:
        self._codes[code] = code_challenge

    def exchange(self, code: str, code_verifier: str) -> str:
        if code not in self._codes:
            raise ValueError("unknown authorization code")
        del self._codes[code]
        return "access-token"  # BUG: the verifier is never checked


def _setup(make_server: Callable[[], object]) -> Tuple[object, str]:
    server = make_server()
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    server.authorize("auth-code-xyz", _s256(verifier))
    return server, verifier


def exchanges_with_correct_verifier(make_server: Callable[[], object]) -> bool:
    server, verifier = _setup(make_server)
    try:
        return server.exchange("auth-code-xyz", verifier) == "access-token"
    except Exception:
        return False


def accepts_intercepted_code(make_server: Callable[[], object]) -> bool:
    """An attacker stole the code but not the verifier. True == a token was issued anyway
    (the bug); False == rejected on the PKCE check."""
    server, _verifier = _setup(make_server)
    try:
        server.exchange("auth-code-xyz", "attacker-does-not-know-the-verifier")
        return True   # redeemed an intercepted code without the verifier
    except Exception:
        return False  # PKCE binding rejected it


def run_self_test() -> int:
    failures = 0
    if not exchanges_with_correct_verifier(PkceAuthServer):
        failures += 1
        print(
            "FAIL: oracle rejected a legitimate exchange with the correct verifier",
            file=sys.stderr,
        )
    if accepts_intercepted_code(PkceAuthServer):
        failures += 1
        print("FAIL: oracle redeemed an intercepted code without the verifier", file=sys.stderr)
    if not accepts_intercepted_code(NoPkceAuthServer):
        failures += 1  # the planted bug must be caught -- else vacuous green
        print("FAIL: no-PKCE server was NOT caught redeeming an intercepted code", file=sys.stderr)
    if failures:
        print(f"self-test: {failures} failure(s)", file=sys.stderr)
        return 1
    print("self-test: OK (PKCE server rejects an intercepted code; no-PKCE server caught)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OAuth 2.1 PKCE binding harness")
    parser.add_argument("--self-test", action="store_true", help="run the planted-bug self-test")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help(sys.stderr)
        return 2
    return run_self_test()


if __name__ == "__main__":
    sys.exit(main())
