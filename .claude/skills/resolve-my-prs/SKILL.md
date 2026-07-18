---
name: resolve-my-prs
description: Walk every open PR authored by the current GitHub user, address unresolved review comments (human + bot), rebase + force-with-lease push only when changes are needed, circle back for CI, and report the final merge order. Pipelined dispatch loop — push and move on, don't block on CI.
---

# resolve-my-prs

Dispatch loop for grinding through a backlog of your open PRs in this repo. The outer orchestrator enumerates the queue and **fans out one Agent per PR in parallel, each in its own git worktree**. The outer orchestrator only does enumeration, dispatch, and final reporting — it never touches branches itself. After the fan-out completes, the outer orchestrator collects results and prints the merge order.

This skill is **self-contained**. Per-PR mechanics (auth, comment fetch, GraphQL thread resolution, push policy, CI debug, conflict resolution) are inlined below. The per-PR agent must read `AGENTS.md` (and `CLAUDE.md` / `CONTRIBUTING.md` if they exist) first — those files contain standing conventions that override the generic guidance here.

## When to use

- Invoked manually as `/resolve-my-prs` when you want to clear your whole PR backlog in one sitting.
- Not for one-off PR work. If you're fixing comments on a single PR, do that in plain conversation. The overhead of the dispatch loop only pays off when there are several PRs to grind through.

## Scope (hard limits)

- **Only PRs authored by the current GitHub user.** Determined by `gh api user -q .login` at the start of the run and never widened.
- **Only open PRs.** Skip draft PRs unless the user explicitly says otherwise.
- **Never merge the default branch into a feature branch.** Always rebase on `origin/<default-branch>` (detect with `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`).
- **Always `--force-with-lease`.** Never plain `--force`.
- **Never bypass checks.** No `--no-verify`, no disabling lint rules, no skipping/deleting tests to make CI green. Fix the underlying issue.

## Pre-flight (once per invocation, in the outer orchestrator)

The outer orchestrator stays in the main checkout. It only runs read-only `gh` and `git` commands. Per-PR worktrees are created by each fanned-out Agent via `isolation: "worktree"` — the orchestrator does **not** create them itself.

Parallel fan-out is the only mode this skill describes. If a user explicitly asks for sequential processing, ignore the skill and process the queue one PR at a time in plain conversation — the per-PR template below is parameterised for a single `${N}` and would need rewriting to drive a loop.

1. Auth:

   ```bash
   gh auth status
   ```

2. Identify yourself and lock the author scope:

   ```bash
   ME=$(gh api user -q .login)
   ```

3. Derive repo slug + default branch once so every downstream `gh api` call has explicit strings:

   ```bash
   OWNER=$(gh repo view --json owner -q .owner.login)
   REPO=$(gh repo view --json name  -q .name)
   DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
   ```

4. Pull the work queue using the locked `$ME` scope:

   ```bash
   gh pr list --author "$ME" --state open \
     --json number,title,headRefName,isDraft,mergeable,mergeStateStatus
   ```

   Filter out drafts. Use `$ME` consistently rather than `@me` — `@me` resolves at request time and could drift if auth context changes mid-run.

5. Refresh the default branch once up front so rebase targets are fresh:

   ```bash
   git fetch origin "$DEFAULT_BRANCH"
   ```

6. Remember where you started — `ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)` — so you can return at the end.

## First pass — parallel fan-out (one Agent per PR, capped concurrency)

After the queue is enumerated, **fan out**: send a message containing up to `MAX_CONCURRENT` `Agent` tool calls. Each call MUST include:

- `subagent_type: "general-purpose"`
- `isolation: "worktree"` — each agent gets its own worktree off the default branch
- `run_in_background: true` — **critical**. Without this, multiple `Agent` calls in one message run concurrently but the orchestrator's turn blocks until every one returns synchronously. With `run_in_background: true`, each agent fires a completion notification when done; the orchestrator's turn ends immediately after dispatch and is re-invoked on each completion. The notification model is what enables the "push and move on" semantics.

**Concurrency cap: `MAX_CONCURRENT = 4`.** Dispatch at most 4 Agent calls in the first message. On each completion notification, if the queue still has PRs, dispatch one replacement Agent so the in-flight count stays ≈4 until the queue drains. The notification-driven backfill preserves "push and move on" — no polling, no sleep. **Rationale:** an unbounded burst dispatch on a sibling project exhausted the Anthropic session budget mid-run and saturated the laptop's worktree / I/O. If session-limit errors still occur with cap=4, lower it further rather than raising it. When the queue exceeds `MAX_CONCURRENT`, the orchestrator prints `"Dispatching N PRs in batches of <MAX_CONCURRENT> — will take ~X minutes"` so the user knows the run is paced.

