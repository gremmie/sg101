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

### Fault 4 — the box emits backscatter. **Traced 2026-08-18; smaller and
### differently caused than first written**

First recorded as "53 delivery-status notifications to `member21@example.com` in
three days", from a box accepting mail for an undeliverable address and bouncing
it to a forged sender. The trace corrected all of that:

- **One message, not 53.** All those lines share queue ID `4F3A25869C1`, retried
  hourly because `uplus.co.kr` refuses connections. Log lines were counted as
  messages.
- **Forwarding, not unknown recipients.** A forged-sender spam arrived for
  `themadeira@themadeira.net` — a *valid* alias — was forwarded to a Gmail
  address, and **Gmail refused it for the missing PTR**, so Postfix bounced to
  the forged sender.
- **`smtpd_reject_unlisted_recipient` is already `yes`**, so the accept-then-
  bounce mechanism this fault was written around does not exist here.
- **The trigger is fixed.** The PTR was repaired 2026-08-17, so that forward now
  succeeds and generates no DSN.

### What the survivor tells us
Brian's own crontab is delivered reliably: `uid=1000 from=<brian>`, rewritten to
`brian@surfguitar101.com`, signed by OpenDKIM, SPF passing on the record's
explicit `ip4:` term — **accepted by Gmail even while the PTR was broken**,
because authentication compensates for reverse DNS. That single working case is
the model the broken ones should be made to match.

### The inventory — RUN 2026-08-18, and it found no contradiction after all

This section originally recorded an apparent contradiction: Brian receives root
cron mail every few months, while the log showed a 100% failure rate that cannot
produce an occasional success. **The inventory dissolved it — the mail he
receives comes from a different machine.**

`bobcat.gremmielabs.dev` (198.58.104.73) is a second Linode that rsyncs this box
nightly at 03:15. Its cron mail authenticates on SPF and is delivered normally.
**Nothing about jaguar's root mail is intermittent: it fails every time.** The
contradiction was two servers being read as one.

What generates mail on this box, measured rather than assumed:

| Source | Sender | Fate |
|---|---|---|
| Brian's crontab (uid 1000) | `brian@surfguitar101.com` | **delivered**, daily 02:01 |
| site mail to `admin@` | `no_reply@surfguitar101.com` | **delivered**, 23 in the window |
| certbot (`/etc/cron.d/certbot`, twice daily) | `root` → `root@surfguitar101.com` | **`5.1.1`, dies here** |
| `cron.daily` / `cron.weekly` via `run-parts` | same | **`5.1.1`, dies here** |
| munin, munin-node (`MAILTO=root`), sysstat | same | silent — no output observed |
| locally generated notices | `root@localhost` | **`5.7.26`, refused by Gmail** |

There is **no root crontab and no systemd timer** on this box; `/etc/crontab`
sets no `MAILTO`, so every `run-parts` job defaults to `root`. **Not one
root-originated message was delivered anywhere in four weeks of retained logs.**

### The certbot job is a broken alarm, and that is worse than it sounds

The twice-daily ~2.4 KB is `certbot -q renew`. `-q` means it should print nothing
on success, and it prints every time, because **two retired domains have
long-expired certificates it keeps trying to renew** — `briananddebra.com`
(expired 2023-07-07) and `deathofagremmie.com` (expired 2023-12-26) — alongside
OCSP warnings from a certbot too old for Let's Encrypt having retired OCSP.

The live certificates are healthy: `surfguitar101.com` valid 89 days,
`wiki.surfguitar101.com` 40, `themadeira.net` 30, and two others.

**So there is no cert emergency — there is a dead alarm.** The job's output is
permanently non-empty, so "certbot sent mail" means nothing, and the mail is
discarded before anyone could read it regardless. Fixing the delivery without
silencing the noise would just deliver 2.4 KB of meaningless output twice a day,
which is the same failure wearing a different hat.

## Technical Requirements

1. **~~Inventory every source of local mail before changing anything.~~ DONE
   2026-08-18** — results in the Background section above. Every recurring mail
   source on this box is accounted for, and the months-apart mail was traced to
   `bobcat.gremmielabs.dev`, a different machine. The remaining requirements may
   proceed.

