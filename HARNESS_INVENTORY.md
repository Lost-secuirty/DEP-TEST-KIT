# Harness Inventory

**Total: 2 seed harnesses** (1 lib, 1 integration). This repo grows in batches of ≤6;
see `HARNESS_ROADMAP.md` for what's next. Every harness ships a paired test and a
planted-bug **proof** test, and documents WHY / HOW / WHERE in its module docstring.

## lib (dependency-backed, in-process)

### property_roundtrip — Hypothesis round-trip property
- **File:** `harnesses/lib/property_roundtrip_test_harness.py`
- **Tests:** `tests/lib/test_property_roundtrip_test_harness.py` (+ `_proof.py`)
- **Dep:** `hypothesis`
- **Why:** example-based tests only check inputs a human imagined; a run-length
  encode→decode round-trip can pass on `"aaa"` yet fail on `"ab"`. Hypothesis
  generates thousands of inputs and **shrinks** a failure to the minimal case.
- **Proof:** a decoder that drops count-1 runs is falsified and shrunk to a 2-char
  counterexample; the oracle holds.

## integration (real ephemeral service, needs Docker)

### postgres_store — real UNIQUE constraint on ephemeral PostgreSQL
- **File:** `harnesses/integration/postgres_store_test_harness.py`
- **Tests:** `tests/integration/test_postgres_store_test_harness.py` (+ `_proof.py`),
  fixtures in `tests/integration/conftest.py`
- **Deps:** `testcontainers`, `psycopg[binary]`
- **Why:** a mock cannot enforce a real schema. A store that "dedupes" via a UNIQUE
  constraint passes every mock test and still writes duplicates if the constraint
  was never declared. Only a real database reveals it.
- **How:** session-scoped container started with `fsync=off` (research T2 speed
  pattern); `autocommit=False` connection per test with a teardown ROLLBACK for
  pristine, near-zero-latency isolation.
- **Proof:** the buggy store (UNIQUE dropped from its DDL) writes a duplicate against
  real PostgreSQL (count == 2); the correct store raises `UniqueViolation`.

## Convention
See `template/harness_template.py` for the shape and `docs/decisions/0001-stack-decisions.md`
for why each dependency/tool was chosen.
