# Agent Instructions

Instructions for AI coding agents (Claude Code, CodeRabbit, etc.) working in this repository.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <short imperative description>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

Examples:

- `feat: add color contour detection`
- `fix(example_exercises): preserve preset config fields when tuning trackbars`
- `docs: document HSV presets in object detection README`

## Pull requests

- Target `main`.
- Address reviewer and review-bot (e.g. CodeRabbit) comments before merging, and resolve the threads once fixed.

## Safety

Exercises in `src/example_exercises/` can fly a real drone. When testing detection logic, prefer `DEBUG_MODE = True` (local webcam) or `NO_TAKEOFF = True` (drone camera, stays grounded) over actual flight.
