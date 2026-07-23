---
name: local-pr-review
description: Run the adversarial Claude review locally in a git worktree before a push, looping reviewer ↔ implementer until consensus. Local counterpart of the claude-code-review GitHub workflow so findings surface before CI runner minutes are burned. Run as /local-pr-review against the current branch.
---

# local-pr-review

Mirror of [.github/workflows/claude-code-review.yml](../../../.github/workflows/claude-code-review.yml)
run locally, in an isolated git worktree, with the implementer agent in
the same session pushing back on weak findings and fixing real ones.
Loops until reviewer and implementer agree, then fast-forwards the
original branch and reports success. Non-convergence (stable
disagreement or the iteration cap) is always reported as a failure
with the outstanding findings — never as a pass.

## When to use

- Manually as `/local-pr-review` against the current branch, before
  pushing a branch that has (or is about to get) an open PR.
- This repo has no pre-push hook wiring; invocation is always manual.

## Inputs

Caller may pass `BASE_REF` and `HEAD_REF` via env. If absent:

```bash
BASE_REF=${BASE_REF:-$(git merge-base HEAD origin/main)}
HEAD_REF=${HEAD_REF:-HEAD}
BRANCH=$(git rev-parse --abbrev-ref HEAD)
```

## Flow

### 1. Pre-flight

- Refuse to run on `main` — there's no PR concept.
- `git fetch origin main` so the merge-base is fresh.
- Show a one-line banner: `=== LOCAL ADVERSARIAL REVIEW: ${BRANCH}
  (BASE..HEAD = ${BASE_REF:0:7}..${HEAD_REF:0:7}) ===`.

### 2. Worktree

Each `Agent` call uses `isolation: "worktree"`. The worktree is
checked out to `HEAD_REF`. No manual `git worktree add` from the skill.

If the current branch is already checked out in another worktree,
abort with `blocked-active-worktree` so the user resolves by hand.
`--porcelain` output pairs each `worktree <path>` line with its
`branch` line, so parse the pairs and compare paths — a bare grep for
the branch line can't tell which worktree it belongs to:

```bash
current=$(git rev-parse --show-toplevel)
other=$(git worktree list --porcelain \
  | awk -v ref="branch refs/heads/${BRANCH}" \
      '/^worktree /{p=substr($0,10)} $0==ref{print p}' \
  | grep -vFx "$current" || true)
[ -n "$other" ] && echo "blocked-active-worktree: $other" && stop
```

### 3. Reviewer pass

Spawn a `claude` subagent (`subagent_type: claude`, `isolation:
"worktree"`, **NOT** `run_in_background` — the loop is foreground so
the user sees each turn live). Prompt body:

```text
You are running inside an isolated git worktree off branch ${BRANCH}.
Read the adversarial reviewer prompt at .claude/prompts/adversarial_reviewer.md
and follow it exactly. The diff under review:

  git diff ${BASE_REF}..${HEAD_REF}

Iteration: ${ITER} of max ${MAX_ITER}.
Previous iterations' findings + implementer verdicts are in HISTORY.md
at the repo root of the worktree (read it before starting if it
exists — do not re-flag items already pushed back on with citation
unless the implementer's citation is itself wrong).

Output the review verbatim in the format the prompt file specifies.
Do NOT post to GitHub — this is a local run. Print to stdout only.
```

After the agent returns, append its output to `HISTORY.md` in the
worktree under `## Reviewer iteration ${ITER}`. Print the banner
`=== ITERATION ${ITER} — REVIEWER ===` followed by the agent's full
output so the user can read it live.

### 4. Convergence check

Parse the `bot-review-marker` HTML comment:

```regex
blocking=(\d+) nonblocking=(\d+) suspect=(\d+)
```

If `blocking == 0` AND `nonblocking == 0` (suspect items are advisory):
**converged**. Print `=== CONVERGED at iteration ${ITER} ===`, jump to
step 6.

If the reviewer's findings are byte-identical to the previous
iteration's findings: **stable disagreement**. Print the unresolved
list and stop with a clear report so the user can review and decide.

### 5. Implementer pass

Spawn a second `claude` subagent in the same worktree. Prompt body:

```text
You are running inside an isolated git worktree off branch ${BRANCH}.
Read the adversarial implementer prompt at
.claude/prompts/adversarial_implementer.md and follow it exactly.

The reviewer's findings for this iteration are in HISTORY.md under
"## Reviewer iteration ${ITER}". Walk each finding, decide
fix/already-fixed/push-back per the prompt's verdict table, and edit
files in this worktree for every "fix" verdict. Do NOT commit — the
orchestrator will amend the loop's work into a single commit at the
end.

Output the verdict report verbatim and append it to HISTORY.md under
"## Implementer iteration ${ITER}". Print to stdout for the user.
```

Print `=== ITERATION ${ITER} — IMPLEMENTER ===` banner. Increment
`ITER` and loop to step 3.

### 6. Hard cap

`MAX_ITER = 5` (override with `LOCAL_REVIEW_MAX_ITER=N`). If reached
without convergence, print the outstanding findings and stop. Do not
loop forever — the user can inspect, decide, and push anyway.

### 7. Settling the worktree back into the original branch

When converged:

1. In the worktree, collect the file list the implementer reported
   touching (the `FIXED <file:line>` lines in `HISTORY.md`), then
   delete `HISTORY.md` (it's loop scratch, not PR content). Stage
   exactly the reported files with `git add -- <file>...` — never
   `git add -A`. If `git status --porcelain` still shows modified or
   untracked files after that, stop and surface them to the user
   instead of staging; stray agent artifacts must not ride into the
   commit.
2. If the worktree's index is non-empty, fold the loop's work into a
   single commit: `git commit -m "fixup! adversarial review iteration
   loop"` (the user squashes it when merging).
3. Back in the main checkout, fast-forward `${BRANCH}` to the
   worktree's HEAD: `git fetch <worktree-path> HEAD:${BRANCH}` (or
   `git update-ref refs/heads/${BRANCH} <new-sha>` if the main
   checkout is on a different branch).
4. If the implementer made no edits in any iteration (clean pass on
   the first reviewer round), skip the fixup commit and the
   fast-forward — nothing to settle.
5. Print `=== LOCAL REVIEW PASSED ===`.

## Outputs

- Converged → report "passed", branch fast-forwarded if edits were made.
- Stable disagreement or iteration cap → report the outstanding
  findings; the user decides whether to fix by hand or push anyway.

## Ground rules

- **Foreground only.** Never `run_in_background`. The user must see
  each iteration as it happens.
- **The skill does not push.** It leaves the branch ready; the user
  (or /resolve-my-prs) pushes.
- **The skill does not post to GitHub.** The matching workflow run
  will still fire on the actual push; this is local-only.
- **One commit max.** Don't litter the branch with per-iteration
  commits — fold all implementer edits into one fixup at the end.
- **Honour the standing conventions in [.claude/prompts/adversarial_implementer.md](../../prompts/adversarial_implementer.md).**
  Reviewer suggestions that contradict them must be pushed back, not
  capitulated to.

## See also

- [.claude/prompts/adversarial_reviewer.md](../../prompts/adversarial_reviewer.md) — reviewer prompt body (single source of truth)
- [.claude/prompts/adversarial_implementer.md](../../prompts/adversarial_implementer.md) — implementer prompt body
- [resolve-my-prs](../resolve-my-prs/SKILL.md) — bulk PR resolution loop that this skill complements
- [.github/workflows/claude-code-review.yml](../../../.github/workflows/claude-code-review.yml) — the CI workflow this mirrors
