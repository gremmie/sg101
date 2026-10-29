# Task: Settle the Licence, and Make Every Statement of It Agree

## Description
Confirm the project's licence with Brian, make `sg101/package.json` and any
other licence statement agree with the `LICENSE` file, check that vendored
third-party code keeps its own notices, and correct the plan's claim that no
`LICENSE` exists.

## Background
**The plan is wrong on its premise.** `plan.md` Step 22 says "the repo has none,
so it is 'all rights reserved' by default." It has one: `LICENSE`, added
2009-04-19 (`7b97ffb3`), **BSD 3-clause**, "Copyright (c) 2009, Brian G. Neal".
So the work is confirming a choice that was made in 2009 and never revisited,
not making one from nothing. **Which licence is Brian's call** — keep BSD
3-clause, change it, or go proprietary — and so is whether the copyright line
gets a year range or a different holder.

**`sg101/package.json` contradicts it:** `"license": "ISC"`, npm's `npm init`
default carried since 2016, not a decision. On a public repo it becomes the
de facto answer for anyone who reads it. For BSD 3-clause the SPDX identifier is
`BSD-3-Clause`; if the code were to stay proprietary, `"UNLICENSED"`, which pairs
with the `"private": true` already there.

**Third-party code in the tree carries its own licences**, and a public repo
redistributes it: front-end libraries the two page designs use (Foundation 6,
jQuery, Blueprint, markItUp, TinyMCE and others under `static/` and
`sg101/static/`), anything vendored from Python packages (the `elsewhere` fork,
any vendored apps), fonts, and the smiley images. The project's licence does not
cover these; each needs its own notice kept where it already is. This task
checks they are present, it does not relicense anything.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C2 — version control & CI)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step 22,
  item 2
- `LICENSE`, `sg101/package.json`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Task 01 has passed, and any history rewrite from tasks 01–02 is done, so
   this commit lands on the final history.
2. **Brian chooses the licence and the copyright line**; the choice recorded in
   `STATUS.md` under a Step 22 task 03 section.
3. `LICENSE` reflects that choice; `sg101/package.json`'s `license` is its SPDX
   identifier (or `UNLICENSED`).
4. **Every other licence statement found and made to agree:** a search of the
   tree for `license`/`licence` fields and headers in project-owned files
   (`package.json`, any `pyproject.toml`/`setup.py`/`setup.cfg`, README,
   file headers). Third-party files' own headers are not touched.
5. **Vendored third-party code inventoried:** each library or asset that is not
   project-owned, where it lives, and whether its licence notice is in the tree.
   Any missing notice is listed for Brian; restoring one is in scope, removing
   or replacing the library is not.
6. `npm run build:css` is not needed (no Sass changes); if `package-lock.json`
   carries the root package's licence, it is updated in the same commit
   (`npm install --package-lock-only` in `sg101/`, or by hand if that changes
   anything else).
7. **`plan.md` Step 22's wording corrected** where it says no `LICENSE` exists,
   in the same commit, so the plan and the tree agree.

## Dependencies
- Task 01 (the gate) passed; task 02's decisions carried out, including any
  rewrite
- Brian, for the licence and copyright choice

## Implementation Approach
1. Search for licence statements and vendored code; build both lists.
2. Present the current state and the options; take Brian's choice.
3. Edit `LICENSE`, `package.json` and any other project-owned statement; fix
   the plan's wording.
4. Run the suite (cheap insurance for the `package.json` edit) and commit.

## Acceptance Criteria

1. **One licence, stated consistently**
   - Given Brian's choice
   - When `LICENSE`, `sg101/package.json` and every other project-owned licence
     statement are read
   - Then they all name the same licence

2. **Third-party notices are intact**
   - Given the inventory of vendored code and assets
   - When each is checked
   - Then each has its own licence notice in the tree, or the gap is listed and
     Brian has decided it

3. **The plan matches the tree**
   - Given the corrected `plan.md`
   - When Step 22 is read
   - Then it no longer claims there is no `LICENSE`

## Metadata
- **Complexity**: Low
- **Labels**: Licensing, Public Release, Documentation
- **Required Skills**: open-source licensing, SPDX, npm package metadata
