# branching-demo

Demo of a **main + backport** branching pattern with two properties Siemens' TestLab team asked for:

1. **Parallel CI** — the backport PR opens *at label time*, not after merge. Both PRs' CIs run at the same time. No sequential doubling of wall time.
2. **Mutual gating** — neither PR can merge until *both* sides' CI is green. Native GitHub features only: no orchestrator, no lock, no rollback.

Layout:

- `main` → future release (v2027.q1, still in development)
- `release/2026.q3` → what customers are running today

## Why does this pattern exist?

A customer files a bug: *"the auth token never refreshes on mobile devices."*

- The fix goes on `main` — that becomes v2027.q1, ships in six months.
- But customers on **v2026.q3** are running that broken code *today*. Six months is not an option.

Two options:

- **Fix main only** → the customer waits six months. Not acceptable for security or critical bugs.
- **Fix main + backport into `release/2026.q3`** → the same fix ships as `v2026.q3.4` next Tuesday.

The **"Backport?"** decision is asking: does the currently-deployed release need this fix too? *"Backport = the same commit, applied to the currently-supported release branch, as a separate PR with its own review."*

## How the automation works — three workflows, ~150 lines of YAML total

### 1. `ci.yml`

Runs `pytest test_hello.py` on every PR (against either branch). Produces a check named **`ci`**. This is what CODEOWNERS and reviewers care about.

### 2. `open-paired-backport.yml`

Triggered when a `backport <target-branch>` label is added to a PR against `main` — **even before the PR is merged.** Cherry-picks the diff onto a new branch off the target, opens a paired PR, cross-links the two PRs via a `<!-- paired-pr: N -->` marker.

- **Consequence 1:** both PRs exist at the same time → their CIs run in parallel → the developer sees results simultaneously.
- **Consequence 2:** neither PR is merged automatically — humans still click merge, but they only see green when both sides pass.

### 3. `mutual-gate.yml`

Fires when any `ci` check completes on any PR. Looks up the paired PR (via the `<!-- paired-pr: N -->` marker) and mirrors the result as a check named **`partner-ci`** on the paired PR's HEAD.

Branch protection requires **both `ci` AND `partner-ci`** to be green. The wiring is:

- Main PR needs its own `ci` green + `partner-ci` (mirrored from backport PR's ci) green
- Backport PR needs its own `ci` green + `partner-ci` (mirrored from main PR's ci) green

If either PR's `ci` fails, the other PR's `partner-ci` goes red. Nothing merges. This is the "mutual gate."

### The pair-lookup mechanism

Machine-readable HTML comment `<!-- paired-pr: N -->`:

- **Backport PR body** carries `<!-- paired-pr: <source-PR> -->`
- **Source PR** gets a comment from the workflow with `<!-- paired-pr: <backport-PR> -->`

The mutual-gate workflow checks the body first, falls back to comments. Nothing about the pairing lives in an external DB — it's all in the PRs themselves.

## What happens when there's a merge conflict?

Three distinct cases:

### Case A — Cherry-pick conflict at backport-open time

The main PR's diff can't be cleanly applied to `release/2026.q3` (someone else touched the same lines on the maintenance branch).

**What the workflow does:** the branch is still pushed, but with unresolved conflict markers in the tree. The backport PR is opened with a ⚠️ note in the body: *"Cherry-pick had conflicts. Pull the branch, resolve, push. CI will re-run."*

**What the developer does:** `git fetch && git switch backport/<N>-to-...` → open the file(s) with `<<<<<<< HEAD` / `=======` / `>>>>>>>` markers → resolve → commit → push. CI re-runs. `partner-ci` on main PR flips to pending, then green when backport CI passes.

### Case B — Merge conflict on `release/2026.q3` after the backport PR opens

Something else merged into `release/2026.q3` while the backport PR was open, touching the same lines.

**What GitHub does:** shows the standard "This branch has conflicts that must be resolved" banner on the backport PR. Merge button is disabled.

**What the developer does:** either resolve conflicts in the GitHub web UI (small conflicts), or locally with a rebase (`git rebase origin/release/2026.q3` then push --force-with-lease). Same story as any GitHub PR conflict.

### Case C — Both sides diverged (the interesting one)

Main PR's `ci` was green. Then the developer force-pushed a new commit to the main PR. The paired backport PR's HEAD is unchanged, but the `partner-ci` check was reported against the *old* main SHA.

**What happens automatically:** the new push to main PR triggers `ci.yml` again. When it completes, `mutual-gate.yml` fires and posts a fresh `partner-ci` to the backport PR (same SHA, updated conclusion). No stale state.

**What if you force-push to the backport?** Same story in reverse. The backport PR gets a new HEAD SHA, so its old `partner-ci` (posted against the old SHA) no longer applies. Branch protection reports the required check as *"expected but not yet reported"* → merge is blocked until the mutual-gate workflow fires again for the new SHA.

The invariant is: **check-runs are per-SHA.** GitHub's own machinery invalidates them automatically when the SHA changes. No cleanup logic needed.

## Setup for adopters

- Add a repo secret named **`BOT_TOKEN`** — a Personal Access Token (or a GitHub App installation token) with **`contents: write`** + **`pull-requests: write`** on this repo. Used by `open-paired-backport.yml` for the git push and PR create. Required because `GITHUB_TOKEN`-authored events don't trigger downstream workflows.
- Enable branch protection on both `main` and each `release/*` branch requiring these check contexts: **`ci`** and **`partner-ci`**.
- Turn on **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests**.

## Repo layout

- `hello.py` — the tiny "app" with a fake bug (`refresh_token` returns the same value forever)
- `test_hello.py` — the test that fails on the bug, passes on the fix
- `CODEOWNERS` — visualises the release-owner governance layer
- `.github/workflows/ci.yml` — the `ci` check
- `.github/workflows/open-paired-backport.yml` — opens the paired PR at label time
- `.github/workflows/mutual-gate.yml` — mirrors `ci` → `partner-ci` on the paired PR
- `DEMO.md` — step-by-step demo script

## Not in this POC

- More than one maintenance branch (2+ backport labels → 2+ paired PRs — pattern is the same, just add labels)
- Deploy pipelines (tag + release workflow lives elsewhere; not the branching-strategy question)
- Auto-merge of the backport PR (humans still click merge — that's the CODEOWNERS + reviewer control)
- PR template that auto-applies the label based on a checkbox (nice-to-have, not required to demo the mechanic)