The orchestrator's job after fan-out: wait for each completion notification, dispatch a replacement Agent if any PRs remain in the queue, accumulate the per-PR reports, and once all agents have reported, assemble the merge order. It does **not** touch any branch itself.

### Worktree-collision rule

If a PR's branch is already checked out in another worktree on this machine, **skip that PR** and mark its outcome as `blocked-active-worktree` in the final report. Fanning out an agent that fights with the user's live edits is worse than skipping. The outer orchestrator detects this with `git worktree list --porcelain` before dispatching.

### Per-PR Agent prompt template

Each fanned-out Agent receives a prompt built from this template, with `${N}`, `${BRANCH}`, `${OWNER}`, `${REPO}`, `${DEFAULT_BRANCH}`, and any PR-specific hints filled in by the outer orchestrator:

```text
You are processing a single open PR (#${N}, branch `${BRANCH}`) for user
`${ME}` in repo `${OWNER}/${REPO}`. The repo's default branch is
`${DEFAULT_BRANCH}`. You are running in a fresh git worktree off
origin/${DEFAULT_BRANCH} (created by isolation: "worktree").

Phase 0 — re-derive shell variables. The outer orchestrator substituted
the brace-form `${ME}` / `${OWNER}` / `${REPO}` / `${DEFAULT_BRANCH}`
placeholders into this prompt, but several shell snippets below also
reference `$ME` / `$OWNER` / `$REPO` as live shell variables (passed via
`jq --arg`, used inside URLs, etc.). Re-bind them in your shell so both
forms behave identically:
  ME=$(gh api user -q .login)
  OWNER=$(gh repo view --json owner -q .owner.login)
  REPO=$(gh repo view --json name  -q .name)
  DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)

Read repo-local convention files BEFORE doing anything — any of these
that exist contain standing rules that override the generic guidance in
this prompt:
  - AGENTS.md (project root)
  - CLAUDE.md (project root)
  - .github/copilot-instructions.md
  - CONTRIBUTING.md
  - src/object_detection/README.md (module conventions)

=== Branch checkout ===

  git fetch origin ${BRANCH}
  git fetch origin ${DEFAULT_BRANCH}
  git checkout -B local-${N} origin/${BRANCH}
  git rebase origin/${DEFAULT_BRANCH}
  # ...do work...
  # ...run the pre-push gate (see below)...
  git push --force-with-lease origin local-${N}:${BRANCH}

If `git rebase origin/${DEFAULT_BRANCH}` hits a conflict whose intent is
genuinely ambiguous after consulting code, history, and PR description,
STOP and return blocked-conflict-ambiguous with file:line. Do not guess.

=== Standing dji-tello-playground conventions ===

These trump bot suggestions to the contrary — push back when bots
violate them, citing AGENTS.md or this list:

  - Commits follow Conventional Commits (`feat:`, `fix:`, `docs:`,
    `refactor:`, `test:`, `chore:`) per AGENTS.md.
  - Numbered exercises in `src/example_exercises/` (`NN_description.py`)
    are deliberately self-contained teaching scripts. Some duplication
    between exercises is intentional for readability; reusable detection
    logic belongs in `src/object_detection/`, not forked into exercises.
  - The `sys.path.insert(...)`-before-import pattern at the top of
    exercises is established repo style (flake8 E402 is expected there).
  - Drone safety is non-negotiable: scripts that can fly keep their
    SIGINT/SIGTERM handlers and emergency-landing cleanup; RC/takeoff
    commands stay inside `not DEBUG_MODE and not NO_TAKEOFF` guards;
    RC velocities are clamped to [-100, 100].
  - Tello frames arrive RGB — `cv2.cvtColor(img, cv2.COLOR_RGB2BGR)`
    before OpenCV color operations. OpenCV hue range is 0–179.
  - Never edit `venv/` or commit anything inside it.

=== Pre-push gate (MANDATORY before every git push) ===

The repo has no pre-commit config and the existing tree does not pass
black/flake8 repo-wide, so the gate is scoped to the files this PR
touches. Tools are pinned in requirements.txt (black, flake8, pytest).
Run from the repo root and fix any failure before pushing:

  CHANGED=$(git diff --name-only origin/${DEFAULT_BRANCH}...HEAD -- '*.py')
  [ -n "$CHANGED" ] && black --check $CHANGED
  [ -n "$CHANGED" ] && flake8 --max-line-length 88 --extend-ignore E203,E402 $CHANGED
  pytest -q || [ $? -eq 5 ]   # exit 5 = "no tests collected" — fine today,
                              # mandatory so broken tests can't ship later

Never push with `--no-verify`, never skip a step, never `# noqa` away a
flake8 finding without an inline reason. If a fix is genuinely
out-of-scope for this PR, file a follow-up issue (see the "Filing as a
follow-up" block below) instead of bypassing the gate. Do NOT reformat
files the PR doesn't touch.

=== Review bots (CodeRabbit + adversarial Claude review) ===

Two bots review PRs here:

  1. CodeRabbit — posts a walkthrough issue-comment plus inline review
     threads. Treat its findings like any reviewer's.
  2. The adversarial Claude reviewer (`.github/workflows/claude-code-review.yml`)
     — runs on every non-fork PR with a valid CLAUDE_CODE_OAUTH_TOKEN
     secret and posts an `## Adversarial review` issue comment with a
     machine-readable `bot-review-marker` line that the Bot Blocking
     Gate check parses. It is tuned for ZERO benefit of the doubt; the
     correct response is **consensus, not capitulation**: fix real
     defects, push back with evidence on hallucinated / stylistic /
     out-of-scope findings, and resolve the thread either way. A silent
     "done" on a wrong bot finding teaches the bot a wrong finding was
     correct.

**Wait gate after each push.** Before declaring `no-op-no-comments`,
confirm the Claude bot has had a chance to post. Poll briefly:

  gh run list --workflow=claude-code-review.yml --branch "${BRANCH}" \
    --limit 5 --json databaseId,status,conclusion,headSha \
    | jq -r ".[] | select(.headSha == \"$(git rev-parse HEAD)\")"

If a matching run is still in-progress, wait for it to complete (or
`gh run watch <id>`) before re-fetching comments. If no matching run
exists after ~60s, assume the workflow's secret-gate failed (forks,
missing secret) and proceed without it.

