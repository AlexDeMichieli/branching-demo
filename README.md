# branching-demo

Two long-lived branches. One fix. Both PRs run in parallel. Neither merges until both are green.

```
   main            release/2026.q3
   ────            ───────────────
   next release    what customers run today
```

## When you open a PR against main

```
1.  You open PR #42 → main
2.  A workflow instantly opens paired PR #43 → release/2026.q3
    (same commits, cherry-picked)
3.  Both CIs run in parallel

    ┌───────────────┐          ┌───────────────┐
    │  PR #42 (main)│          │  PR #43 (bp)  │
    │  ci     ✅    │          │  ci     ✅    │
    │  partner-ci ✅│◄────────►│  partner-ci ✅│
    └───────────────┘          └───────────────┘
    Both mergeable.
```

## The mutual gate

Every PR has two required checks: **`ci`** (its own tests) and **`partner-ci`** (a copy of the other side's `ci`). Neither PR can merge unless both are green:

```
   ci on #42  │  ci on #43  │  Result
   ───────────┼─────────────┼─────────────────────
      ✅      │     ✅      │  Both mergeable
      ✅      │     ❌      │  Both blocked
      ❌      │     ✅      │  Both blocked
      ❌      │     ❌      │  Both blocked
```

`partner-ci` is just an ordinary GitHub check that one PR's workflow writes onto the other PR's HEAD commit. No orchestrator, no lock — the check is the coordination.

## The three files that do the work

```
.github/workflows/
├── ci.yml                       # runs pytest, mirrors result as partner-ci
├── open-paired-backport.yml     # opens the paired backport PR when a PR is opened on main
└── pair-lifecycle.yml           # keeps the pair in sync when one PR closes
```

## Setup for adopters

1. Add repo secret **`BOT_TOKEN`** — PAT (or GitHub App token) with `contents: write` + `pull-requests: write`.
   > `GITHUB_TOKEN`-authored events don't trigger downstream workflows.
2. **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests** → on.
3. Branch protection on `main` and each `release/*` branch → require **`ci`** and **`partner-ci`**.

## Also in the repo

- `hello.py` / `test_hello.py` — tiny app with a demo bug
- `CODEOWNERS` — release-owner governance
- `DEMO.md` — the step-by-step live-demo script
