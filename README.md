# branching-demo

Live demo of the **main + backport** branching pattern.

- `main` → future release (v2027.q1, still in development)
- `release/2026.q3` → what customers are running today (v2026.q3.3)

A **backport PR** is how a fix on `main` gets applied to `release/2026.q3` as a separate, reviewed change — no cross-branch orchestrator required.

See [`DEMO.md`](DEMO.md) for the live-demo script.

## Why does this pattern exist?

Say a customer files a bug: **"the auth token never refreshes on mobile devices"**.

- The fix goes on `main` (that becomes v2027.q1 — ships in six months).
- But customers on **v2026.q3** are running that broken code *today*. They can't wait six months for a patch. Field engineers are locked out.

Two options:

- **Fix main only** → customer waits until 2027.q1 ships. Not acceptable for security or critical bugs.
- **Fix main + backport into `release/2026.q3`** → same fix is applied to the current release as its own PR, ships as `v2026.q3.4` next Tuesday.

That's what the "Backport?" decision is asking: *does the currently-deployed release need this fix too?*

## Why do it this way and not with a custom orchestrator?

The alternative that gets proposed sometimes is a custom orchestrator that merges to both branches atomically, with a global lock and a rollback path if one side fails. That's fragile:

- Git has no atomic cross-branch merge; you'd build the transaction yourself.
- Rollback in Git is a compensating commit, not a true undo — downstream CI already saw the intermediate state.
- The global lock becomes a single point of failure for every dual-scope PR.

**Backport PRs give you the same governance with none of that risk.** Each PR is a normal PR: CODEOWNERS, required checks, Merge Queue, review. If the backport fails, `main` is fine, the failure is *visible on the PR page*, and a human handles it. This is exactly what Linux, Kubernetes, Rails, Postgres, and GitHub Enterprise Server itself all do.

## Repo layout

- `hello.py` — the tiny "app" that will get a bug fix live during the demo
- `CODEOWNERS` — visualises the release-owner governance layer
- `.github/workflows/backport.yml` — the [korthout/backport-action](https://github.com/korthout/backport-action) config. Label a merged PR with `backport release/2026.q3` and a new PR is auto-opened against the maintenance branch.
- `DEMO.md` — 4-minute live-demo script
