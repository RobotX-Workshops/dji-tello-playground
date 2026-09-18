# Agent Instructions

Instructions for AI coding agents (Claude Code, CodeRabbit, etc.) working in this repository.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<optional scope>): <short imperative description>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

Examples:

- `feat: add color contour detection`
- `fix(example_exercises): preserve preset config fields when tuning trackbars`
- `docs: document HSV presets in object detection README`

## Pull requests

- Target `main`.
- Address reviewer and review-bot (e.g. CodeRabbit) comments before a PR is merge-ready, and resolve the threads once fixed.
- **Never merge.** The workflow's job ends when a PR is merge-ready (no conflicts, required checks green, all review threads resolved): report merge-readiness and a recommended merge order, then hand off to the user. Merging is always a human action. No agent may run `gh pr merge` or merge by any other means — regardless of how the request is phrased (e.g. "resolve all the PRs" means prepare + report, never merge).

## Safety

Exercises in `src/example_exercises/` can fly a real drone. When testing detection logic, prefer `DEBUG_MODE = True` (local webcam) or `NO_TAKEOFF = True` (drone camera, stays grounded) over actual flight.