2. **~~Add a `root` entry to the virtual alias table.~~ DONE 2026-08-18** —
   `root@surfguitar101.com  bgneal@gmail.com` in
   `/etc/postfix/virtual_alias_maps`, `postmap`ed and reloaded, with the file
   backed up first. Verified by `postmap -q`, by a test message reaching
   `status=sent`, and **by Brian confirming it in his Gmail inbox**. Note for
   the record: `/etc/aliases` already held `root: bgneal@gmail.com` and had been
   unreachable since `surfguitar101.com` became a virtual alias domain — the
   intent was configured, just never consulted.

3. **~~Give locally generated mail a sender that can be authenticated.~~ DONE
   2026-08-18.** `sender_canonical_maps` mapping `root@localhost` to
   `root@surfguitar101.com`, one entry, `main.cf` backed up first.
   `sender_canonical_classes` was already at its default of `envelope_sender,
   header_sender` — **rewriting the header is the load-bearing half**, since
   OpenDKIM signs by From domain, and envelope-only would have fixed SPF while
   leaving DKIM failing.

   **What this class of mail turned out to be: Django's error reports.** The
   Message-ID format (`YYYYMMDDHHMMSS.pid.randrange`), the
   `client=localhost.localdomain[127.0.0.1]` submission and the 5–10 KB sizes
   identify it as `mail_admins()` through `AdminEmailHandler`, sent from
   `root@localhost` because **`SERVER_EMAIL` is unset** — exactly the defect
   Step 16 task 01 found in the settings and fixed in code. Eighteen of them
   between 2026-07-20 and 2026-08-18, every one refused, with the bounce about
   each also failing. **Nobody has seen an exception report from the live site
   in years.**

   Verified at the receiver: `dkim=pass header.i=@surfguitar101.com`,
   `spf=pass smtp.mailfrom=root@surfguitar101.com`, `dmarc=pass
   header.from=surfguitar101.com`. *OpenDKIM logged nothing for the message, so
   the mail log alone could not have answered this — the header could.*

   **Interim by construction.** Task 01's `SERVER_EMAIL` fix does the same job
   properly, but production runs the old code and will for several more steps.
   The rewrite becomes redundant, and harmless, once that deploys.

   Original text follows.

   ~~Give locally generated mail a sender that can be authenticated.~~ Rewrite
   `root@localhost` (and any other non-`surfguitar101.com` local sender found in
   requirement 1) onto an address on the signing domain, via
   `sender_canonical_maps`. The test is not that the rewrite happens; it is that
   the resulting message is **signed**, since OpenDKIM signs by domain.

4. **~~Publish SPF at the HELO name.~~ DONE 2026-08-20** — published by hand in
   Cloudflare and verified at both authoritative nameservers, exactly one SPF
   record at the name. Task 03's requirement 13 is the same record and closes
   with it. Delivery-side proof is still outstanding: the clean test is the DMARC
   report covering 08-21, read on 08-22, and the confirming observation is a
   *pass* row for the bounce class rather than an absence of failures. Original
   text follows. This is task 03's requirement 13, repeated
   here because it fixes fault 3 and is a prerequisite for verifying it:
   ```
   mail.surfguitar101.com.  TXT  "v=spf1 ip4:173.255.245.115 -all"
   ```
   One record, and it satisfies both Google's authentication requirement and
   DMARC's need for one aligned pass.

5. **Verify the backscatter stopped — do not "fix" it.** Rewritten 2026-08-18
   after tracing it (see fault 4 above). The original text prescribed rejecting
   unknown recipients at SMTP time; that mechanism is not what produced the
   bounces, and it is already enabled by default.

   The check is DSN generation per day across the retained logs:
   ```
   zgrep -h 'sender non-delivery notification' /var/log/mail.log* \
     | awk '{print $1, $2}' | sort -k1,1M -k2,2n | uniq -c
   ```
   **Expected: counts fall to zero after 2026-08-17**, when the PTR was repaired
   and forwarded mail stopped being refused. If they do not, the diagnosis is
   incomplete and the remaining DSNs must be traced the same way — parent queue
   ID via `postfix/bounce: <parent>: sender non-delivery notification: <child>`.

   **Change nothing on the strength of this requirement alone.** What remains
   after the PTR fix is inherent to forwarding third-party mail: any destination
   refusing a forwarded message for any reason produces a bounce to whatever
   sender the message claimed. `themadeira.net` forwards to four external
   addresses, so the exposure is real but small, and **task 06's move to
   Cloudflare Email Routing retires it structurally** — which is the correct fix
   on a box scheduled for decommissioning.

