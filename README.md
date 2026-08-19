# branching-demo

Live demo of the **main + backport** branching pattern.

- `main` → future release (v2027.q1, still in development)
- `release/2026.q3` → what customers are running today (v2026.q3.3)

A **backport PR** is how a fix on `main` gets applied to `release/2026.q3` as a separate, reviewed change — no cross-branch orchestrator required.

See [`DEMO.md`](DEMO.md) for the live-demo script.

## Repo layout

- `hello.py` — a tiny "app" that will get a bug fix live
- `CODEOWNERS` — release owners for the maintenance branch
- `.github/workflows/backport.yml` — auto-opens the backport PR when you label a merged PR with `backport release/2026.q3`
