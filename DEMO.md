# Live demo — the 4-minute script

## Setup already done for you

- `main` branch has `hello.py` with a fake bug (`refresh_token` returns the same value forever).
- `release/2026.q3` branch has the same code (what customers run today).
- A backport workflow is wired up: label a merged PR with **`backport release/2026.q3`** and a new PR is auto-opened against the maintenance branch.

## Step 1 — Open a bug-fix PR against `main`

```bash
git switch main
git switch -c fix/refresh-token
# Edit hello.py — replace the bug with a working refresh:
#   return user.get("token") + "-rotated"
git commit -am "Fix token refresh: always rotate the value"
git push -u origin fix/refresh-token
gh pr create --base main --title "Fix token refresh" \
  --body "Bug: refresh_token was returning the same token forever."
```

Show reviewers on the PR: required checks would run, CODEOWNERS approvals apply, Merge Queue picks it up (or plain merge for this scratch demo).

## Step 2 — Merge the PR into `main`

Click **Merge**. Show that `main` now has the fix.

Point out to the audience: at this moment, main has the fix but **customers on `release/2026.q3` still have the bug**. That's the moment where you decide whether to backport.

## Step 3 — Trigger the backport

On the merged PR, add the label **`backport release/2026.q3`**.

Within ~30 seconds the backport action opens a **new PR** titled `[Backport release/2026.q3] Fix token refresh`.

Show the new PR: it has its **own diff, own CI, own approvals**. Nothing was merged automatically.

## Step 4 — Reviewer sees the backport PR, approves, merges

Merge the backport PR. Now both `main` and `release/2026.q3` have the fix.

**Recap for the room:**

- One fix, applied to two branches
- Each branch got its own review
- No custom orchestrator, no lock, no rollback
- If the backport had failed CI, `main` would still be fine — the failure is *visible on the PR*, not silent state corruption

## Fallback if the label-triggered action doesn't fire

Run this manually to open the backport PR yourself:

```bash
git switch release/2026.q3
git switch -c backport/fix-refresh-token
git cherry-pick <SHA-from-main>
git push -u origin backport/fix-refresh-token
gh pr create --base release/2026.q3 --title "[Backport release/2026.q3] Fix token refresh"
```

Same governance still applies.
