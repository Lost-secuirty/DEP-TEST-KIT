"""Proof: only a real database reveals the missing-constraint bug.

The buggy store (UNIQUE dropped from its DDL) silently accepts a duplicate against
real PostgreSQL — count becomes 2 — while the correct store rejects it. A mock
would have caught neither, which is the entire point of the integration lane.
"""

import psycopg
import pytest

from harnesses.integration import postgres_store_test_harness as h

pytestmark = pytest.mark.integration


def test_proof_buggy_store_allows_duplicate(pg_conn) -> None:
    store = h.BuggyUserStore(pg_conn)
    store.ensure_schema()
    store.add_user("dup@example.com")
    store.add_user("dup@example.com")
    assert store.count() == 2  # the planted bug, made visible by a real DB


def test_proof_correct_store_blocks_what_buggy_allows(pg_conn) -> None:
    store = h.UserStore(pg_conn)
    store.ensure_schema()
    store.add_user("dup@example.com")
    with pytest.raises(psycopg.errors.UniqueViolation):
        store.add_user("dup@example.com")
