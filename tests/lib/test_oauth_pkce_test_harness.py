"""Oracle + CLI-contract test for oauth_pkce (pairs with its proof file).

Two-file convention: this asserts the secure path and the runnable CLI contract;
test_oauth_pkce_proof.py asserts the planted bug is caught (the teeth).
"""

from harnesses.lib import oauth_pkce_test_harness as h


def test_self_test_green() -> None:
    assert h.run_self_test() == 0


def test_cli_no_args_returns_2() -> None:
    assert h.main([]) == 2


def test_cli_self_test_returns_0() -> None:
    assert h.main(["--self-test"]) == 0


def test_oracle_happy_path() -> None:
    assert h.exchanges_with_correct_verifier(h.PkceAuthServer) is True


# --- scenario coverage: the PKCE server rejects wrong-verifier / unknown-code / replay ---
def _exchange_ok(server, code, verifier):
    try:
        return server.exchange(code, verifier) == "access-token"
    except Exception:
        return False


def test_oracle_rejects_wrong_verifier() -> None:
    server, verifier = h._setup(h.PkceAuthServer)
    assert _exchange_ok(server, "auth-code-xyz", "wrong-verifier") is False


def test_oracle_rejects_unknown_code() -> None:
    server, verifier = h._setup(h.PkceAuthServer)
    assert _exchange_ok(server, "no-such-code", verifier) is False


def test_oracle_rejects_code_replay() -> None:
    server, verifier = h._setup(h.PkceAuthServer)
    assert _exchange_ok(server, "auth-code-xyz", verifier) is True
    assert _exchange_ok(server, "auth-code-xyz", verifier) is False


# --- second pass: a second independent code/verifier exchange works ---
def test_oracle_supports_a_second_independent_exchange() -> None:
    server, verifier = h._setup(h.PkceAuthServer)
    server.authorize("code-2", h._s256("verifier-2"))
    assert _exchange_ok(server, "code-2", "verifier-2") is True
    assert _exchange_ok(server, "auth-code-xyz", verifier) is True


import pytest  # noqa: E402


@pytest.mark.parametrize("verifier", [
    "wrong-verifier", "", "AAAA", "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXx",
])
def test_oracle_rejects_wrong_verifier_corpus(verifier) -> None:
    server, _real = h._setup(h.PkceAuthServer)
    assert _exchange_ok(server, "auth-code-xyz", verifier) is False, verifier


@pytest.mark.parametrize("code", ["nope", "", "auth-code-xy", "AUTH-CODE-XYZ"])
def test_oracle_rejects_unknown_code_corpus(code) -> None:
    server, verifier = h._setup(h.PkceAuthServer)
    assert _exchange_ok(server, code, verifier) is False, code


# === our own / batch 2 (original) ===
# Adeyemi (whimsical/psych): a failed knock does not burn the door -- a wrong-verifier attempt
# raises but leaves the code unspent, so the legitimate client can still redeem it.
def test_oracle_failed_exchange_does_not_consume_code() -> None:
    server, verifier = h._setup(h.PkceAuthServer)
    try:
        server.exchange("auth-code-xyz", "attacker-does-not-know-the-verifier")
        burned_early = True
    except Exception:
        burned_early = False
    assert burned_early is False
    assert server.exchange("auth-code-xyz", verifier) == "access-token"


# Brandt (absurd/psych): the public challenge is not the verifier -- presenting the visible
# code_challenge as if it were the secret (a plain-method downgrade) does not satisfy S256.
def test_oracle_challenge_is_not_the_verifier() -> None:
    server, verifier = h._setup(h.PkceAuthServer)
    challenge = h._s256(verifier)  # the attacker can see this; it is sent in the clear
    try:
        server.exchange("auth-code-xyz", challenge)
        downgraded = True
    except Exception:
        downgraded = False
    assert downgraded is False
