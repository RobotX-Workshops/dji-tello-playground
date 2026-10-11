# Agent-Agnostic PR Resolution Workflow

This document is the canonical automation contract for resolving PRs in this
repo. It is intentionally independent of Claude, Codex, or any other specific
agent runtime. Tool-specific skills and commands should be thin adapters around
this file plus [AGENTS.md](../../AGENTS.md).

## Goals

- Resolve review comments on open PRs authored by the authenticated GitHub user.
- Preserve the repo's safety gates: the local adversarial review loop,
  concurrent-push protection, review-thread replies, and CI verification.
- Keep local user work isolated by using dedicated git worktrees.
- Allow multiple PRs to be processed concurrently when the active agent runtime
  supports safe delegation.
- **Never merge.** The workflow's job ends when a PR is merge-ready (no
  conflicts, required checks green, all review threads resolved): report
  merge-readiness and a recommended merge order, then hand off to the
  user. Merging is always a human action. No agent may run `gh pr merge`
  or merge by any other means — regardless of how the request is phrased
  (e.g. "resolve all the PRs" means prepare + report, never merge).

## Adapter Contract

An adapter is the small tool-specific layer that maps this workflow onto an
agent runtime. Examples include Claude slash-command skills, Codex sub-agents,
or a human-run shell checklist.

Adapters must:

- Treat [AGENTS.md](../../AGENTS.md) as the command source of truth.
- Use this document for orchestration semantics.
- Keep provider-specific language, model names, session behavior, and tool
  syntax out of AGENTS.md.
- Prefer a fresh worktree per PR and skip PRs whose branch is already checked
  out elsewhere.
- Never bypass checks, disable tests, use plain `--force`, or create token files.

Adapters may:

- Process PRs sequentially if they do not support safe background delegation.
- Process up to 4 PRs concurrently if they can isolate worktrees and report
  per-PR outcomes independently.
- Add local convenience commands, as long as the command behavior still follows
  AGENTS.md.

## Single-PR Flow

Use this flow for a named PR number or PR URL.

1. Run `gh auth status`.
2. Determine the authenticated login with `gh api user -q .login`.
3. Fetch PR metadata with `gh pr view` and verify:
   - `state` is `OPEN`.
   - `author.login` matches the authenticated login.
   - `isDraft` is false unless the user explicitly asked to process drafts.
4. Fetch `origin/main`.
5. Check `git worktree list --porcelain`; if the PR branch is already checked
   out in another worktree, return `blocked-active-worktree`.
6. Create or enter an isolated worktree for the PR.
7. Fetch the PR branch and capture the starting remote SHA before local edits:

   ```bash
   git fetch origin "${BRANCH}"
   STARTING_REMOTE_SHA=$(git rev-parse "origin/${BRANCH}")
   git checkout -B "local-${PR_NUM}" "origin/${BRANCH}"
   git rebase origin/main
   ```

8. Fetch all review channels per AGENTS.md:
   - inline PR comments,
   - PR review bodies,
   - issue comments,
   - GraphQL review-thread resolution state.
9. Assess every finding critically against the cited code and canonical docs.
10. Fix valid defects, push back on invalid findings with evidence, and reply
    on every finding before resolving any thread.
11. Run the local adversarial review before pushing: invoke the
    `/local-pr-review` skill (see
    [.claude/skills/local-pr-review/SKILL.md](../../.claude/skills/local-pr-review/SKILL.md))
    manually against the branch — this repo has no pre-push hook wiring, so
    nothing routes `git push` through it automatically. Let that loop run to
    convergence rather than skipping it.
12. Before any `--force-with-lease` push, re-fetch `origin/${BRANCH}` and
    confirm it still matches `STARTING_REMOTE_SHA`; if it has moved, someone
    else pushed concurrently — stop and return `blocked-concurrent-push`
    rather than clobbering it. (This repo's AGENTS.md does not define a
    separate concurrent-push gate; `--force-with-lease` plus this manual
    check is the whole mechanism.)
13. Push with `git push --force-with-lease origin "HEAD:${BRANCH}"`.
14. Return a structured report (one block per PR) with these fields:

    ```text
    PR: #<number>
    Outcome: <one of the Outcomes below>
    SHA: <pushed sha or '-'>
    Worktree: <absolute worktree path>
    Local branches: <comma-separated local branch names, or '-'>
    Resolved threads: <thread URLs/IDs, or '-'>
    Push-backs: <one line per intentionally rejected finding with its reason, or '-'>
    Notes: <one line for the orchestrator's merge-order decision>
    ```

## Bulk PR Flow

Use this flow when the user asks to clear all of their open PRs.

1. Run the pre-flight from the single-PR flow through authenticated-login
   discovery.
2. Enumerate work with:

   ```bash
   # gh pr list caps output at --limit N and does not expose totals, so a queue
   # larger than the limit would silently lose PRs. Page the GraphQL API
   # instead: flatten every page with `jq -s` and use totalCount as a
   # completeness check before dispatching.
   gh api graphql --paginate \
     -F owner="$OWNER" -F name="$REPO" \
     -f query='query($owner:String!, $name:String!, $endCursor:String) {
       repository(owner:$owner, name:$name) {
         pullRequests(first:100, states:OPEN, after:$endCursor) {
           totalCount
           nodes {
             author { login }
             number title headRefName isDraft mergeable mergeStateStatus
           }
           pageInfo { hasNextPage endCursor }
         }
       }
     }' |
     jq -s --arg me "$ME" '
       ([.[].data.repository.pullRequests.nodes[]] | length) as $collected
       | ([.[].data.repository.pullRequests.totalCount] | last) as $total
       | if $collected != $total then
           error("incomplete PR pagination")
         else
           [.[].data.repository.pullRequests.nodes[]
            | select(.author.login == $me)
            | {number, title, headRefName, isDraft, mergeable, mergeStateStatus}]
         end'
   ```

