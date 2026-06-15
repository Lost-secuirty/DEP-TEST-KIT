#!/usr/bin/env python3
"""Hallucinated-dependency detection harness (live installed-version resolution; packaging).

WHY:   LLM-generated manifests pin packages to versions that do not exist — the Sonatype
       "AI agents recommend non-existent / yanked / typosquatted package versions" supply-chain
       class, the version-level sibling of the attribute-level `hallucinated_symbol`. A naive
       gate ("is the package name known / installed?") passes, because the *package* is real —
       only the pinned *version* is hallucinated. `uv audit` catches versions with a KNOWN CVE,
       not versions that were never published; the only ground truth for "does this exact
       version exist?" is resolution against a concrete, locked environment.

HOW:   Parse each `name==version` pin with `packaging` (PEP 440), then resolve it against the
       LIVE installed distribution set via `importlib.metadata`: a pin is real iff the package
       is installed AND the pinned specifier actually matches the installed version. The ORACLE
       `hallucinated_pins` flags a pin that does not resolve — a hallucinated VERSION of a real
       package (`pydantic==99.99.99`) or an entirely absent package (a typosquat). The BUGGY
       `buggy_hallucinated_pins` checks only that the package NAME is installed and ignores the
       version, so a hallucinated version of a genuinely-installed package slips straight through.

WHERE: lib/ — dependency-backed (`packaging` for PEP 440 parsing/comparison, added to the `lib`
       extra) and fully in-process; it resolves against the real locked environment, nothing is
       mocked. Real pins are built from the live installed versions so the harness is robust to
       `uv.lock` bumps (it never hard-codes a version that a lock refresh would invalidate).

Self-test:
  python harnesses/lib/hallucinated_dependency_test_harness.py --self-test
"""

from __future__ import annotations

import argparse
import sys
from importlib import metadata

from packaging.requirements import Requirement  # the dependency: PEP 440 parsing/comparison

# Symbol the vacuous-green meta-gate (tools/vacuity_gate.py) neuters to confirm teeth.
VACUITY_TARGETS = ["pin_resolves"]

# Packages guaranteed present in the `lib` extra; real pins are built from their LIVE versions
# so a lock refresh can never make this harness fail on a stale hard-coded version.
_REAL_PKGS = ("pydantic", "packaging", "hypothesis")
REAL_PINS = [f"{pkg}=={metadata.version(pkg)}" for pkg in _REAL_PKGS]

# A hallucinated VERSION of a REAL package (the case the naive name-only check misses), plus an
# entirely absent package (a typosquat the naive check happens to catch too).
HALLUCINATED_VERSION_OF_REAL_PKG = "pydantic==99.99.99"
HALLUCINATED_PINS = [HALLUCINATED_VERSION_OF_REAL_PKG, "nonexistent-typosquat-pkg-xyz==1.0.0"]


def pin_resolves(pin: str) -> bool:
    """ORACLE primitive: does `pin` (`name==version`) resolve against the live installed
    environment — the package is installed AND the pinned specifier matches what is installed?"""
    req = Requirement(pin)
    try:
        installed = metadata.version(req.name)
    except metadata.PackageNotFoundError:
        return False  # package not installed at all (absent / typosquat / hallucinated name)
    return req.specifier.contains(installed, prereleases=True)


def hallucinated_pins(pins: list[str]) -> list[str]:
    """ORACLE: the pins that do NOT resolve against the live environment (hallucinated)."""
    return sorted({pin for pin in pins if not pin_resolves(pin)})


def buggy_hallucinated_pins(pins: list[str]) -> list[str]:
    """BUGGY: checks only that the package NAME is installed and ignores the pinned version, so a
    hallucinated VERSION of a genuinely-installed package (pydantic==99.99.99) is invisible."""
    bad = []
    for pin in pins:
        name = Requirement(pin).name
        try:
            metadata.version(name)
        except metadata.PackageNotFoundError:
            bad.append(pin)
    return sorted(bad)


def run_self_test() -> int:
    failures = 0

    if hallucinated_pins(REAL_PINS):
        failures += 1
        print("FAIL: oracle flagged a real, installed pin (false positive)", file=sys.stderr)

    oracle_found = set(hallucinated_pins(HALLUCINATED_PINS))
    if oracle_found != set(HALLUCINATED_PINS):
        failures += 1
        print("FAIL: oracle missed a hallucinated pin", file=sys.stderr)

    # The teeth gap: the naive checker must MISS the hallucinated version of a real package
    # (it only checks the name). It legitimately still catches the entirely-absent package.
    buggy_found = set(buggy_hallucinated_pins(HALLUCINATED_PINS))
    if HALLUCINATED_VERSION_OF_REAL_PKG in buggy_found:
        failures += 1
        print("FAIL: naive checker flagged the hallucinated version — no teeth gap", file=sys.stderr)

    if failures:
        print(f"self-test: {failures} failure(s)", file=sys.stderr)
        return 1
    print("self-test: OK (oracle catches a hallucinated version of a real package the naive "
          "name-only check misses)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hallucinated-dependency detection harness")
    parser.add_argument("--self-test", action="store_true", help="run the planted-bug self-test")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help(sys.stderr)
        return 2
    return run_self_test()


if __name__ == "__main__":
    sys.exit(main())
