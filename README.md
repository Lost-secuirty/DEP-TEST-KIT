# DEP-TEST-KIT

Dependency-backed and real-service **integration** test harnesses — the non-stdlib
companion to [`testing-kits`](https://github.com/lostsoulfs/testing-kits).

`testing-kits` is deliberately zero-dependency, pure-stdlib. This repo is the
opposite by design: small, inspectable harnesses that demonstrate a real failure
class **using the right third-party tool or a real ephemeral service** — pinned,
locked, and audited. Same shape as testing-kits; different dependency rule.

## Two flavors

| Flavor | Path | Runs | Needs |
|--------|------|------|-------|
| **lib** | `harnesses/lib/` | in-process | a pinned library (e.g. Hypothesis) |
| **integration** | `harnesses/integration/` | real ephemeral service | Docker + testcontainers |

## The harness shape (every file explains itself)

One self-contained harness + a paired test + a planted-bug **proof** test. Every
harness documents, in its module docstring:

- **WHY** — the failure class it catches that the stdlib / example-based tests miss.
- **HOW** — the dependency or service, the correct **oracle**, and the intentional
  **buggy** implementation it proves it catches.
- **WHERE** — which flavor, and the dependency it adds to the matching `pyproject` extra.

The proof test is non-negotiable: it asserts the buggy impl is caught and the oracle
passes. A test that can pass while inert is *vacuous green* — the bug class this repo
exists to prevent.

## Seed harnesses

- `lib/property_roundtrip_test_harness.py` — Hypothesis round-trip property; shrinks a
  planted single-run-dropping decoder to a 2-char counterexample.
- `integration/postgres_store_test_harness.py` — asserts a real `UNIQUE` constraint on
  an ephemeral PostgreSQL; proves a store that forgot the constraint silently writes
  duplicates (a mock would catch neither).

## Running

```bash
uv sync --all-extras                 # provision a locked, reproducible env
uv run pytest -m "not integration"   # fast lib lane (no Docker)
uv run pytest -m integration         # real-service lane (needs Docker)
uv run python harnesses/lib/property_roundtrip_test_harness.py --self-test
```

## Dependency policy

Dependencies are allowed, but **pinned, locked (`uv.lock`), and audited**. CI fails on
unlocked, unused, or vulnerable dependencies (`uv sync --locked` → `deptry` → `uv audit`
→ `uv run --frozen`). A dependency is added to `pyproject.toml` only when a harness
actually imports it. See `docs/decisions/0001-stack-decisions.md` for why each tool was
chosen.

See `AGENTS.md` for the working contract and `HARNESS_ROADMAP.md` for what's next.
