#!/usr/bin/env python3
"""PostgreSQL store integration test harness (testcontainers).

WHY:   A mocked database cannot enforce a real schema. A store that "deduplicates"
       users by relying on a UNIQUE constraint will pass every mock-backed test and
       still write duplicate rows in production if the constraint was never actually
       declared. Only a real database reveals the difference. This harness asserts
       the constraint against an ephemeral PostgreSQL — the failure class mocks miss.

HOW:   `UserStore` declares `email TEXT UNIQUE`; a second insert of the same email
       raises `UniqueViolation`. `BuggyUserStore` ships the SAME code but omits
       UNIQUE from its DDL — the exact "forgot the constraint" defect. The proof
       test shows the real database silently accepts the duplicate for the buggy
       store (count == 2) while rejecting it for the correct one. A mock would have
       caught neither.

WHERE: integration/ — needs a real ephemeral service via Docker. Adds
       `testcontainers` and `psycopg[binary]` to the `integration` extra.
       Isolation follows the 2026 pattern (research T2): one session-scoped
       container started with `fsync=off` for speed, an `autocommit=False`
       connection per test, and a teardown ROLLBACK that discards the (transactional)
       DDL and rows — pristine state with near-zero latency. Fixtures live in
       `tests/integration/conftest.py`.

Self-test:
  python harnesses/integration/postgres_store_test_harness.py --self-test
  (deferred: the real proof runs under `pytest -m integration`, which needs Docker)
"""

from __future__ import annotations

import argparse
import shutil
import sys

CORRECT_DDL = "CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL)"
# BUGGY: the UNIQUE constraint was dropped — only a real database exposes this.
BUGGY_DDL = "CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT NOT NULL)"


class UserStore:
    ddl = CORRECT_DDL

    def __init__(self, conn) -> None:
        # conn is a psycopg (v3) connection, injected by the test fixtures.
        self.conn = conn

    def ensure_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(self.ddl)

    def add_user(self, email: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO users (email) VALUES (%s) RETURNING id", (email,))
            return cur.fetchone()[0]

    def count(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM users")
            return cur.fetchone()[0]


class BuggyUserStore(UserStore):
    """Identical store, but the DDL forgot UNIQUE — the planted bug."""

    ddl = BUGGY_DDL


def run_self_test() -> int:
    have_docker = shutil.which("docker") is not None
    print(
        "self-test: DEFERRED -- this is an integration harness. "
        "Run `pytest -m integration` (needs Docker). "
        f"docker on PATH: {have_docker}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PostgreSQL store integration harness")
    parser.add_argument("--self-test", action="store_true")
    parser.parse_args(argv)
    return run_self_test()


if __name__ == "__main__":
    sys.exit(main())
