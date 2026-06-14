# DEP-TEST-KIT — common tasks. Everything runs through uv for a locked, reproducible env.

.PHONY: sync test test-int lint deptry audit selftest sbom all

sync:            ## provision the locked environment (all extras)
	uv sync --locked --all-extras

test:            ## fast lib lane (no Docker)
	uv run --frozen pytest -m "not integration" -q

test-int:        ## real-service lane (needs Docker)
	uv run --frozen pytest -m integration -q

lint:            ## ruff
	uv run ruff check .

deptry:          ## unused/missing dependency scan
	uv run deptry harnesses

audit:           ## OSV vulnerability audit of the locked graph
	uv audit --preview-features audit

selftest:        ## per-harness self-tests (lib)
	uv run --frozen python harnesses/lib/property_roundtrip_test_harness.py --self-test

sbom:            ## generate a CycloneDX SBOM
	uvx cyclonedx-py environment "$$(uv python find)" --output-format json -o sbom.cdx.json

all: sync lint deptry test selftest audit
