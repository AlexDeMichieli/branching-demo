# Live demo — parallel + mutual-gated backport

Total wall time: ~5 minutes.

Two browser tabs open:

- Repo: https://github.com/AlexDeMichieli/branching-demo
- Actions: https://github.com/AlexDeMichieli/branching-demo/actions

## The story you're telling

> A customer filed a bug. `refresh_token()` never actually refreshes. I'll fix it on `main`, and I want the same fix on `release/2026.q3` at the same time. Two PRs, running in parallel, neither mergeable until both pass.

## Step 1 — Open the main PR

1. Repo tab → click **`hello.py`**
2. Pencil icon → change:
   ```
   return user.get("token")
   ```
   to:
   ```
   return user.get("token") + "-rotated"
   ```
3. **Commit changes...**
4. Message: `Fix token refresh: always rotate the value`
5. **⚠ Radio button: "Create a new branch for this commit and start a pull request"** (NOT the direct-to-main option)
6. **Propose changes** → **Create pull request**

Say: *"Normal PR against main. Watch what happens when I add the backport label."*

## Step 2 — Add the backport label

On the newly-opened PR:

1. Right sidebar → **Labels** (gear icon)
2. Tick **`backport release/2026.q3`**
3. Click outside to close

Switch to **Actions tab**. Within ~5 seconds:

- **Open paired backport PR** run starts and finishes in ~20 seconds
- **ci** run starts on the main PR (from step 1)
- **ci** run starts on the newly-created backport PR

Say: *"Both PRs are open. Both CIs are running in parallel. Same wall time as running one PR alone."*

## Step 3 — Watch the mutual gate

Switch to the main PR → scroll to the checks section.

Expected sequence:

- `ci` — pending, then green (~1–2 min)
- `partner-ci` — appears after backport PR's `ci` finishes, mirrors it green
- Backport PR: same story, other direction

Say: *"Neither PR shows the merge button as clickable until both `ci` and `partner-ci` are green. Branch protection is enforcing that."*

## Step 4 — Prove the mutual gate blocks

This is the money shot. Deliberately break the backport PR.

1. Switch to the **backport PR** (title starts with `[Backport release/2026.q3]`)
2. Click **Files changed** tab → find `hello.py` → click the `...` menu → **Edit file**
3. Change the fix back to the buggy version:
   ```
   return user.get("token")
   ```
4. **Commit changes** directly to the backport branch (this is fine, you're pushing to your own PR branch, not a protected branch)

Wait ~1–2 minutes. Watch:

- Backport PR's `ci` turns **red** (test fails on the reintroduced bug)
- Main PR's `partner-ci` turns **red** — mirrored from the backport failure
- Main PR's own `ci` is still green, but the merge button is disabled

Say: *"Main PR passes its own tests. But the mutual gate is blocking it because the backport is broken. This is what 'atomicity substitute' looks like in native GitHub."*

## Step 5 — Fix and merge

1. On the backport PR: pencil-edit `hello.py` again, restore the `-rotated` fix, commit
2. Wait for `ci` to go green
3. Watch `partner-ci` on the main PR flip back to green
4. Merge the main PR: **Merge pull request** → **Confirm merge** → **Delete branch**
5. Merge the backport PR: same three clicks

Say: *"Both branches now have the fix. Same commit content, applied to each release independently, both under mutual gate. No orchestrator, no lock, no compensating rollback."*

## What to say if asked "can the backport open even earlier"

> Yes — apply the label at PR-open time via a PR template checkbox, or automatically via a workflow that inspects the PR title / commit messages. The action itself already fires on the label event, so anything that adds the label works.

## What to say about merge conflicts

- **Case A (cherry-pick can't apply cleanly):** the workflow still pushes the branch with markers, opens the PR with a ⚠️ note. Developer pulls, resolves, pushes.
- **Case B (backport PR gets stale vs release/2026.q3):** normal GitHub "resolve conflicts" flow — web UI or local rebase.
- **Case C (either PR gets a force-push):** check-runs are per-SHA, so old status naturally invalidates. New CI runs, new mirror. No stale state.

Full details in `README.md` under "What happens when there's a merge conflict?"

## Cleanup between demo runs

Delete the fix and backport branches (both auto-delete if you clicked "Delete branch" after each merge). Then close any lingering PRs. If you push to main by accident:

```bash
cd /tmp/branching-demo && git fetch origin
git switch main && git reset --hard <last-good-SHA>
git push --force-with-lease origin main
```

To reset the whole demo to a clean seed:

```bash
git switch main            && git reset --hard <last-good-main>            && git push --force-with-lease origin main
git switch release/2026.q3 && git reset --hard <last-good-release>         && git push --force-with-lease origin release/2026.q3
```