=== Comment fetch (four channels) ===

Comments live in four places. Fetch all four — silently missing one
channel is how findings get skipped.

  # 1. PR body
  gh pr view ${N} --json body

  # 2. Issue comments (conversation-tab comments — where the Claude bot
  #    posts its `## Adversarial review` block and CodeRabbit posts its
  #    walkthrough). --paginate is REQUIRED: gh api defaults to one page
  #    of 30, so on a busy PR older comments are invisible.
  gh api --paginate repos/${OWNER}/${REPO}/issues/${N}/comments

  # 3. Review summaries (the bot/human "I reviewed this" bodies)
  gh pr view ${N} --json reviews,latestReviews

  # 4. Inline review comments (attached to file:line). Same pagination
  #    rule — without --paginate the gh CLI quietly truncates.
  gh api --paginate repos/${OWNER}/${REPO}/pulls/${N}/comments

Review bodies and issue comments have **no `isResolved` field** — they
are not modelled as review threads, so the GraphQL `reviewThreads`
query in the resolution step below will never report state for them.
Track them manually: read every body in full, decide a verdict per the
table below, and reply on the parent review / issue comment when
pushing back or confirming a fix. This is the easiest class of feedback
to silently drop after one pass.

=== Verdict per finding (MANDATORY for every comment) ===

Every comment is a hypothesis until you verify it. The goal of the loop
is **consensus on real defects**, not perpetual disagreement — and not
capitulation by default either.

For each finding:

  1. Re-read the cited file at the cited line. Reviewers hallucinate
     file contents, misread types, and quote code that was already
     removed earlier in the same PR. `Read` the actual file before
     forming an opinion. If the quoted snippet doesn't match the tree,
     the comment is almost certainly a false positive.
  2. Check the comment against repo docs (AGENTS.md, README.md,
     src/object_detection/README.md). A comment that contradicts those
     is itself a defect.
  3. Pick a verdict and act:

