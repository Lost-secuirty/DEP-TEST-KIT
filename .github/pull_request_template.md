## What & why

<!-- What does this PR change, and why? Link the decision record if relevant. -->

## Changes

<!-- Notable changes by area/file. Call out anything sensitive: dependencies,
     uv.lock, CI, .github/, .claude/. -->

-

## Deviations from plan

<!-- Mandatory. Any mid-task change of approach vs. the stated plan. Write "None."
     explicitly if there were none — an untouched template is not an answer. -->

## Dependency impact

- [ ] No dependency change
- [ ] Added/removed a dependency (reason stated above; `uv.lock` regenerated)

## Risk area

- [ ] Docs only
- [ ] `lib/` harness (in-process)
- [ ] `integration/` harness (real service)
- [ ] Dependency / lockfile / CI
- [ ] Governance / `.claude/`

## Testing

- [ ] `uv run pytest -m "not integration"` passes
- [ ] `uv run pytest -m integration` passes (or n/a — no integration change)
- [ ] `uv run deptry harnesses` clean
- [ ] `uv audit` clean
- [ ] New harness ships a planted-bug **proof** test (not vacuous green)
