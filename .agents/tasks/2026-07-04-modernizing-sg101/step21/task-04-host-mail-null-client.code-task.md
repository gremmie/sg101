# Task: Send-Only Mail from the Host, Proven by a Failing Cron Job

## Description
Give the VM a send-only mail client, so mail from cron, logrotate, automatic
updates and the backup timer reaches `bgneal@gmail.com` through Postmark.
Rewrite the sender as well as the recipient, check which outbound ports actually
work, confirm nothing listens on 25, and **prove it by making a job fail and
seeing the message arrive**.

## Background
Step 16 moved the *application's* mail to Postmark through environment
variables. Mail the *host* generates is separate: with no mail program installed
it is discarded silently, which is how a failing backup goes unnoticed. jaguar
lost every root message, certbot warning and Django traceback for years that
way, until Step 16 task 10 fixed its sender on 2026-08-18.

**Four parts, each recorded in `plan.md` Step 21 (*outgoing mail on the new VM*):**
- **The client itself** — `msmtp`, or Postfix as a null client. It
  reproduces jaguar's `/etc/aliases` (`root`, `brian`, `www-data` → Gmail).
  Cloudflare Email Routing does not cover this: it only handles mail arriving
  from the internet.
- **The sender.** Cron mail leaves as `root@<hostname>`, and Postmark refuses any
  From address that is not a verified domain or sender signature ("not a Sender
  Signature on this account"). Rewrite it to an address on
  `surfguitar101.com` — the same `sender_canonical` fix applied to jaguar.
- **Egress.** Linode blocks outbound port 25 by default; some providers also
  restrict 587. Postmark accepts **2525** as an alternative. Test from the VM.
  The failure mode is silent queueing.
- **No inbound path.** Nothing listens on 25, and the VM has no MX record.

**`tools/email_smoke.py` proves the application's mail, not this.** Run it from
the VM anyway (it proves the host's egress for the app), but the host's own
mail needs its own proof.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C8 — email → transactional provider)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step
  21, *ALSO CARRIES: outgoing mail on the new VM*
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — Step 16 task 10,
  the `sender_canonical` fix on jaguar
- `tools/email_smoke.py`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Pick `msmtp` or a Postfix null client and give the reason. Either must accept
   mail through `sendmail`, since that is what cron and the other system jobs
   call.
2. Mail to `root`, `brian`, the admin account and `www-data` goes to
   `bgneal@gmail.com`.
3. The envelope sender and the From header are rewritten to a
   `surfguitar101.com` address Postmark accepts.
4. The Postmark credential lives in a root-only file on the host. It can be a
   separate Postmark server token from the application's, so each can be
   revoked alone; record which was chosen.
5. The working submission port is measured from the VM (587, then 2525), and the
   result recorded.
6. `ss -ltn` shows nothing listening on 25, on any address.
7. The backup timer from task 05 and logrotate's failures reach Gmail through
   this path; check how each reports failure.

## Dependencies
- Task 03 (the VM exists)
- Postmark account access, for the credential and to see the message in the
  activity log

## Implementation Approach
1. Test egress first with a plain connection to Postmark's SMTP host on each port.
2. Install and configure the client, the aliases and the sender rewrite.
3. Send one message by hand with `sendmail`, and read its headers in Gmail
   (`dkim=pass`, `spf=pass`, the rewritten From).
4. Install a cron entry that fails on purpose (`false` with output), wait for
   it, confirm the mail arrives, then remove the entry.
5. Record everything in `STATUS.md`.

## Acceptance Criteria

1. **A failing job reaches the inbox**
   - Given a cron entry that exits non-zero with output
   - When it runs
   - Then the message arrives in `bgneal@gmail.com`, and Postmark's activity log
     shows it accepted

2. **The sender is accepted**
   - Given mail submitted as `root`
   - When it reaches Postmark
   - Then it is not refused as an unknown sender signature, and its headers show
     `dkim=pass` and `spf=pass`

3. **No inbound mail path**
   - Given the configured host
   - When listening sockets are listed
   - Then nothing listens on port 25, and DNS has no MX pointing at the VM

4. **Egress is measured**
   - Given the VM
   - When connections are tried to Postmark on 587 and 2525
   - Then which works is recorded, and the client uses one that does

5. **Breaking the config is noticed**
   - Given a deliberately wrong credential
   - When the failing cron job runs again
   - Then the failure is visible somewhere Brian would look (client log, Postmark,
     or the absence of the message), and that is recorded, not assumed

## Metadata
- **Complexity**: Low
- **Labels**: Email, Postmark, Operations, Linux, Monitoring
- **Required Skills**: msmtp or Postfix, SMTP, cron, email authentication headers
