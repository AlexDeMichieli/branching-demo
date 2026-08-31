# Live demo — parallel + mutual-gated backport

Total wall time: ~5 minutes.

Two browser tabs open:

- Repo: https://github.com/AlexDeMichieli/branching-demo
- Actions: https://github.com/AlexDeMichieli/branching-demo/actions

## The story

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
5. **⚠ Radio button: "Create a new branch for this commit and start a pull request"** (NOT direct-to-main)
6. **Propose changes** → **Create pull request**

Say: *"Normal PR against main. Watch what happens next — no label, no button, nothing."*

## Step 2 — The backport PR opens automatically

Switch to **Actions tab**. Within ~5 seconds:

- **Open paired backport PR** run starts and finishes in ~20 seconds
- A new PR appears titled `[Backport release/2026.q3] Fix token refresh...`
- **ci** runs start on **both** PRs in parallel

Say: *"One PR opened, but the workflow cherry-picked the fix onto `release/2026.q3` and opened a second PR against it. Both CIs run at the same time — same wall time as a single PR."*

## Step 3 — Watch the mutual gate

Switch to the main PR → scroll to the checks section.

Expected sequence:

- `ci` — pending, then green (~1–2 min)
- `partner-ci` — appears after the backport PR's `ci` finishes, mirrors it green
- Backport PR: same story, other direction

Say: *"Neither PR's merge button is clickable until both `ci` and `partner-ci` are green. Branch protection enforces that."*

## Step 4 — Prove the mutual gate blocks

The money shot. Deliberately break the backport PR.

1. Switch to the **backport PR**
2. **Files changed** → find `hello.py` → `...` menu → **Edit file**
3. Change the fix back to the buggy version:
   ```
   return user.get("token")
   ```
4. **Commit changes** directly to the backport branch

Wait ~1–2 minutes:

- Backport PR's `ci` turns **red**
- Main PR's `partner-ci` turns **red** — mirrored from the backport
- Main PR's own `ci` is still green, but the merge button is disabled

Say: *"Main passes its own tests. But the mutual gate blocks it because the backport is broken. This is atomicity without an orchestrator."*

## Step 5 — Fix and merge

1. On the backport PR: restore the `-rotated` fix, commit
2. Wait for `ci` to go green
3. Watch `partner-ci` on the main PR flip back to green
4. Merge the main PR → **Delete branch**
5. Merge the backport PR → **Delete branch**

Say: *"Both branches now have the fix. No orchestrator, no lock, no compensating rollback."*

## FAQ during demo

**"What if we don't want to backport a change?"**
Close the auto-opened backport PR without merging. `pair-lifecycle.yml` posts `partner-ci = success` on the main PR — the mutual gate releases, main merges alone.

**"What about merge conflicts on the cherry-pick?"**
Backport PR opens with conflict markers in the file and a ⚠️ note in the body. Developer pulls, resolves, pushes. Same flow.

**"What if someone force-pushes?"**
Check-runs are per-SHA. Old status becomes irrelevant on the new SHA, CI re-runs, mirror re-fires. No cleanup logic needed.

## Cleanup between demo runs

Both PRs auto-delete their branches on merge. If a demo run leaves stragglers:

```bash
cd /tmp/branching-demo-fresh
gh pr list --state open --json number --jq '.[].number' | xargs -I {} gh pr close {} --delete-branch
```
