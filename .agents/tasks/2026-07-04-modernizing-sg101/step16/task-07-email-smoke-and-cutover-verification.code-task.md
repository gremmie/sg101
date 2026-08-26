# Task: Email Smoke Tool and Cutover Verification

## Description
Build `tools/email_smoke.py` on the model of `tools/image_smoke.py`, and use it
to prove the migration actually worked — **against the receiver that has been
rejecting this site's mail for years, not merely against a passing test suite.**

The acceptance test for Step 16 is not "the suite is green" or even "Gmail
accepted it." Gmail already accepts this site's mail today, with `dkim=pass` and
`spf=pass`, while Microsoft rejects it. **A verification that only checks Gmail
would have passed before any of this work and will pass after — it cannot
distinguish success from failure.** The test that matters is a real message
arriving in an Outlook/Hotmail inbox, and not in its junk folder.

The graduated warm-up this task used to own was **dropped 2026-08-20 on
measurement** — no path in the tree can produce a burst. What it owns instead is
watching Postmark's bounce dashboard through the first two weeks. See the
Background below.

## Background

### The precedent
Step 15 task 05 built `tools/image_smoke.py` with an opt-in `--s3` flag that
exercises a real round trip against the live bucket rather than mocks, and it
found things mocks could not — the credentials still authenticated after three
years dormant, and `public-read` still succeeded. Same approach here: mocks
verify our code, a real send verifies the world.

### What only a real send can establish
The suite cannot see any of this, because `locmem` never leaves the process:

- whether Postmark accepts the token and the sender signature
- whether DKIM and Return-Path actually verified, versus merely being published
- what `Authentication-Results` a receiver computes — the only direct evidence
  that task 03's DNS work landed
- **whether Microsoft accepts the message**, which is the entire point of Step 16
- whether mail lands in inbox or junk, which no SMTP response reveals

### The stale-list problem, and why the warm-up was dropped — 2026-08-20
Of 668 distinct forum topic subscribers:

| Last login | Subscribers |
|---|---|
| 8+ years / never | **231** |
| 3–8 years | 191 |
| 1–3 years | 94 |
| under 1 year | 152 |

**63% are three or more years dormant**, and this task originally answered that
with a graduated warm-up. **The headcount is the wrong unit.** Dormant members
subscribe to dead topics that never get replied to, so their rows never turn into
mail. Weighted by a year of real posting — 4,186 posts producing 9,041
notification emails — the picture inverts:

| Recipient last logged in | Emails | % | Distinct people |
|---|---|---|---|
| Within 1 year | 7,526 | **83.2%** | 81 |
| 1–3 years | 440 | 4.9% | 17 |
| 3–8 years | 712 | 7.9% | 20 |
| 8+ years | 363 | 4.0% | 15 |

**11.9% of notification mail reaches accounts dormant 3+ years, across 35
distinct addresses** — not the 423 people the headcount implies. And **Postmark
suppresses an address after its first hard bounce**, so exposure is bounded by
distinct addresses rather than by message volume: the ceiling is ~35 bounces
across a full year, and dormant is not dead.

**No burst is reachable.** No mass-mail path exists anywhere in the tree — every
`send_mail` call site sends to a single recipient on an individual event, and
subscriptions are explicit opt-in, so nobody was auto-subscribed by posting.
Fan-out is **median 1** subscriber per topic (mean 1.56, p95 3, max 31) against
~25 notifications a day. A reply to an old thread mails one or two people. The
peak day in two years was **233** notifications (207 within the last 12 months),
which is the one number that argues for staging — but a peak day is spread across
many topics at a median fan-out of one, and suppression still caps each dead
address at a single bounce.

**Decision: no staged send.** Sequencing recently-active members first would be
real work guarding a rate that cannot get high enough to matter. **What replaces
it is watching Postmark's bounce dashboard through the first two weeks**, with
the stop threshold still set in advance — the numbers are small enough to eyeball.

