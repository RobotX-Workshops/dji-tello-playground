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

Caller may pass `BASE_REF` and `HEAD_REF` via env. Resolve `HEAD_REF` first —
`BASE_REF`, `BRANCH`, and the banner all derive from it, so a caller-supplied
`HEAD_REF` must not fall back to the current checkout:

```bash
HEAD_REF=${HEAD_REF:-HEAD}
git fetch origin main
BASE_REF=${BASE_REF:-$(git merge-base "$HEAD_REF" origin/main)}
BRANCH=$(git rev-parse --abbrev-ref "$HEAD_REF")
```

## Flow

### 1. Pre-flight

- Refuse to run on `main` — there's no PR concept.
- `origin main` was already fetched while resolving `BASE_REF` above, so
  the merge-base is fresh by the time this step runs.
- Show a one-line banner: `=== LOCAL ADVERSARIAL REVIEW: ${BRANCH}
  (BASE..HEAD = $(git rev-parse --short "$BASE_REF")..$(git rev-parse
  --short "$HEAD_REF")) ===`. (Resolve via `rev-parse` — substring
  slicing like `${HEAD_REF:0:7}` prints garbage for symbolic refs such
  as `HEAD` or `origin/main`.)

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
and follow it exactly. The diff under review (commit-to-working-tree form —
the implementer's edits from earlier iterations are deliberately left
uncommitted in this worktree, and a two-endpoint `${BASE_REF}..${HEAD_REF}`
diff would never show them):

  git diff ${BASE_REF}

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

If `blocking == 0` AND `nonblocking == 0` AND every SUSPECT finding in
this iteration already has a recorded implementer verdict in
`HISTORY.md`: **converged**. Print `=== CONVERGED at iteration
${ITER} ===`, jump to step 6.

If the blocking/nonblocking counts are zero but one or more SUSPECT
findings lack a verdict, do NOT settle yet — SUSPECT is advisory for
the counts, but it never skips the implementer's investigation. Run
step 5 so the implementer investigates each SUSPECT and records a
verdict. If that pass makes no code edits, treat the loop as converged
when it returns; if it does edit files, loop to step 3 as usual so the
reviewer sees the new diff.

If the reviewer's findings are byte-identical to the previous
iteration's findings: **stable disagreement**. Print the unresolved
list and stop with exit status 2 so a hook or wrapper surfaces it to
the user ("reviewer and implementer can't agree — review the report
and decide whether to bypass").

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
without convergence, print the outstanding findings and stop with exit
status 2. Do not loop forever — the user can inspect, decide, and push
anyway.

### 7. Settling the worktree back into the original branch

When converged:

1. In the worktree, collect the file list the implementer reported
   touching (the `FIXED <file:line>` lines in `HISTORY.md`), then
   delete `HISTORY.md` (it's loop scratch, not PR content). Stage
   exactly the reported files with `git add -- <file>...` — never
   `git add -A`. Then check for strays among **unstaged and untracked
   paths only** — the just-staged allowlisted files legitimately show
   as staged, so a bare `git status --porcelain` would false-positive
   on a successful fixup:

   ```bash
   strays=$(git diff --name-only; git ls-files --others --exclude-standard)
   ```

   If `strays` is non-empty, stop and surface the list to the user
   instead of staging more; stray agent artifacts must not ride into
   the commit.
2. If the worktree's index is non-empty, fold the loop's work into a
   single commit: `git commit --no-verify -m "fixup! adversarial review
   iteration loop"`. (`--no-verify` is intentional here — pre-commit
   hooks are about *intent*, this commit is a mechanical re-shape of
   the diff the user is about to push.)
3. Back in the main checkout, fast-forward `${BRANCH}` to the
   worktree's HEAD: `git fetch <worktree-path> HEAD:${BRANCH}` (or
   `git update-ref refs/heads/${BRANCH} <new-sha>` if the main
   checkout is on a different branch).
4. If the implementer made no edits in any iteration (clean pass on
   the first reviewer round), skip the fixup commit and the
   fast-forward — nothing to settle.
5. Print `=== LOCAL REVIEW PASSED ===`.

## Outputs

- Exit 0 → converged (or bypassed), branch fast-forwarded if edits were made.
- Exit 2 → unresolved findings (stable disagreement or iteration cap);
  the user decides whether to fix by hand or push anyway.
- Exit non-zero non-2 → setup error (no worktree, no `claude` binary,
  blocked-active-worktree, etc.).

## Bypass channels

- `CLAUDE_LOCAL_REVIEW=0` env — skill exits 0 immediately when set.
- `git push --no-verify` — git skips pre-push hooks entirely (there are
  none wired in this repo today, but the flag is a universal bypass).
- Caller may pass `LOCAL_REVIEW_MAX_ITER=N` to override the iteration cap.

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
