"""Fixtures for the integration lane (research T2 pattern).

A single session-scoped PostgreSQL container started with disk-safety disabled for
speed; a fresh autocommit=False connection per test whose teardown ROLLBACKs —
because DDL is transactional in PostgreSQL, the table and all rows vanish, giving
pristine isolation with no per-test container churn.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def postgres_container():
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer("postgres:16-alpine").with_command(
        "-c fsync=off -c synchronous_commit=off -c full_page_writes=off"
    )
    with container as pg:
        yield pg


@pytest.fixture()
def pg_conn(postgres_container):
    import psycopg

    # driver=None yields a libpq URL that psycopg (v3) accepts directly.
    conn = psycopg.connect(postgres_container.get_connection_url(driver=None), autocommit=False)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()
