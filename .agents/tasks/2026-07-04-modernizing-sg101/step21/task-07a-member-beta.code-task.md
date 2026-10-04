# Task: Member Beta on beta.surfguitar101.com — a Few Days of Real Use Before the Cutover

## Description
After the dress rehearsal (task 07), leave the rehearsed site up for a few days
at `beta.surfguitar101.com` and invite a handful of members to use it. They log
in with their real accounts against a copy of production. Mail reaches only the
people on an allowlist. Everything they write is discarded, because the cutover
restores a fresh snapshot over it. The output is a list of what testers found,
compiled at the end, and Brian's go/no-go for task 08.

## Background
Task 07 proves the data path and gives numbers, and says of itself that the
result is "not a site anyone uses". Nothing in Step 21 puts the new stack in
front of anyone but Brian before the DNS flip. What testers can catch that the
smoke tools cannot: templates and pages no test visits, their own old posts and
photos rendering, logins with passwords hashed years ago, and the site under a
few people's real use instead of a script.

**Brian's decisions (2026-09-26):** a handful of invited members; a direct link
on a subdomain, `beta.surfguitar101.com`; mail blocked or discarded, by a
setting; testers told up front that everything they do will be lost and
overwritten; a test period of a few days. **The calendar workflow runs end to
end against the real Google Calendar** (submit, approve, Synchronize, event
appears). Brian deletes the beta's events from Google by hand afterwards, and
testers are asked not to edit or delete their existing events.

**The real calendar is the one thing the beta changes that the cutover will not
undo.** Synchronize (`gcalendar/admin.py`, `google_sync`) sends every event in
`Event.pending_events`, meaning every row in `NEW_APRV`, `EDIT_APRV` or
`DEL_APRV`, not only the ones testers created. A `DEL_APRV` row deletes a real
event from Google. Whatever the snapshot brought into those states is sent at the
first sync. Runbook A3's 32 pending rows are already gone: Brian deleted them in
production (reported 2026-09-26; the date of the deletion was not recorded, and
the runbook and task 09 still list it as to do). So the snapshot should bring an
empty queue, unless an event has been approved and not yet synchronized since
then. Brian's approval in
the admin is the gate that matters: an event reaches the pending queue only
through it. The calendar page itself embeds the live Google Calendar in an iframe
(`sg101/templates/gcalendar/index.html`), so a synced beta event appears on the
**live** site's calendar page as well as the beta's, until it is deleted.

**The subdomain needs no new certificate or host setting** (read from the repo
2026-09-26):
- `ALLOWED_HOSTS = ['.surfguitar101.com']` in `production.py` already matches.
- The vhost names only the apex and `www`. Apache serves an unmatched `Host`
  from the first `*:443` vhost, which is this one. Confirm that with the smoke
  test rather than assume it.
- Cloudflare's edge certificate covers one level of subdomain. The Origin CA
  certificate (runbook B5) covers `beta` only if it was issued with the default
  hostnames, `surfguitar101.com` and `*.surfguitar101.com`. Check the one
  installed.
- `SESSION_COOKIE_DOMAIN = None`, so session cookies are per-host. A tester's
  beta session and live session do not share a cookie.
- HSTS is sent without `includeSubDomains` (`production.py`), so it does not
  affect the subdomain.

**Mail is the dangerous part, and the site will generate plenty of it.**
Testers will post and send private messages, and each of those notifies real
subscribers and recipients through `core.tasks.send_mail`. One path skips that
function: Django's `mail_admins`, called by `AdminEmailHandler` for error mail.
*(Corrected 2026-10-01: this said Django's password reset and `email_admins`
skip it too. Both go through `core.functions.send_mail`, password reset since
Step 16's `SitePasswordResetForm`; `tools/email_smoke.py`'s `UNWRAPPED_PATHS`
lists only the error mail.)* `tools/email_smoke.py` names all ten. The one place
every path passes through is `EMAIL_BACKEND`, which production already reads
from the environment. So the setting belongs there: a backend that filters recipients
against an allowlist, not a check in `send_mail`, which would miss the other
paths. Task 07's console backend blocks everything. The beta needs mail to reach
testers, because registration, password reset and notifications are among the
things worth testing.