Two caveats stay attached. This measured forum notifications only; PM
notifications (`messages/forms.py:159`) can also reach a dormant member, and
registration and password-reset mail goes to an address the user just typed —
none of them bulk. And the graduated warm-up was **volunteered to Postmark in the
approval request**, so this is doing less than was stated, not more.

### What the site sends, for coverage
Seven paths, after task 04 deletes email-a-friend: registration confirmation
(`accounts/forms.py:230`), forgotten username (`accounts/forms.py:268`), forum
topic notification (`forums/views/subscriptions.py:46`), private-message
notification (`messages/forms.py:158`), contact form (`contact/forms.py:73`),
admin/manager flag mail (`core/functions.py:85,95`), and **password reset**.

**Two of those are not `core.functions.send_mail` callers**, and both are easy
to miss for the same reason — they were listed as wrapper paths in an earlier
draft of this task, which was wrong:

- **Password reset** goes through Django's stock `PasswordResetView`
  (`accounts/urls.py:48-55`), synchronously and outside Celery, unless task 02
  requirement 10 has landed. Exercise it whichever way it is wired, and check
  which way that is before writing the assertion.
- **Django error mail** goes through `AdminEmailHandler` and sends from
  `SERVER_EMAIL`, which task 01 changes from `root@localhost` in this step.
  Exercise it explicitly — it is the channel you need working when something
  else breaks.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `tools/image_smoke.py` — the tool to model, including its opt-in live flag
- `step15/task-05-s3-smoke-tool-and-verification.code-task.md` — the precedent
- `step16/task-03-dns-email-authentication.code-task.md` — the DNS this verifies
- `DOCKER.md` — house conventions for `tools/` scripts

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Build `tools/email_smoke.py` with live sending strictly opt-in**, mirroring
   `image_smoke.py --s3`. The default run must send nothing: it renders each
   template, asserts the headers, and reports — safe to run in CI and by anyone.

2. **Cover all seven sending paths**, rendering each real template rather than a
   synthetic body, so a template that references a removed context variable is
   caught here rather than by a member.

3. **Assert the From addresses are what task 01 established** —
   `no_reply@surfguitar101.com` for five paths, `admin@surfguitar101.com` for
   registration, reset and topic notifications, and `SERVER_EMAIL` for error
   mail. **Assert `SERVER_EMAIL` is not `root@localhost`**; that regression
   would otherwise surface only during an outage.

4. **Assert the email-a-friend URLs are gone**, per task 04 — a smoke tool that
   still knows how to exercise a deleted feature is a smoke tool nobody updated.

5. **On a live run, send to at least three receivers**, and make the second
   mandatory:
   - a Gmail address — the current baseline, which already passes
   - **an Outlook.com or Hotmail address — the actual acceptance test**
   - a mailbox where full headers are readable

6. **Report the parsed `Authentication-Results` for each, not a boolean.** The
   tool should print the `spf=`, `dkim=` and `dmarc=` verdicts it can obtain and
   say plainly whether `dmarc=pass` appeared at all — its absence is how task
   03's DMARC record is confirmed present, and it is the check most easily
   assumed.

7. **Require inbox-versus-junk to be confirmed by a human**, and say so in the
   output. No SMTP response distinguishes them; a tool that implies otherwise
   is worse than one that admits the limit.

8. **Do not put credentials in the tool.** Read the same environment variables
   the application uses.

9. **Watch Postmark's bounce and complaint rates through the first two weeks**,
   and define in advance what number triggers stopping. This is what replaced the
   graduated warm-up (dropped 2026-08-20, above): there is no staged send to
   widen, only a dashboard to read. Deciding the threshold after seeing a scary
   number is how a cutover becomes a suspension.