3. Filter out drafts unless explicitly requested.
4. Fetch `origin/main` once before dispatch.
5. Detect active worktree collisions and mark those PRs
   `blocked-active-worktree`.
6. Dispatch remaining PRs through the single-PR flow.
   - If the agent runtime supports background workers, cap concurrency at 4.
   - Backfill one PR when a worker completes until the queue is drained.
   - If the runtime cannot safely delegate, process the queue sequentially.
7. Do not wait on CI in the first pass after a push; report the pushed SHA and
   move on.
8. Circle back over PRs with pending/failing CI, new comments, unresolved
   threads, or non-terminal outcomes.
9. Stop redispatching a PR when the same genuine blocker remains after honest
   investigation; surface the blocker instead of retrying blindly.
10. Report merge order for unblocked PRs:
    - dependency chains first,
    - then smaller blast radius before larger changes.

    This report is the END of the workflow — **never merge**. It is
    delivered only AFTER the [Cleanup](#cleanup) section has completed
    (worktree/branch reaping and restoration of the orchestrator's starting
    branch). The workflow's job ends when a PR is merge-ready (no conflicts,
    required checks green, all review threads resolved): report
    merge-readiness and a recommended merge order, then hand off to the
    user. Merging is always a human action. No agent may run `gh pr merge`
    or merge by any other means — regardless of how the request is phrased
    (e.g. "resolve all the PRs" means prepare + report, never merge).

## Cleanup

After all circle-back rounds complete, reap the worktrees and local branches the
bulk run left behind. Cleanup is **all-or-nothing**:

- **If any PR in the run ended in a `blocked-<reason>` state, skip cleanup
  entirely.** The user needs to `cd` into the blocked worktree and finish by
  hand. Worktree liveness is decided by process/PID checks, not the current
  working directory, so a user shell sitting inside the worktree provides no
  incidental protection — the skip must be applied before any reaping runs.
- When skipping, list the surviving worktrees and local branches so the user
  knows what was kept. These discovery commands are global (not scoped to this
  run); the report's `Worktree` and `Local branches` fields are informational
  only and do not drive selective cleanup:

  ```bash
  git worktree list --porcelain | grep '^worktree ' | tail -n +2 | sed 's/^worktree //'
  git branch -l 'local-*' 'agent-*' 'worktree-*' 'claude/*'
  ```

- Only when NO PR in the run is blocked: prune stale worktrees (locked-worktree
  detection + PID liveness + `git worktree prune`) and remove the stale local
  branches created per PR (`local-*` and the agent/worktree prefixes above).
  Prefer the repo's dedicated cleanup tooling over a bare
  `git worktree remove` / `git branch -D` loop because it applies PID liveness
  checks. Adapters map this to their own cleanup commands (e.g. Claude's
  `/cleanup-worktrees` and `/cleanup-branches` skills).

Then restore the orchestrator's starting branch before reporting the merge order.

## Per-PR Worker Contract

Each isolated per-PR worker must follow this protocol:

- Read AGENTS.md before acting; do not substitute stale copied commands.
- Rebase on `origin/main`; never merge `main` into a feature branch.
- Capture `STARTING_REMOTE_SHA` immediately after fetching the branch and before
  the gate loop.
- Treat review comments as hypotheses until verified against the actual file,
  canonical docs, and PR intent.
- Reply to every finding, including no-action decisions, duplicates, and
  findings from review bodies or issue comments that have no resolvable thread.
- Resolve only threads that were actually addressed.
- If deferring an item, create a GitHub issue first and cite it in the reply.
- Avoid duplicate acknowledgement comments by checking the target channel before
  posting: query the same channel for comments authored by the running user
  within the last ~60 seconds and compare the full body before re-posting.
- Before claiming a no-op `no-op-no-comments` (or otherwise treating the PR as
  ready), run the readiness gate on the current head SHA: the latest bot
  adversarial-review marker for that SHA must report `blocking=0`, and no
  required CI check on that SHA may be in a failing state. A marker on an older
  SHA does not satisfy the gate. (`already-merged` skips this gate — the branch
  may be gone.)
- Return `blocked-<reason>` rather than guessing through ambiguous conflicts,
  unclear CI failures, or contradictory review requirements.

## Outcomes

Adapters should normalize per-PR results to these outcomes:

- `pushed-waiting-CI`: changes were pushed and CI has not settled yet.
- `merged-ready`: no conflicts, required checks are green, and review threads
  are resolved.
- `no-op-no-comments`: current HEAD is already ready and no push was needed.
- `already-merged`: the PR is no longer open because it was merged.
- `blocked-active-worktree`: the branch is checked out elsewhere locally.
- `blocked-<reason>`: a specific blocker requires human input or external
  state to change.

## Tool-Specific Notes

- Claude slash commands live under `.claude/skills/` and should be adapters that
  point here instead of owning repo policy.
- Codex should execute this workflow directly from AGENTS.md and this document;
  if using sub-agents, each sub-agent owns a distinct PR worktree.
- The GitHub workflow named `Claude Code Review` is a project reviewer, not the
  owner of these instructions. Treat its comments like any other review input:
  verify, fix when valid, and push back with citations when invalid.