**`Site.domain` is `surfguitar101.com`, and mail and pages build absolute links
from it** (`forums/views/subscriptions.py`, `messages/forms.py`,
`core/functions.py`, `core/templatetags/core_tags.py`, `donations/views.py`). Left
alone, a notification sent to a tester links to jaguar. Changing the row on the
beta database fixes the links. The fresh snapshot at C1 restores the original
row. The change has two side effects:
- `email_admins` sends from `no_reply@<site.domain>`, so admin mail would come
  from `no_reply@beta.surfguitar101.com`. Postmark may refuse a sender outside
  the verified domain, and DMARC alignment for the subdomain is unverified. Find
  out which by sending one.
- `donations/views.py` passes the domain to PayPal. **A donation on the beta is
  real money**, and its IPN comes back to a database that will be discarded.

**Anyone can reach the hostname, not only the people with the link.** It is a
public DNS name. The site offers registration, and bots find new hostnames. The
copy holds nothing a logged-out visitor can't already see on the live site, but
a stranger could register there, spam it, or have it indexed as a duplicate of
the real site.

## Decisions (Brian, all settled 2026-09-26)
1. **Who can reach the site — DECIDED 2026-09-26: Cloudflare Access.** The
   alternative was the link alone, plus `noindex`, accepting that strangers may
   wander in. With Access, testers open the link, type their email address and
   get a one-time code that Cloudflare sends, not the site. The testers'
   addresses form one list that serves both the Access policy and the mail
   allowlist, and strangers never reach the registration form. The cost is one
   extra step for testers. **Set up so far (Brian, 2026-09-26):** a Zero Trust
   organization on the Free plan (up to 50 users), team name `sg101-beta`, so
   the login page is `sg101-beta.cloudflareaccess.com`. **No application
   exists yet**; requirement 7 creates it.
2. **Donations — DECIDED 2026-09-26: testers are told not to donate.** The
   alternative was pointing the beta at the PayPal sandbox by making
   `DONATIONS_DEBUG` readable from the environment (it is hard-coded `False` in
   `base.py`); no code changes for this. The instruction is the only safeguard,
   so the invitation says it plainly and teardown checks that no donation
   arrived.
3. **What stops the cutover — DECIDED 2026-09-26: Brian decides, from a list
   compiled at the end.** Testers report problems during the period; at the end
   they are compiled into one list, and Brian may file them as GitHub issues on
   the repo. Brian then decides which delay task 09. **Likely to delay it:**
   critical problems with login or registration, any Django crash (a 500), and
   serious template rendering failures. Everything else is expected to go to the
   list for after the cutover.

## Testers

**Volunteered (recorded 2026-10-01, Brian):** Fady, Kojack, Emilien03,
kick_the_reverb and synchro, by site username. Their email addresses are not
recorded here; they come from each account when the Access policy and the mail
allowlist are built (requirement 7).

## Reference Documentation
**Required:**
- `.agents/tasks/2026-07-04-modernizing-sg101/step21/task-07-dress-rehearsal.code-task.md`
  — this task starts from its end state and reuses its safety blocks

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — B3, B5,
  B6 (the temporary firewall rule), D3
- `tools/email_smoke.py` — the ten mail paths, used here to prove the allowlist
- `core/tasks.py` — `log_send` and the `email` logger, which the backend's drop
  log should match
- `contact/tests/test_views.py` or `antispam/tests/test_turnstile.py` — the
  pattern for re-enabling logging in tests

## Technical Requirements
1. **An allowlisting email backend, in `core`,** chosen by `EMAIL_BACKEND` and
   configured by a new `EMAIL_ALLOWLIST` setting read from the environment (a
   comma-separated list). It subclasses Django's SMTP backend. It removes every
   `to`/`cc`/`bcc` address not on the list, matching case-insensitively, and
   drops any message left with no recipients. Each removed address is logged to
   the `email` logger. **It fails closed:** an empty or missing allowlist drops
   everything and sends nothing. It is not the default in any settings module,
   and `.env.example` documents it next to `EMAIL_BACKEND`.
