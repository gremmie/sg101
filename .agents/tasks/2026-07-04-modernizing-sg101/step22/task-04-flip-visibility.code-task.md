# Task: Flip the Repository Public, and Close Step 22

## Description
With the audit passed, the exposure review decided and the licence settled,
make `github.com/gremmie/sg101` public, harden its GitHub settings for a public
repo, confirm it from outside, and close Step 22 — the plan's last step.

## Background
**The ordering is the whole point** (`plan.md` Step 22): audit, then licence,
then visibility. Making a repo public is close to irreversible in effect —
clones, forks and caches outlive a switch back to private — so every
precondition is checked against the record, not assumed.

**What changes for a public repo on GitHub:**
- **Secret scanning and push protection** are free for public repos and catch a
  future slip at push time, which is cheaper than another audit.
- **Actions on pull requests from forks:** a public repo accepts PRs from
  anyone, and `.github/workflows/ci.yml` runs on every push and PR. Fork PRs get
  no repository secrets by default, but they do get runner time; the setting
  that requires approval before running workflows for outside contributors
  should be confirmed.
- **leopard's deploy key** (GitHub ID 164483639) is read-only and unaffected;
  leopard keeps pulling over SSH.
- **Dependabot alerts** and the dependency graph become visible to everyone.

**GitHub settings are changed only after naming the change and getting Brian's
yes**. The visibility switch itself is
Brian's to make or to approve explicitly at the moment.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§2.5 R13, C2 — version control & CI)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step 22
- `STATUS.md` — Step 22 tasks 01–03
- `AGENTS.md`, `README.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Preconditions read from `STATUS.md`, each cited:** task 01 passed with
   every finding resolved; task 02's decisions carried out, including any
   rewrite and leopard's recovery from it; task 03's licence committed. If any
   is missing, stop.
2. **A last delta scan** with task 01's exact commands over commits since task
   01's scan, so nothing landed between the audit and the flip unscanned.
3. **Settings changes named and confirmed one at a time** before each is made
   (`gh api` or the web UI): secret scanning on, push protection on, fork-PR
   workflow approval for outside contributors, and any others Brian adds.
4. **The flip**, by Brian or with his explicit approval at the time.
5. **Verified from outside:** a logged-out browser and an unauthenticated
   `git clone https://github.com/gremmie/sg101.git` both work; `LICENSE` shows
   in GitHub's sidebar as the chosen licence.
6. **CI still green** after the flip, on a push (the close-out commit will do),
   watched to completion rather than assumed.
7. **leopard still pulls:** a `git fetch` on leopard over the deploy key
   succeeds (a read, safe over ssh).
8. **Docs updated:** `AGENTS.md` and `README.md` no longer describe the repo as
   private where they do; `.agents/summary/` left as its dated snapshot.
9. **Step 22 closed:** `plan.md`'s Step 22 box ticked and `STATUS.md` updated in
   the same commit, both dated; the modernization plan's checklist complete.
   Memory's planning pointer updated to say so.

## Dependencies
- Tasks 01, 02 and 03 of this step
- Brian, for every GitHub settings change and the visibility switch

## Implementation Approach
1. Check the preconditions in `STATUS.md`; run the last delta scan.
2. Propose the settings changes as a list; make each on Brian's yes.
3. Brian flips visibility; verify from outside.
4. Close-out commit (docs, plan, STATUS), push, watch CI; check leopard fetches.

## Acceptance Criteria

1. **Nothing went public out of order**
   - Given `STATUS.md`'s Step 22 record
   - When the flip's time is compared with tasks 01–03's completion
   - Then all three were complete, and a final delta scan was clean, before it

2. **Public and working**
   - Given the flipped repository
   - When it is opened and cloned without credentials, CI runs on a push, and
     leopard fetches
   - Then all succeed, and GitHub shows the chosen licence

3. **Guarded for the future**
   - Given the confirmed settings
   - When a commit containing a test secret is pushed to a scratch branch, if
     Brian wants push protection shown working
   - Then the push is refused

4. **The plan is complete**
   - Given the close-out commit
   - When `plan.md` and `STATUS.md` are read
   - Then both show Step 22 done with the same date, and no step remains open

## Metadata
- **Complexity**: Low
- **Labels**: GitHub, Public Release, Security, Documentation, Close-out
- **Required Skills**: GitHub settings and API, GitHub Actions, git
