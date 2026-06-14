"""Proof: a real Keycloak (real JWKS, real RS256 tokens) exposes the difference
between verifying and merely decoding. The oracle rejects a forged token; the
buggy verifier (verify_signature=False) accepts it."""

import pytest

from harnesses.integration import keycloak_oidc_test_harness as h

pytestmark = pytest.mark.integration


def test_proof_oracle_rejects_forged(keycloak_oidc) -> None:
    oracle = h.TokenVerifier(keycloak_oidc["jwks_url"], keycloak_oidc["issuer"],
                             keycloak_oidc["audience"])
    assert h.accepts_token(oracle, keycloak_oidc["forged_token"]) is False


def test_proof_buggy_accepts_forged(keycloak_oidc) -> None:
    buggy = h.BuggyTokenVerifier(keycloak_oidc["jwks_url"], keycloak_oidc["issuer"],
                                 keycloak_oidc["audience"])
    assert h.accepts_token(buggy, keycloak_oidc["forged_token"]) is True


def test_proof_oracle_accepts_valid(keycloak_oidc) -> None:
    # Without this, an oracle that rejected *everything* would still pass the forged-token
    # proofs; assert it accepts the genuine RS256 token so the rejection is real verification.
    oracle = h.TokenVerifier(keycloak_oidc["jwks_url"], keycloak_oidc["issuer"],
                             keycloak_oidc["audience"])
    assert h.accepts_token(oracle, keycloak_oidc["valid_token"]) is True