2. Tests written first, and each one seen to fail against a mutation it is meant
   to catch. Cover: a mixed recipient list keeps only listed addresses, in all
   three fields; a message with no listed recipients is not sent; an empty list
   sends nothing; matching ignores case; drops are logged. The suite and the
   deprecation gate both pass.
3. **Crashes are collected by the site as well as by testers.** A 500 on the
   beta reaches Brian through `AdminEmailHandler` (`ADMINS` is on the allowlist)
   and is written to `sg101.log`. At the end of the period, read `sg101.log`
   and the error mail for the whole period and add every distinct traceback to
   the list, whether or not a tester reported it. Keep it within `sg101.log`'s
   ~100 KB x 10 rotation; a few days fits.
4. On the beta host: `EMAIL_BACKEND` set to the allowlisting backend,
   `EMAIL_ALLOWLIST` set to the testers' addresses plus `ADMINS`, and the real
   Postmark token in place, so allowlisted mail goes out for real. The real
   Google Calendar key is installed and `GCAL_CREDENTIALS_PATH` set to it
   (runbook B1). This undoes task 07's calendar block. Restart the stack,
   including the worker and beat (runbook C4a), so every process reads the new
   settings.
4a. **Before the key is installed, confirm the beta's sync queue is empty.**
   Count `Event.pending_events` on the beta database and record the number. It
   is expected to be zero, since A3 is done, and the count is also what confirms
   A3 from a real snapshot. Any row that is there anyway (`DEL_APRV` above all)
   is resolved on the beta before the first Synchronize, by moving it back to its
   unapproved status or deleting it. That change is discarded at C1. The admin sync page lists what it will send, so
   read that list before every press. Approve only events testers created.
5. **Prove the allowlist on the host before inviting anyone.** Run
   `tools/email_smoke.py --live` to one address on the list and one address Brian
   owns that is not. The first receives mail and the second receives nothing,
   shown in Postmark's activity log as well as the inbox. Include the
   `email_admins` path, to settle the `no_reply@beta` question.
6. `Site.domain` set to `beta.surfguitar101.com` on the beta database only. A
   notification a tester receives links to the beta.
7. DNS: a proxied `beta` record pointing at leopard; unproxied would bypass
   Access. A self-hosted Access application on `beta.surfguitar101.com` in the
   `sg101-beta` organization: one Allow policy that includes the testers' emails
   and Brian's, One-time PIN login, 24-hour session. Check it from a browser
   with an address not on the list: no code arrives and the site is not
   reached.
   `noindex`, whether or not Access is used: an `X-Robots-Tag` header set by a
   Cloudflare rule, so nothing in the repo changes. `tools/prod_smoke.sh` passes
   against the hostname. Turnstile works on registration and the contact form
   there, because a widget's hostname list may not include the subdomain.
8. **The invitation**, drafted and sent by Brian. It covers: everything done on
   the beta is thrown away; mail from the beta is real mail but reaches only
   testers; **don't donate** — the donation page is live PayPal and the money
   would be real; adding a calendar event is
   welcome and will appear on the real calendar until Brian removes it, but
   **don't edit or delete events you already have**; the dates; where to report
   problems.
9. **The findings**, compiled into one list at the end of the period from
   testers' reports and requirement 3's tracebacks, and summarized in
   `STATUS.md`. Brian may file them as GitHub issues; if so, `STATUS.md` links
   them rather than repeating them. Each is marked **blocks cutover** or
   **after cutover** by Brian, using decision 3. A blocking fix is deployed to
   the beta (or to the rehearsal host) and checked there, not only in the
   suite, before task 09.
