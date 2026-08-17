# Task: Email Smoke Tool, Warm-Up, and Cutover Verification

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

This task also owns the warm-up, because the first bulk send after cutover goes
to a list that is 63% dormant.

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

### The stale-list problem, measured
Of 668 distinct forum topic subscribers:

| Last login | Subscribers |
|---|---|
| 8+ years / never | **231** |
| 3–8 years | 191 |
| 1–3 years | 94 |
| under 1 year | 152 |

**63% are three or more years dormant.** A meaningful fraction of those
addresses are dead. Postmark auto-suppresses hard bounces, but a burst of them
on a brand-new account is exactly what triggers a provider review — and a
suspension takes registration and password-reset mail down with it.

Peak day in two years was 239 notification emails, so a busy day can put a
few hundred messages into the pool at once. The warm-up is not optional.

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

9. **Warm up the notification list rather than sending to all 668 at once.**
   Send to recently-active subscribers first, watch the Postmark bounce and
   suppression counts, and widen only if they stay low. The 231 subscribers
   dormant 8+ years should be last, or pre-pruned.

10. **Watch Postmark's bounce and complaint rates through the first week**, and
    define in advance what number triggers stopping. Deciding the threshold
    after seeing a scary number is how a warm-up becomes a suspension.

11. **Re-verify against the old server's failure modes.** Confirm from real
    headers that the message no longer HELOs as `jaguar.deathofagremmie.com`,
    that reverse DNS forward-confirms, and that the `Message-ID` no longer
    carries the dead domain — the three defects found in the 2026-08-12 capture.

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
7. Begin the graduated warm-up; monitor bounce and suppression counts daily.
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
- **Given** the first week after cutover
  **Then** Postmark's bounce and complaint rates stayed under the threshold set
  **in advance**, and the warm-up widened only as they held
- **Given** the suite under `docker_test`
  **Then** it is green, and the tool's own tests are included

## Metadata
- **Complexity**: Medium — the tool is straightforward; the verification
  discipline and the warm-up are the substance
- **Labels**: Email, Verification, Smoke Test, Deliverability, Postmark,
  Tooling, Step 16
- **Required Skills**: Reading `Authentication-Results` and `Received` headers,
  SMTP delivery semantics, IP warm-up practice, writing a tool that is honest
  about what it cannot check