6. **~~Retire the two dead certificates.~~ DONE 2026-08-18.** The trap was
   real: `deathofagremmie.com` was an *enabled* vhost naming its expired cert,
   so deletion without `a2dissite` first would have stopped Apache and taken
   `surfguitar101.com` with it. Order run: disable, `configtest`, reload, verify
   both live sites answer 200, then `certbot delete` on both. `certbot -q renew`
   now prints nothing and exits 0. **Brian no longer owns
   `deathofagremmie.com`** — the renewal had been failing against the current
   owner's Cloudflare, which is why it could never have been fixed, only
   deleted. Original wording follows.

   ~~Retire the two dead certificates, and only then trust certbot's silence.~~
   Measure first: run `certbot -q renew` by hand and read what it actually
   prints, since the OCSP warnings may survive deleting the expired pair. Then
   check whether any Apache vhost still references
   `/etc/letsencrypt/live/briananddebra.com/` or `.../deathofagremmie.com/` —
   **deleting a certificate that a vhost still names will stop Apache from
   starting**, which turns a tidy-up into an outage for the sites that do
   matter. Remove or disable those vhosts first, then `certbot delete
   --cert-name` each. The goal is a job whose output is empty on success, so
   that a future message from it means something.

7. **Change nothing structural.** `myhostname`, `mydestination` and the milter
   configuration stay as they are, per task 03's correction 3 and requirement
   12 — the box carries 20 live aliases and is being decommissioned. If a fix
   appears to require editing local delivery routing, stop and record it as
   something the migration retires instead.

8. **~~Request delisting from Comcast.~~ CLEARED 2026-08-19** — both MX hosts
   now answer `220 … ESMTP server ready` where they answered `554 … #BL000100`
   the day before, same box, same command, same two targets. Delivery itself is
   still unconfirmed: a `220` is the connection being accepted, not a message
   reaching an inbox. History below.

   **~~Request delisting from Comcast.~~ CHASED TO ITS SOURCE 2026-08-18.**
   The Blocked Provider form covers `BL000000`; our error is `BL000100`, and
   their reply ("not on our blocklist") answered the wrong question. The block
   was still live afterwards — `554 … #BL000100` at both `mx1.mxge.comcast.net`
   and `mx1a1.comcast.net`, from a bare SMTP greeting with no mail sent. The
   error's own link leads to **Validity's Return Path Blocklist**
   (`senderscore.org`), a commercial feed no public DNSBL query can see, which
   is why the IP reads clean on Spamhaus, SpamCop, Barracuda, CBL, SpamRats,
   UCEPROTECT, PSBL and GBUdb (all control-verified from the sending host).
   **Removal requested there 2026-08-18**; the form did not disclose listing
   status. Re-check the greeting in a day or two — it is the only ground truth.
   Original text follows.

   ~~Request delisting from Comcast.~~ SUBMITTED 2026-08-18, via their
   Blocked Provider Request Form, citing the measured remediation with dates:
   PTR forward-confirming since 2026-08-17, HELO aligned, DMARC published,
   outbound TLS enabled 2026-08-18, local senders rewritten, and recipient-side
   headers showing `spf=pass` / `dkim=pass` / `dmarc=pass`. Acknowledgement says
   up to three business days; their FAQ says as little as thirty minutes.

   **Verify without sending mail.** Comcast refuses at the SMTP greeting, not at
   `DATA`, so a bare connection from the box answers it — `220` means delisted,
   `554` means still blocked, and no message, queue entry or member recipient is
   involved:
   ```
   python -c "
   import socket
   for h in ('mx1.mxge.comcast.net', 'mx1a1.comcast.net'):
       try:
           s = socket.create_connection((h, 25), 10)
           print('%-24s %s' % (h, s.recv(1024).decode('utf-8', 'replace').strip()))
           s.close()
       except Exception as e:
           print('%-24s ERROR %s' % (h, e))"
   ```
   Must be run on the production host: the answer depends on the connecting IP.
   The MX lookup does not — `dig +short mx comcast.net` answers the same
   anywhere, so the hostnames can be refreshed from a laptop.

   **Corrected 2026-08-19: this block previously named `mx1.comcast.net`, which
   does not exist.** It is not in Comcast's MX set and has no A record, so the
   command as written could only ever produce
   `socket.gaierror: [Errno -2] Name or service not known` — a failure that
   looks like a connection problem rather than a typo. The two hostnames above
   are the ones actually run on 2026-08-18, recovered from the host's shell
   history rather than reconstructed. Comcast publishes eight MX hosts
   (`mx1`/`mx2.mxge` at priority 5, six more at 50); **only these two were ever
   checked**, so a `554` from both is evidence about the IP, not proof that all
   eight agree.

   Original text follows.

   ~~Request delisting from Comcast — after requirement 5, not before.~~
   Added 2026-08-18. Comcast refuses all mail from `173.255.245.115` with
   `554 … found on one or more DNSBLs` (their code `BL000100`). The IP is on
   **none** of six public blocklists checked, so this is Comcast's own internal
   list, and the remedy is their block-removal request at
   `postmaster.comcast.net`.

   **Sequencing, and the reason it is not urgent.** 23 site notifications to one
   member were queued behind the block, and this requirement originally called
   saving them time-sensitive. **Brian's call, 2026-08-18: let them expire** —
   Comcast has been blocking for a long time, the messages are stale, and a
   removal request would not have completed inside the remaining hours of the
   5-day queue lifetime anyway. On expiry each returns to
   `no_reply@surfguitar101.com`, which is not in the virtual alias map, so the
   bounces die locally and nothing reaches a third party.

   **With no deadline, submit the request only once the backscatter is fixed.**
   Asking for removal while the box still bounces to forged senders invites a
   second listing, and the submission is far stronger when it can state that
   reverse DNS was repaired 2026-08-17, that SPF, DKIM and DMARC all pass, and
   that the bounce behaviour has been corrected.

