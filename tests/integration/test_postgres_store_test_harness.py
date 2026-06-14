import psycopg
import pytest

from harnesses.integration import postgres_store_test_harness as h

pytestmark = pytest.mark.integration


def test_unique_constraint_rejects_duplicate(pg_conn) -> None:
    store = h.UserStore(pg_conn)
    store.ensure_schema()
    store.add_user("a@example.com")
    with pytest.raises(psycopg.errors.UniqueViolation):
        store.add_user("a@example.com")


def test_distinct_emails_are_accepted(pg_conn) -> None:
    store = h.UserStore(pg_conn)
    store.ensure_schema()
    store.add_user("a@example.com")
    store.add_user("b@example.com")
    assert store.count() == 2