| Verdict | Action |
|---------|--------|
| Valid, not yet fixed | Implement fix, push, reply with commit SHA / file:line, then resolve |
| Valid, already fixed in this PR | Reply with the commit SHA / file:line that fixed it, then resolve |
| False positive (hallucination) | Reply quoting the real code that disproves the comment, then resolve |
| Correct fact, wrong conclusion (by design) | Reply citing the invariant (doc path, standing convention, file:line), then resolve |
| Stylistic preference, not a defect | Reply briefly with the rationale for the existing choice, then resolve |
| Duplicate of an earlier addressed finding | Reply `"addressed in <prior-reply-URL>"`, then resolve |
| `SUSPECT` flagged by reviewer | Investigate; promote to one of the rows above based on what you find. Never resolve a `SUSPECT` thread on faith. |

=== EVERY finding gets a reply, EVERY thread gets resolved ===

Even no-action findings need a trace. The user audits this skill's
output by scrolling the PR's Conversation tab and looking for
unresolved threads or silent comments. A finding you investigated and
decided to no-op on is indistinguishable from a finding you never read
unless you leave a trace. The bar is: "did the agent at least look at
this?" must be answerable by reading the PR's Conversation tab alone.

  - No silent agreement. A reply of "done" on an invalid comment teaches
    the bot's knowledge base that a wrong finding was correct.
  - No silent disagreement. If you don't fix a comment, the reply must
    explain why with a citation.
  - Reply first, then resolve. Always. The thread should never be
    resolved before the reply lands.
  - Body-channel acknowledgements (review bodies, issue comments) are
    doubly important because there's no `isResolved` field to fall back
    on — name each finding by quote or file:line in your acknowledgement.

=== "Filing as a follow-up" means actually filing an issue ===

If a reply defers an item ("tracked as a follow-up", "out of scope for
this PR"), you MUST create a GitHub issue for it *before posting the
reply*, then cite the issue number in the reply. Issue body opens with
`Deferred from #${N} (<PR-comment-URL>).` and has 2-4 lines covering
what, where (file:line), why deferred, and success criteria.

Issue creation uses `gh issue create` with `--title <scope>: <one-line
ask>` and `--body` passed via a HEREDOC (inline `--body "..."` mangles
newlines). Then in your reply on the PR, append the single line:

  Follow-up filed: #<new-issue> (<one-line scope>)

=== Idempotent posting — never double-post ack comments ===

Before POSTing any ack comment, check the same channel you're about to
post on for an authored comment in the last 60 seconds with a matching
**full body** (not a prefix). If a match exists, skip the POST and
extract `.html_url` from that comment for any downstream reference.

`gh api --jq` accepts only a single filter string and does NOT proxy
jq's `--arg`, so the check goes through a real `jq` invocation:

  existing=$(gh api --paginate "repos/${OWNER}/${REPO}/issues/${N}/comments?per_page=100" \
    | jq -s 'add' \
    | jq -r --arg me "$ME" --arg body "$reply_body" \
        '[.[] | select(.user.login == $me and .body == $body
          and ((.created_at | fromdateiso8601) > (now - 60)))][0].html_url // empty')
  [ -n "$existing" ] && echo "duplicate; reusing $existing" && return

Same shape with the path swapped for the inline-comments channel
(`pulls/${N}/comments`) and the review-bodies channel
(`pulls/${N}/reviews`).

=== Thread resolution (GraphQL) ===

Replying via the REST `/comments/<id>/replies` endpoint does NOT mark
the thread resolved. Track the specific thread IDs you replied to and
resolve only those — do not bulk-resolve all unresolved threads, since
that would silently close findings you never addressed.

First, page through every review thread so you can map each inline
comment ID you replied to back to its parent thread ID. `reviewThreads`
uses Relay cursors; paginate until `hasNextPage` is false:

  gh api graphql -f query='
    query($owner:String!,$repo:String!,$n:Int!,$cursor:String){
      repository(owner:$owner,name:$repo){
        pullRequest(number:$n){
          reviewThreads(first:100, after:$cursor){
            pageInfo{ hasNextPage endCursor }
            nodes{ id isResolved comments(first:100){ nodes{ databaseId } } }
          }
        }
      }
    }' -F owner="$OWNER" -F repo="$REPO" -F n="$N" \
     [ -F cursor=<endCursor from previous page> ]

