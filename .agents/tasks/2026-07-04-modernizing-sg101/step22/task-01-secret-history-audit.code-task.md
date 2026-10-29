# Task: Secret-History Audit #2 — the Gate Before the Public Flip

## Description
Scan the whole git history, every branch and tag, for credentials before
`github.com/gremmie/sg101` is made public. Triage each finding, rotate anything
live and confirm it dead, and settle per finding whether history is rewritten.
**Nothing else in Step 22 proceeds until this passes.**

## Background
**Audit #1 covered the converted history only**, on 2026-07-15 (Step 2,
`STATUS-archive-steps-01-15.md`): `gitleaks` found 5 historical hits,
`trufflehog` 0 verified live, all 2009–2015 and all benign — four client-side
Google Maps keys (public by design) and one dead 2011 OAuth consumer key with no
committed secret material. Nothing was rotated, and the record closes with
*"re-check at audit #2 before any public flip."*

**Everything committed since is unscanned, and that is where the risk
concentrated.** Step 3 (`8f752f16`, 2026-07-15) moved every secret into
environment variables, so the 548 commits from it onward (every ref,
`git rev-list --count --all ^8f752f16^`, 2026-10-23) touched settings modules,
`.env.example`, CI, compose files and host config — each a chance for a real
value to land where a placeholder belonged. Re-scan that delta **and** run a
final full pass; a delta-only scan assumes audit #1 was perfect.

**Files that hold, or held, secrets locally and must never have been tracked:**
`.env`, `secrets/` (the calendar service account key, git-ignored as a whole
directory and not backed up anywhere), the old `secrets.json`, and the real
counterparts of the committed `backup/backup.env.example` and
`fail2ban/cloudflare.env.example`. `firewall/settings.env` *is* tracked, by
design, and its tool refuses `LINODE_TOKEN` in it — confirm that has held over
its whole history, not just the current file. Credentials that have existed in
this project at some point include: Django `SECRET_KEY`, DB passwords, AWS keys
(app and backup IAM user), Postmark server token, Turnstile and older reCAPTCHA
keys, the Cloudflare Global API Key (rolled 2026-10-22) and scoped tokens, the
Linode firewall token, healthchecks.io ping URLs, and the Google service-account
key.

**Public exposure covers every ref**, not just `main`: `multi-upload`, `v3-dev`,
`abandoned-2015` and the tags `cutover-2026-10-07`, `pre-step-4-prune`,
`rollout` are all on GitHub. Scan `--all`.

**Rotation is not removal.** Rotating kills an exposed credential; the old value
stays in history. Physically removing one needs `git filter-repo`, which rewrites
every hash — including the cutover tag and leopard's clone at `/svr/sg101`, whose
next `git pull` would then fail. **Decide per finding, not as a policy**, and if
any rewrite is chosen, batch it with task 02's into one rewrite.

**Non-credential exposure** — member names, IPs, email addresses in `.agents/`
and fixtures — is task 02's, not this task's. Note anything seen in passing for
it; don't triage it here.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§2.5 R13, C2 — version control & CI; §7 risks — secret exposure)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/vcs-migration.md` —
  *Secret hygiene — TWO audits* (the audit's definition)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS-archive-steps-01-15.md` —
  Step 2, *Secret audit #1*
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step 22

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **The scanners are shown to work before their silence counts.** In a
   throwaway clone in the scratchpad, commit a planted fake credential of a kind
   this project uses (an AWS key pair shape, a Postmark-style token) on a
   non-`main` branch, and confirm both `gitleaks` and `trufflehog` report it
   when run the same way as the real scan. Record versions and exact commands.
2. **Delta scan:** every commit reachable from any ref and not reachable from
   `8f752f16^`, with both tools.
3. **Full scan:** the whole history of every ref, with both tools;
   `trufflehog` with verification on, so a live hit is distinguished from a
   pattern match.
4. **Ignored files never tracked:** `git log --all --diff-filter=A --name-only`
   (or equivalent) shows no commit ever adding `.env`, anything under
   `secrets/`, `secrets.json`, `backup/backup.env`, `fail2ban/cloudflare.env`,
   or a key or certificate file (`*.pem`, `*.key`, `*.p12`, service-account
   JSON). The origin certificate and key from runbook B5 are included.
5. **`firewall/settings.env` audited over its history:** no version ever held a
   token.
6. **`.gitignore` verified against the tree:** `git ls-files -ci
   --exclude-standard` is empty, and every local secret file on the Mac
   (`.env`, `secrets/…`) is reported ignored by `git check-ignore`.
7. **Every finding triaged** in a table — commit, path, kind, live/dead/public
   by design, and how that was established. Audit #1's five are re-checked, not
   carried over.
8. **Any live credential rotated** and the old value shown refused by its
   service. Where a credential cannot be tested (as with task 11's Global key),
   say so rather than claiming it dead.
9. **Brian decides, per finding, rotate-only or rotate-and-scrub.** The
   decision and its reason recorded; no rewrite is performed in this task.
10. **Brian decides whether the audit stays in the repo**: a committed
    `.gitleaks.toml` allowlisting the triaged benign findings, and/or a CI scan
    job. Either is optional; present the choice, don't make it.
11. Results recorded in `STATUS.md` under a Step 22 task 01 section, with the
    measurements; raw scanner output kept in the scratchpad, not committed
    (it would republish what it found).

## Dependencies
- Step 21 closed (done 2026-10-23)
- `gitleaks`, `trufflehog`, `git-filter-repo` (all installed via Homebrew on the
  Mac)
- Brian, for rotations in each service's console and the scrub decisions

## Implementation Approach
1. Record tool versions; build the planted-secret clone and prove detection.
2. Run the delta then the full scan, both tools, over `--all`; save output to
   the scratchpad.
3. Run the never-tracked and `.gitignore` checks.
4. Triage into one table; for any live hit, stop and raise it with Brian at
   once rather than finishing the scan first.
5. Present findings and the scrub and keep-the-audit decisions; record what
   Brian chose.

## Acceptance Criteria

1. **The scan is shown able to fail**
   - Given a clone with a planted fake credential on a side branch
   - When both scanners run with the audit's exact commands
   - Then both report it, and those commands are the ones used for the real scan

2. **Clean history, or every finding accounted for**
   - Given the delta and full scans over every ref
   - When the results are triaged
   - Then each finding is dead, public by design, or rotated and shown refused

3. **Secret files never tracked**
   - Given the list of local secret files and key-file patterns
   - When the history of every ref is searched for their addition
   - Then no commit ever added one, and `git check-ignore` covers each on disk

4. **Decisions are Brian's and recorded**
   - Given the triaged findings
   - When rotate-only vs scrub, and keep-a-config vs not, are settled
   - Then each choice and its reason is in `STATUS.md`, and no history has been
     rewritten by this task

## Metadata
- **Complexity**: Medium
- **Labels**: Security, Secrets, Git History, Audit, Public Release
- **Required Skills**: gitleaks, trufflehog, git internals, credential rotation
