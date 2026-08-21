# branching-demo

Main + backport branching with **parallel CI** and a **mutual gate**. Zero custom orchestrator.

```
   main            release/2026.q3
   ────            ───────────────
   next release    what customers run today
   (v2027.q1)      (v2026.q3.3)
```

A fix on `main` gets a paired backport PR into `release/2026.q3`. Both CIs run at once. Neither PR merges until both are green.

## What happens when you label a PR

```
1.  Developer opens PR #42 → main
    └─ ci runs on #42

2.  Developer adds label:  backport release/2026.q3
    └─ workflow cherry-picks + opens PR #43 → release/2026.q3
       ci runs on #43 in parallel with #42

3.  Both CIs finish
    ┌───────────────┐          ┌───────────────┐
    │  PR #42       │          │  PR #43       │
    │  ci     ✅    │          │  ci     ✅    │
    │  partner-ci ✅│◄────────►│  partner-ci ✅│
    └───────────────┘          └───────────────┘
    Both mergeable.
```

## What happens when one side fails

```
    ┌───────────────┐          ┌───────────────┐
    │  PR #42       │          │  PR #43       │
    │  ci     ✅    │          │  ci     ❌    │
    │  partner-ci ❌│◄─────────│               │
    └───────────────┘          └───────────────┘
    Main is BLOCKED even though its own ci passed.
    Fix the backport → both go green → both mergeable.
```

Branch protection requires **`ci` AND `partner-ci`** on both branches. Neither can merge in isolation.

## The three files that do the work

```
.github/workflows/
├── ci.yml                       # runs pytest, mirrors result as partner-ci
└── open-paired-backport.yml     # opens the paired PR when the label is added
```

## When something goes wrong

### 1 · Cherry-pick can't apply cleanly

Someone else already touched the same lines on `release/2026.q3`, so the auto cherry-pick collides.

```
  label added
        │
        ▼
  ┌────────────────────────────────┐
  │  PR #43 (backport) opens with: │      ci ❌
  │    <<<<<<< HEAD                │       │
  │    old code                    │       │ mirrors
  │    =======                     │       ▼
  │    new code (the fix)          │      partner-ci ❌  on PR #42
  │    >>>>>>>                     │
  │  ⚠️ Note in the PR body         │      (main PR blocked)
  └──────────────┬─────────────────┘
                 │
                 │  developer pulls the branch,
                 │  keeps the right side of the merge,
                 │  removes the markers, pushes
                 ▼
  ┌────────────────────────────────┐
  │  hello.py is clean now         │      ci ✅  ──►  partner-ci ✅  on PR #42
  └────────────────────────────────┘
                                          Both PRs mergeable.
```

### 2 · A conflict appears later

Someone merges an unrelated change into `release/2026.q3` while PR #43 was open, and it touches the same lines.

```
  PR #43 (backport) — status changes on its own:

  ┌────────────────────────────────┐
  │  ⚠️ This branch has conflicts   │      merge button: disabled
  │      that must be resolved     │
  │  [ Resolve conflicts ]         │
  └──────────────┬─────────────────┘
                 │
                 │  developer resolves in the web UI
                 │  (small conflict) or rebases locally
                 │  and force-pushes the backport branch
                 ▼
                                          ci ✅  ──►  partner-ci ✅  on PR #42
                                          Both PRs mergeable.
```

### 3 · Force-push on either PR

Any new commit changes the PR's HEAD SHA. The old `ci` + `partner-ci` were reported against the *old* SHA and no longer count for the new one.

```
  Before force-push:              After force-push:

  PR #42                          PR #42
    HEAD: abc123                    HEAD: def456   ← new
    ci     ✅ (on abc123)           ci     ⏳
    partner-ci ✅ (on abc123)       partner-ci ⏳   ← required, not yet reported

                                    (merge blocked until fresh checks land)

  What happens automatically:
    1. ci re-runs on def456
    2. it mirrors partner-ci → PR #43
    3. PR #43's next ci run mirrors partner-ci ─► PR #42

  No manual cleanup. Check-runs are per-SHA — GitHub's model handles it.
```

### 4 · The backport fix has to look *different*

Sometimes `release/2026.q3` needs a smaller / different code change than `main` (main might refactor; release wants the minimal patch).

```
  PR #42 (main)            PR #43 (backport)
  refactored fix           different fix
  (10 files, 200 lines)    (1 file, 3 lines)
                                                
  The mutual gate still holds:
     both PRs' ci must pass
     both partner-ci must mirror green
                                                
  What changes: the developer pushes their own commits
  on the backport branch instead of accepting the
  cherry-picked diff. The paired-PR wiring stays intact.
```

## Setup for adopters

1. Add repo secret **`BOT_TOKEN`** — PAT (or GitHub App token) with `contents: write` + `pull-requests: write`.
   > `GITHUB_TOKEN`-authored events don't trigger downstream workflows, so we can't use the default token.
2. **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests** → on.
3. Enable branch protection on `main` and each `release/*` branch requiring these checks: **`ci`** and **`partner-ci`**.

## Also in the repo

- `hello.py` — tiny app with a demo bug in `refresh_token`
- `test_hello.py` — the test that fails on the bug, passes on the fix
- `CODEOWNERS` — release-owner governance
- `DEMO.md` — the step-by-step live-demo script

## Not covered here

- More than one release branch — same pattern, add more labels
- Deploy pipelines — separate concern (tag + release workflow)
- Structurally different fixes on release vs main — those are just plain PRs, no pairing
