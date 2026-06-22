"""Proof: enforcing the PKCE verifier/challenge binding defeats code interception. The
no-PKCE server redeems an intercepted code with the wrong verifier; the PKCE server rejects it."""

from harnesses.lib import oauth_pkce_test_harness as h


def test_proof_no_pkce_accepts_intercepted_code() -> None:
    assert h.accepts_intercepted_code(h.NoPkceAuthServer) is True


def test_proof_pkce_rejects_intercepted_code() -> None:
    assert h.accepts_intercepted_code(h.PkceAuthServer) is False


def test_proof_pkce_allows_correct_verifier() -> None:
    assert h.exchanges_with_correct_verifier(h.PkceAuthServer) is True


# --- scenario coverage: the no-PKCE server redeems a code with the wrong verifier ---
def test_proof_nopkce_accepts_wrong_verifier() -> None:
    server, verifier = h._setup(h.NoPkceAuthServer)
    assert server.exchange("auth-code-xyz", "wrong-verifier") == "access-token"