10. **Re-verify against the old server's failure modes.** Confirm from real
    headers that the message no longer HELOs as `jaguar.deathofagremmie.com`,
    that reverse DNS forward-confirms, and that the `Message-ID` no longer
    carries the dead domain — the three defects found in the 2026-08-12 capture.

    **The first two are already remediated and verified; the third will still
    fail, and that is expected rather than a regression — updated 2026-08-17.**

    - **HELO**: fixed via `smtp_helo_name` and **observed in an Outlook capture**
      (`helo=mail.surfguitar101.com`).
    - **Reverse DNS**: forward-confirms, verified at the authoritative
      nameservers. Note Microsoft's `Received` format is `from <helo> (<ip>)` and
      never shows the PTR, so **do not expect an Outlook header to demonstrate
      this** — Gmail's `from HELO (ptr [ip])` form is the one that does.
    - **`Message-ID`**: **confirmed to come from Django**, not Postfix, so
      neither the interim fix nor Postmark changes it. A *pass* here would need
      explaining — most likely Postmark rewriting the header — rather than being
      taken as the fix. See task 03 Finding 7a and
      `research/email-header-captures.md`.

    **Baseline captures already exist**, so this tool is comparing against real
    data rather than recollection: 2026-08-12 Gmail (pre-remediation) and
    2026-08-17 Outlook (post-interim-fix, pre-Postmark), both in
    `research/email-header-captures.md`. The original failing state can no longer
    be reproduced on the live box, which is why capture 2 was taken when it was.

    **A useful non-obvious baseline number from capture 2:** Microsoft scored the
    message `SCL=3` while still delivering to the Inbox. Authentication was
    perfect and reputation was neutral. **If the post-cutover capture does not
    show that improving, the provider move has not bought what it was meant to
    buy** — so record the SCL, not just the inbox/junk outcome.

## Dependencies
- **Tasks 01, 02, 03** — env plumbing, the backend, and verified DNS.
- Task 04, which removes email-a-friend; the tool must not carry a path for it.
- An Outlook.com or Hotmail test address, created if one does not exist.

## Implementation Approach
1. Write `tools/email_smoke.py` with the default no-send mode; get it green.
2. Add the header and From-address assertions across all seven paths.
3. Create the Outlook/Hotmail test address.
4. After tasks 01–03 land, run with the live flag to the three receivers.
5. Read the full headers by hand for each; record them in STATUS.
6. Confirm inbox versus junk in each mailbox by eye.
7. Watch Postmark's bounce and suppression counts daily through the first two
   weeks, against the threshold set before the first live send.
8. Only after a clean week, let task 03 restore `-all` and escalate DMARC past
   `p=none`.

## Acceptance Criteria
- **Given** `tools/email_smoke.py` with no flags
  **Then** it sends nothing, exercises all seven paths, and exits non-zero on
  any failed assertion
- **Given** the live flag and a configured Postmark environment
  **Then** messages are delivered to all three receivers
- **Given** the message received at Gmail
  **Then** `Authentication-Results` shows `spf=pass`, `dkim=pass` **and
  `dmarc=pass`** — the third being new, since no `dmarc=` clause appeared in the
  2026-08-12 baseline capture
- **Given** the message received at Outlook.com or Hotmail
  **Then** it is **delivered and in the inbox, not the junk folder** — confirmed
  by eye. *This is the acceptance criterion for Step 16 as a whole.*
- **Given** the received headers
  **Then** the HELO name is Postmark's, reverse DNS forward-confirms, and no
  header carries `jaguar.deathofagremmie.com`
- **Given** `SERVER_EMAIL`
  **Then** error mail sends from `admin@surfguitar101.com`, and an assertion
  fails if it is ever `root@localhost`
- **Given** the first two weeks after cutover
  **Then** Postmark's bounce and complaint rates stayed under the threshold set
  **in advance**, read off the dashboard rather than staged around
- **Given** the suite under `docker_test`
  **Then** it is green, and the tool's own tests are included

## Metadata
- **Complexity**: Medium — the tool is straightforward; the verification
  discipline is the substance
- **Labels**: Email, Verification, Smoke Test, Deliverability, Postmark,
  Tooling, Step 16
- **Required Skills**: Reading `Authentication-Results` and `Received` headers,
  SMTP delivery semantics, writing a tool that is honest about what it cannot
  check