10. **Teardown before task 09, added to task 09's "undo the rehearsal's safety
    blocks" list:** the `beta` DNS record and the Access application removed (the
    `sg101-beta` organization can stay: it is free and serves nothing without an
    application);
    `EMAIL_BACKEND` and `EMAIL_ALLOWLIST` removed from `.env`; no donation
    recorded on the beta since the snapshot (a count of `Donation` rows) and none
    in PayPal (the row count cannot catch one: PayPal sends a beta donation's IPN
    to jaguar, as it did Kojack's on 2026-10-04, so PayPal's list is the check);
    beta uploads cleaned out of the S3 bucket; `https://beta.surfguitar101.com/*`
    removed from the Google Maps key's website restrictions (added 2026-10-03
    so the band map would draw); Cloudflare's `X-Robots-Tag: noindex` response
    header rule for the `beta` hostname deleted, and the hostname removed from
    Turnstile's widget (both added for requirement 7). **Calendar:**
    before the beta database is overwritten, list every event it put on Google
    (`status=ON_CAL` rows whose `google_id` is not in production's, or created
    after the snapshot), then delete each one from Google by hand. This list is
    the only record of them; after C1, nothing in the site's database refers to
    them. The key itself stays, because production needs it. The `Site` row
    needs no action, because C1's restore replaces it; task 09's smoke should
    still read it once.

## Dependencies
- Task 07 complete: the site restored, synced and serving on a test hostname
  with mail blocked. This task renames that hostname to `beta` or adds `beta`
  alongside it.
- Task 05's backups running, since the host holds real data for days rather than
  hours.
- Task 06 need not be finished. That also means no fail2ban on the beta; Access
  (decision 1) is what covers the gap.

## Implementation Approach
1. Build and test the backend (TDD); leave the changes uncommitted for
   review.
2. Configure the host, then prove the allowlist (requirement 5) before any
   invitation is sent.
3. Set up DNS, Access and `noindex`; smoke-test.
4. Invite, and run for the agreed days.
5. Compile the list (requirements 3 and 9); Brian marks each item.
6. Tear down (requirement 10) and hand the go/no-go to task 08.

## Acceptance Criteria

1. **Mail reaches testers and no one else**
   - Given the allowlisting backend with the testers' addresses
   - When a tester's post notifies subscribers who are not testers, and the smoke
     sends to an address not on the list
   - Then Postmark's activity log shows mail only to listed addresses, and the
     `email` log records each dropped recipient

2. **The backend fails closed**
   - Given `EMAIL_BACKEND` set to the allowlisting backend with no allowlist
   - When any mail path sends
   - Then nothing is sent, as proven by a test seen to fail when the empty-list
     case is mutated to allow all

3. **Testers can use the site as themselves**
   - Given an invited member with an account on the live site
   - When they open the link and log in with their existing password
   - Then they reach their own profile, posts and photos, and links in the mail
     they receive point at the beta

4. **Nothing on the beta costs anyone anything**
   - Given the beta's donation page
   - When a tester follows it
   - Then the invitation told testers not to donate, and at teardown the beta
     holds no donation recorded since the snapshot

5. **Every finding has a decision**
   - Given the test period has ended
   - When the compiled list (in `STATUS.md`, or GitHub issues linked from it) is
     read
   - Then it includes every distinct traceback from `sg101.log`, each item is
     marked blocks cutover or after cutover, and every blocking item is fixed
     and checked on the host before task 09

6. **The real calendar changes only by what testers added**
   - Given the snapshot's pending rows were resolved before the first sync
   - When a tester's event is approved and synchronized
   - Then it appears on the real calendar, and no event that existed before the
     beta was changed or removed

7. **Nothing from the beta survives into the cutover**
   - Given the teardown
   - When task 09 starts
   - Then the `beta` record and the Access application are gone, `.env` holds no
     allowlist, every event the beta added to Google has been deleted there, and
     task 09's undo list names every item this task added

## Metadata
- **Complexity**: Medium
- **Labels**: Cutover, User Testing, Email, Cloudflare
- **Required Skills**: Django email backends, Cloudflare DNS and Access, Postmark
