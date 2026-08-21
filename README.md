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

## Merge conflicts

**Cherry-pick can't apply cleanly at open time**
```
backport PR opens with <<<<<<< markers in the tree
→ ci fails (Python won't parse markers)
→ developer pulls the branch, resolves, pushes
→ ci re-runs → partner-ci re-mirrors → both green
```

**Standard conflict later** (someone merged into release/2026.q3)
```
GitHub shows "resolve conflicts" banner on the backport PR
→ developer resolves in the web UI or via local rebase
```

**Force-push on either PR**
```
Check-runs are per-SHA. Old partner-ci no longer applies.
→ CI re-runs on new SHA → partner-ci re-mirrors → automatic.
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