9. **~~Enable opportunistic outbound TLS.~~ DONE 2026-08-18.** Applied
   (`smtp_tls_security_level = may`, `smtp_tls_loglevel = 1`, `main.cf` backed
   up) and verified from both ends: the log shows `Untrusted TLS connection
   established to gmail-smtp-in.l.google.com: TLSv1.2 with cipher
   ECDHE-ECDSA-AES128-GCM-SHA256`, the message was delivered, and **Gmail now
   reports it as encrypted where it previously reported it was not** — a
   before/after contrast at the receiver, not an inference. Original text
   follows.

   Added 2026-08-18, and unlike the rest
   of this task it affects **every message the box sends**, not only bounces and
   system mail. `smtp_tls_security_level` is unset, which on this Postfix
   vintage means outbound TLS is off: mail leaves in plaintext to every
   destination. Inbound has TLS (`smtpd_use_tls = yes`) with the snakeoil
   self-signed certificate, which is why the omission is easy to miss — the
   config *looks* TLS-aware.

   Found by accident, in a bounce nobody was reading: a DSN to a Mailchimp
   address was refused with `530 Must issue a STARTTLS command first`. **A
   receiver that requires STARTTLS refuses this box outright, and no DMARC
   report will ever say so, because it is not an authentication failure.**
   Google's bulk-sender guidelines also list TLS as a requirement, so this has
   been working against the very receiver whose acceptance this step keeps
   measuring.

   ```
   postconf -e 'smtp_tls_security_level = may'
   postconf -e 'smtp_tls_loglevel = 1'
   postfix reload
   ```
   `may` is opportunistic: a peer that offers no TLS still receives plaintext,
   exactly as today, so nothing that currently works can stop working. The
   loglevel makes verification direct — a delivered message's headers should
   show `version=TLS1_2` where they currently show nothing. Back up `main.cf`
   first. **Caveat:** this box's OpenSSL is 14.04-era; if a handshake ever
   fails, opportunistic mode retries in the clear, so the failure mode is delay
   rather than loss.

10. **Verify from the receiving side, not from the log.** A `status=sent` line
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
- ~~**Given** the inventory from requirement 1…~~ **met 2026-08-18**: every
  recurring mail source is accounted for, and the months-apart mail was traced
  off this machine entirely
- **Given** `certbot -q renew` after requirement 6
  **Then** it prints nothing, so that any future mail from that job is a real
  signal — and Apache still starts, with every live site serving its own cert
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
- **Given** a message delivered to Gmail after requirement 9
  **Then** its `Received` header records a TLS version and cipher, where today
  it records none
- **Given** the DSN-per-day counts across the retained logs
  **Then** they are zero after 2026-08-17, or every survivor has been traced to
  its parent message and explained
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
