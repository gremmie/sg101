# Task: Repair the Old Host's Local Mail Plumbing

## Description
Fix three faults on the production box that cause **server mail to be silently
destroyed**, and one that makes the box send unsolicited mail to strangers. All
four were found on 2026-08-18 while investigating the first DMARC aggregate
reports. None involves the application: this is Postfix configuration and one
DNS record.

**Explicitly scoped to a machine with a short remaining life.** The host is
decommissioned in Step 21, and inbound mail moves to Cloudflare Email Routing in
task 06. Nothing here is architecture — each item is one or two lines, chosen so
that a person who does not want to become a mail administrator can apply it,
verify it, and stop thinking about it. Where a fix would require restructuring
local delivery, the recommendation is to leave it alone and let the migration
retire it.

## Background

### How these were found
The `_dmarc` record published in task 03 produced its first aggregate reports on
2026-08-18, showing 4 of 65 messages failing both SPF and DKIM. Chasing those 4
through `/var/log/mail.log` turned up more than the answer: three unrelated
reasons that mail leaving this box goes nowhere, one of which explains a symptom
Brian had been puzzled by for years.

**Every claim below is quoted from the mail log or from a live `postconf`
query.** The dates are real and the log is the evidence; nothing here is
inferred from documentation.

### Fault 1 — root's cron mail is destroyed on this machine

Twice daily, roughly 12 hours apart, ~2.4 KB each:

```
Aug 18 12:16:29 postfix/pickup[31679]: 2FCC158654D: uid=0 from=<root>
Aug 18 12:16:29 postfix/qmgr[1389]:    2FCC158654D: from=<root@surfguitar101.com>, size=2356
Aug 18 12:16:29 postfix/error[8392]:   2FCC158654D: to=<root@surfguitar101.com>, orig_to=<root>,
    relay=none, delay=0.05, dsn=5.1.1, status=bounced (User unknown in virtual alias table)
```

Postfix rewrites the bare `root` onto `surfguitar101.com`. That domain is a
**virtual alias domain**, and the table has no `root` entry, so delivery fails in
0.06 seconds without the message ever leaving the machine. The bounce generated
about it is itself undeliverable.

This has nothing to do with DNS, DKIM, SPF, or Gmail. Six occurrences in the
2026-08-16→18 window, every one bounced, zero delivered.

### Fault 2 — mail sent as `root@localhost` is refused as unauthenticated

Sent to `admin@surfguitar101.com`, forwarded by the alias to Brian's Gmail, and
refused with Google stating the reason:

```
550-5.7.26 Your email has been blocked because the sender is unauthenticated.
550-5.7.26 Gmail requires all senders to authenticate with either SPF or DKIM.
550-5.7.26  DKIM = did not pass
550-5.7.26  SPF [localhost] with ip: [173.255.245.115] = did not pass
```

`localhost` is on no OpenDKIM signing table and has no SPF record anywhere, so
this class cannot authenticate. Three occurrences on 2026-08-16 alone.

### Fault 3 — bounce notifications cannot authenticate either

A Postfix-generated DSN has an empty envelope sender, so SPF falls back to the
**HELO identity** — `mail.surfguitar101.com` since task 03, which publishes an A
record and no TXT. No record means SPF returns `none`, never `pass`. And Postfix
does not apply milters to internally generated bounces
(`internal_mail_filter_classes` is empty by default, confirmed with `postconf
-d`), so they are unsigned.

Neither mechanism can pass, which is **the best current explanation of the 4
DMARC failures**, and it is also why these were refused with `5.7.25` while the
PTR was broken.

**Note the trap:** repairing the PTR did not fix this class. It changes which
error it gets. Google requires SPF *or* DKIM to pass, so an unsigned null-sender
message now fails `5.7.26` where it used to fail `5.7.25`.

### Fault 4 — the box emits backscatter

53 delivery-status notifications to `member21@example.com` in three days. The box
accepts mail for an address it cannot deliver, then bounces it to the envelope
sender, which on spam is forged. **That makes this machine a sender of
unsolicited mail on a spammer's behalf, from the IP Postmark is currently
evaluating.** It is the reputation half of Step 16's problem, and no DNS record
touches it.

### What the survivor tells us
Brian's own crontab is delivered reliably: `uid=1000 from=<brian>`, rewritten to
`brian@surfguitar101.com`, signed by OpenDKIM, SPF passing on the record's
explicit `ip4:` term — **accepted by Gmail even while the PTR was broken**,
because authentication compensates for reverse DNS. That single working case is
the model the broken ones should be made to match.

### What is NOT known, and must not be assumed
**Brian reports receiving root cron mail occasionally — "months in between".**
The log window (2026-08-16→18) shows six root messages and six local bounces,
i.e. a 100% failure rate, which cannot produce an occasional success. So
**something in this picture is missing**: another sender, another recipient,
another path, or a job whose mail is addressed somewhere that does resolve.

Requirement 1 exists to find it. **Do not apply fixes to a model that has a
known contradiction in it** — the inventory comes first, because a fix that
makes the symptom disappear without explaining the rare success has only made
the evidence harder to read.