Build a `comment_id -> thread_id` map from the paged results. For each
inline comment you actually replied to in this run (track `REPLIED_IDS`
as you post), look up its `thread_id`, dedupe, and resolve only those:

  for tid in $RESOLVED_THREAD_IDS; do
    gh api graphql -f query='mutation($threadId:ID!){
      resolveReviewThread(input:{threadId:$threadId}){thread{id isResolved}}
    }' -f threadId="$tid"
  done

Re-fetch the same paginated query at the end as a verification step.
Every thread ID in `RESOLVED_THREAD_IDS` must show `isResolved: true`.
Threads you intentionally left open should be called out in `Notes`.

=== Pushing ===

Run the pre-push gate above. Then:

  git push --force-with-lease origin local-${N}:${BRANCH}

Do NOT wait for CI. Return immediately after the push so the
orchestrator can move on. CI babysitting belongs to the circle-back
round.

Return EXACTLY this report shape (one fenced block):
  PR: #${N}
  Outcome: <pushed-waiting-CI | no-op-no-comments | blocked-<reason> | already-merged>
  SHA: <pushed sha or '-'>
  Resolved threads: <list of URLs or thread IDs, or '-'>
  Push-backs: <one line per intentionally rejected comment with the reason, or '-'>
  Notes: <one line, anything the orchestrator needs for the final merge-order decision>

