# Task: Review What Else Goes Public — Personal Data, Infrastructure Detail, Branches and Issues

## Description
List, by kind, everything other than credentials that becomes public when the
repository does, and have Brian decide what happens to each kind before the
flip. **This task is an addition to the plan** (Brian, 2026-10-23): `plan.md`'s
Step 22 gates the flip on secrets alone.

## Background
**A credential scan answers one question; going public asks a wider one.** The
repo was private for its whole git life, and its records were written that way.
`.agents/` in particular is a detailed operational log, and it names:
- **Members and testers** by username (the five beta testers, a member whose
  uploads explained the ` fog` rows), and possibly by real name or email.
- **Client IP addresses**, e.g. the block-list entries quoted in Step 21 task
  10's watch rows; `sg101-evidence/` was kept *outside* the repo precisely
  because it holds client IPs.
- **Infrastructure identifiers:** leopard's address, Linode firewall and
  instance IDs, the Zero Trust org, the calendar service account's address, S3
  bucket and IAM user names, admin mail addresses.
- **Traffic and abuse analysis** — crawler fingerprints, ban thresholds, which
  checks registration spam fails — that is useful to an abuser.

Elsewhere in the tree: `*/fixtures/*.json` (are any drawn from production?),
`archive/wiki/` (the wiki's content, public once already), test data, and
comments quoting real rows.

**Beyond the tree:** the three non-`main` branches (`multi-upload`, `v3-dev`,
`abandoned-2015`) and three tags publish with it; so do **GitHub issues** (#5
onward), their comments and any attachments, and the Actions logs of past runs.

**Not every item needs action**, and much is already public (the site's own
pages show usernames). The point is that each kind gets a decision rather than
being published by default. Record the options and let Brian choose; don't
settle one by picking it in passing.

**The options per kind** are roughly: keep as is; redact going forward only
(history keeps it); scrub from history with `git filter-repo`; drop a branch or
tag; close/edit/delete issues; or, for `.agents/` as a whole, move it out of the
public repo. Any history rewrite is batched with task 01's into **one** rewrite,
done before task 03, because it changes every hash — including the
`cutover-2026-10-07` tag that STATUS cites by commit, and leopard's clone at
`/svr/sg101`, which needs a re-clone or `reset` against the new history.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§2.5 R13, C2 — version control & CI)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — Step 21 task 10's
  watch rows, the densest source of IPs and traffic detail
- Task 01 of this step, for any non-credential items it noted in passing

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Inventory by kind, measured:** for each kind above, how many occurrences,
   in which paths, and on which refs (current tree vs history only). Counts come
   from a search, with the pattern recorded — not from recollection. IPv4/IPv6
   literals, email addresses, and the usernames recorded in STATUS are searched
   for directly.
2. **Fixtures checked** against their origin: production-derived or
   hand-written, and whether any real member's data or password hash is in them.
3. **Each non-`main` branch and tag** described in one line (what it is, last
   commit date) with a keep/drop question for Brian.
4. **GitHub issues and past Actions logs** reviewed for anything not fit to
   publish (`gh issue list --state all`, `gh run list`); findings listed.
5. **The inventory is not republished in a public place:** it lives in the
   scratchpad and in Brian's hands; what goes into `STATUS.md` is the counts and
   the decisions, not the IPs and names themselves.
6. **Brian decides per kind**; each decision recorded in `STATUS.md` under a
   Step 22 task 02 section.
7. **Decisions carried out** that do not rewrite history (forward redactions,
   issue edits, branch or tag deletions, a `.agents/` move), each on its own
   commit, and the suite run if any tracked code or fixture changes.
8. **If any rewrite is chosen** (here or in task 01), it is planned here as one
   `git filter-repo` invocation over a fresh mirror clone, with: the exact
   paths/replacements, a dry run's diff summary, the tags re-pointed, the
   force-push, leopard's re-clone steps (Brian runs them), and STATUS's commit
   citations noted as pre-rewrite hashes. Execution only after Brian approves
   that plan.

## Dependencies
- None technical; can run before or after task 01, but any rewrite waits for
  both
- Brian, for every decision; force-pushes and GitHub deletions confirmed first
  by naming the change before making it

## Implementation Approach
1. Search the tree and history for each kind; build the inventory in the
   scratchpad.
2. Review branches, tags, issues and Actions logs.
3. Present the inventory by kind with options; take Brian's decisions.
4. Carry out the forward-only changes; if a rewrite is chosen, write its plan
   and stop for approval.

## Acceptance Criteria

1. **Every kind has a decision**
   - Given the inventory of personal data, infrastructure detail, abuse
     analysis, fixtures, branches, tags, issues and logs
   - When Brian reviews it
   - Then each kind has a recorded decision, and none is published by default

2. **The review does not publish what it found**
   - Given the inventory's contents
   - When `STATUS.md` is updated
   - Then it holds counts and decisions only, not the addresses or names

3. **Fixtures hold no real member data, or it is decided**
   - Given each fixture file
   - When compared against its origin
   - Then it is shown hand-written or synthetic, or Brian has decided its fate

4. **One rewrite, planned before run**
   - Given any history scrub chosen in task 01 or here
   - When the rewrite is prepared
   - Then it is a single, dry-run plan covering both tasks, approved by Brian,
     with leopard's recovery steps written out

## Metadata
- **Complexity**: Medium
- **Labels**: Privacy, Public Release, Git History, GitHub, Documentation
- **Required Skills**: git history search, git-filter-repo, GitHub CLI, judgment on PII