## Technical Requirements

1. **Inventory every source of local mail before changing anything.** Enumerate
   root's crontab and `/etc/cron.*`, user crontabs, systemd timers, and any
   `MAILTO=` settings; the `/etc/aliases` and virtual alias tables; and any
   scripts that call `mail`, `sendmail` or `mailx` directly. For each, record
   **sender address, recipient address, and frequency.** Cross-check against a
   full week of `/var/log/mail.log`, not against expectation.
   **Acceptance is explaining the rare success, not producing a list.**

2. **Add a `root` entry to the virtual alias table**, pointing at a destination
   that already works — `admin@surfguitar101.com` forwards to Brian's Gmail
   today. Rebuild with `postmap` and reload. This is the whole of fault 1.

3. **Give locally generated mail a sender that can be authenticated.** Rewrite
   `root@localhost` (and any other non-`surfguitar101.com` local sender found in
   requirement 1) onto an address on the signing domain, via
   `sender_canonical_maps`. The test is not that the rewrite happens; it is that
   the resulting message is **signed**, since OpenDKIM signs by domain.

4. **Publish SPF at the HELO name.** This is task 03's requirement 13, repeated
   here because it fixes fault 3 and is a prerequisite for verifying it:
   ```
   mail.surfguitar101.com.  TXT  "v=spf1 ip4:173.255.245.115 -all"
   ```
   One record, and it satisfies both Google's authentication requirement and
   DMARC's need for one aligned pass.

5. **Stop the backscatter by rejecting at SMTP time rather than accepting and
   bouncing.** Confirm `smtpd_reject_unlisted_recipient = yes` and that the
   virtual alias maps genuinely cover every address the MX accepts. A recipient
   the box will not deliver to must be refused during the SMTP conversation, so
   the *sending* server owns the failure and no message is created here.

6. **Change nothing structural.** `myhostname`, `mydestination` and the milter
   configuration stay as they are, per task 03's correction 3 and requirement
   12 — the box carries 20 live aliases and is being decommissioned. If a fix
   appears to require editing local delivery routing, stop and record it as
   something the migration retires instead.

7. **Verify from the receiving side, not from the log.** A `status=sent` line
   means the far end accepted the connection, not that the message authenticated
   or landed in an inbox. Each fix is confirmed by a real message's
   `Authentication-Results` header, in the same way the 2026-08-17 Outlook
   capture and the 2026-08-18 Gmail capture were read.

## Dependencies
- Root on the production host, and access to the Cloudflare zone for
  requirement 4.
- Independent of every code task in Step 16. Can be done at any time before the
  host is decommissioned.
- Requirement 4 overlaps task 03's requirement 13; do it once, in whichever task
  reaches it first, and mark the other done.

## Implementation Approach
1. Run the inventory (requirement 1) and reconcile it against a week of log.
   **Stop here if the rare-success contradiction is not explained.**
2. Apply requirement 2, then trigger or wait for one root cron run and confirm
   delivery end to end.
3. Apply requirement 3; send one message as the rewritten sender and read its
   headers for a valid signature.
4. Publish the SPF record from requirement 4; re-check a bounce's
   `Authentication-Results` afterwards.
5. Apply requirement 5; watch the log for a day and confirm no new DSNs to
   external strangers.
6. Re-read the DMARC aggregate reports after 48 hours: the residual failures
   should be gone, which is the independent confirmation that fault 3 was
   diagnosed correctly.

## Acceptance Criteria
- **Given** the inventory from requirement 1
  **When** compared against a week of `/var/log/mail.log`
  **Then** every recurring mail source is accounted for, **and the occasional
  successful root cron mail is explained** rather than left as an anomaly
- **Given** a root cron job that mails `root`
  **When** it runs after requirement 2
  **Then** the message reaches Brian's Gmail, and no `5.1.1 User unknown in
  virtual alias table` line appears for it
- **Given** a message generated locally by a system process
  **When** it is delivered after requirement 3
  **Then** its headers show `dkim=pass` with `d=surfguitar101.com`, and Gmail
  does not refuse it with `5.7.26`
- **Given** a Postfix-generated bounce after requirement 4
  **When** its headers are read at the receiver
  **Then** SPF passes on the HELO identity and DMARC reports an aligned pass
- **Given** a day of mail log after requirement 5
  **Then** no delivery-status notification was sent to an external address that
  did not originate mail here
- **Given** the DMARC aggregate reports 48 hours after requirements 3–5
  **Then** the residual both-mechanism failures are absent
- **Given** the whole task
  **Then** `myhostname`, `mydestination` and the milter configuration are
  unchanged, and the 20 existing aliases still deliver

## Metadata
- **Complexity**: Low per fix, Medium overall — the difficulty is diagnostic,
  not mechanical, and requirement 1 is the part that can fail
- **Labels**: Email, Postfix, DNS, Production Host, Deliverability, Step 16
- **Required Skills**: Postfix virtual aliases and canonical maps, SPF and DKIM
  well enough to read an `Authentication-Results` header, reading a mail log