Keep the report under 250 words. `merged-ready` is NOT a first-pass
outcome — after pushing, CI has not yet run; the earliest a PR reaches
`merged-ready` is in a circle-back round after CI lands green.
```

### What the outer orchestrator does between fan-out and reporting

- Do **not** poll the agents. With `run_in_background: true` on every dispatch, each agent fires a completion notification when done and the orchestrator's turn is re-invoked.
- **On each completion notification, if the queue still has PRs, dispatch one replacement Agent** before accumulating the report, so the in-flight count stays ≈`MAX_CONCURRENT`. Skipping this step collapses the run back to "one batch of 4, then idle".
- Do **not** check CI yourself for pushed PRs. The agents pushed and returned without waiting; circle-back is its own round of fan-out.
- When **all** agents have reported (queue empty AND no in-flight Agents), assemble the merge order (see "Final report" below) from their `Outcome` + `Notes` fields. Carry each PR's reported `SHA` forward — the circle-back round will need it injected as `${PREV_SHA}` so the per-PR agent matches the right CI run.

## Circle-back phase (parallel fan-out, same shape as first pass)

After the first-pass reports come back, identify PRs with **open work**: CI still running or failing on the pushed SHA, new bot comments landed since the push, or threads still unresolved. **Fan out again with the same cap=4 + backfill pattern as the first pass.** Each call uses `isolation: "worktree"` and `run_in_background: true`. Use the same Per-PR Agent prompt template plus the additions below.

For each circle-back invocation, the orchestrator MUST inject `${PREV_SHA}` (the SHA the first-pass agent reported for that PR) so the new agent matches the correct CI run rather than re-deriving the SHA from a moved branch. Prepend to the prompt:

```text
Previous push SHA for this PR: ${PREV_SHA}. Use this SHA when matching
the CI run from the prior pass.
```

1. **New comments since last push.** Re-fetch the four channels and the `claude-code-review.yml` workflow status (the bot re-runs on every push and usually posts within a minute or two of the run completing). Diff against the `Notes` snapshot in the previous round's report. Apply the same verdict logic.

2. **CI status for `${PREV_SHA}`** — the per-PR agent runs:

   ```bash
   gh run list --branch "${BRANCH}" --limit 10 \
     --json databaseId,name,status,conclusion,headSha \
     | jq -r ".[] | select(.headSha == \"${PREV_SHA}\")"
   ```

   Match on `${PREV_SHA}`, not `git rev-parse HEAD` — the branch may have moved between rounds. Treat `claude-code-review.yml` `conclusion=success` as "bot review posted, fetch and address" rather than "PR is green".

3. **Failures by category:**

   | Failure | Action |
   |---|---|
   | **Test (pytest)** | Read the failing output, diagnose root cause. Fix the code if the code is wrong; fix the test only if the new behavior matches the PR's business intent. Never skip or delete a test to make CI green. |
   | **Lint (flake8)** | Re-run the gate's flake8 line locally on the changed files, fix every reported issue. Don't `# noqa` without an inline reason. |
   | **Format (black)** | `black <changed files>` then re-stage. |
   | **Bot review (Claude or CodeRabbit)** | Apply the verdict table; fix real defects, push back with evidence on hallucinated / stylistic / out-of-scope findings. |
   | **Bot Blocking Gate** | Failing means the latest adversarial review on the head SHA reported `blocking>0` (or the review hasn't completed). Address the blocking findings and push; the gate re-evaluates automatically. |
   | **Flaky** | Rerun once. If it keeps failing intermittently, treat it as a real failure and investigate. |

4. **Same push policy.** Before pushing the fix, rebase on `origin/${DEFAULT_BRANCH}` again, re-run the pre-push gate, then `git push --force-with-lease`. Resolve any threads you addressed via the GraphQL mutation.

5. **Repeat the circle-back** by re-fanning out over the still-open PRs until every PR is mergeable: no conflicts, all required checks green, all threads resolved. Each round is its own parallel fan-out under the same `MAX_CONCURRENT` cap.

6. **Genuine blocker → stop and surface it.** If an Agent returns `blocked-<reason>` for ambiguous conflict, CI failure with no clear cause after honest investigation, or two comments that contradict each other where neither matches the PR's business intent, surface the blocker in the final report with the specific PR number, the failing check or thread URL, and what was already tried. Do not re-dispatch the same PR with the same prompt hoping for a different answer.

## Final report

Once every PR in scope is mergeable, restore your starting branch (`[ "$ORIGINAL_BRANCH" = "HEAD" ] || git checkout "$ORIGINAL_BRANCH"`) and print the **merge order** the user should use. Order by:

1. **Dependency chain first.** If PR B's branch was cut from PR A's branch, or PR B's diff overlaps with files PR A touches, A merges first.
2. **Smallest blast radius next.** Among PRs with no dependencies, merge the one that touches the fewest files first.

Justify the order briefly (1 short sentence per PR pair).

If any PR ended the run in a blocked state, list it separately at the bottom with the blocker and *do not* include it in the merge order.

## Ground rules (recap)

- **Outer orchestrator never touches branches.** Enumerate, fan out, collect reports, print merge order. That's it.
- **At most 4 Agents per message, with backfill on completion** (`MAX_CONCURRENT = 4`). Each call uses `isolation: "worktree"` AND `run_in_background: true`. Never dispatch the whole queue at once.
- **Skip PRs whose branch is already checked out in another worktree** — mark `blocked-active-worktree`.
- **Reply + resolve on every finding, even no-action ones.** A silent skip is indistinguishable from a missed comment.
- **Wait for the `claude-code-review.yml` run to complete before declaring no-comments.**
- **Pre-push gate is scoped to changed files** (`black --check` + `flake8 --max-line-length 88 --extend-ignore E203,E402` + `pytest -q`, treating "no tests collected" as pass). Mandatory before every push, never bypassed.
- **"Filing as a follow-up" means actually filing an issue.**
- Scope is strict: open PRs authored by `$ME` only. No exceptions.
- If you're going to push, rebase on `origin/${DEFAULT_BRANCH}` first. Never `git merge` the default branch into a feature branch.
- No-op PRs (no unresolved comments, no conflicts, bot run already complete and clean) are left alone. No rebase, no push, no CI burn.
- Always `--force-with-lease`, never `--force`.
- When two comments conflict, choose what fits the PR's business requirements and reply on the thread you didn't follow.
- Never bypass a check by disabling, skipping, or deleting tests / lint rules / required status checks.
- Pipeline across PRs: each per-PR Agent pushes and returns without waiting for CI; circle-back is its own round of fan-out.
- When in doubt — stop and ask. Don't guess.

## See also

- [local-pr-review](../local-pr-review/SKILL.md) — run the adversarial reviewer ↔ implementer loop locally before pushing.
- [.claude/prompts/adversarial_reviewer.md](../../prompts/adversarial_reviewer.md) and [.claude/prompts/adversarial_implementer.md](../../prompts/adversarial_implementer.md) — the two prompt bodies.
- [.github/workflows/claude-code-review.yml](../../../.github/workflows/claude-code-review.yml) — the adversarial Claude reviewer that posts on every non-fork PR with a valid `CLAUDE_CODE_OAUTH_TOKEN` secret.
- [.github/workflows/bot-blocking-gate.yml](../../../.github/workflows/bot-blocking-gate.yml) — the required check that enforces `blocking=0` on the head SHA.
- [AGENTS.md](../../../AGENTS.md) — repo conventions (commit format, PR policy, drone safety).
