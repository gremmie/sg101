# Email header captures — before, interim, and (pending) after

Real delivered-message headers, kept because inference about mail configuration
has been wrong three times in this project and a header settles in seconds what
reasoning gets wrong for years. See `../STATUS.md` Step 16 and
`../../../tasks/2026-07-04-modernizing-sg101/step16/task-03-dns-email-authentication.code-task.md`.

Antispam blobs, base64 `X-Microsoft-Antispam-Message-Info` and routing hops
between Microsoft's own hosts are trimmed; everything diagnostic is kept verbatim.

---

## Capture 1 — 2026-08-12, Gmail, BEFORE any remediation

Sent from the Linode Postfix (`173.255.245.115`) as it had been configured for
years. Only the diagnostic fragments were preserved at the time.

```
Received: from jaguar.deathofagremmie.com ([173.255.245.115])
DKIM-Signature: v=1; a=rsa-sha256; c=simple/simple; d=surfguitar101.com; s=dkim;
Authentication-Results: mx.google.com;
    dkim=pass header.i=@surfguitar101.com header.s=dkim header.b=CnijwesJ;
    spf=pass (…designates 173.255.245.115 as permitted sender)
Message-ID: <…@jaguar.deathofagremmie.com>
```

**What it established:**
- **DKIM was signing and passing**, disproving a written finding that the
  out-of-range milter port meant mail went out unsigned.
- **Reverse DNS did not forward-confirm.** Gmail renders
  `from HELO (ptr-name [ip])` when it can confirm reverse DNS. The parenthetical
  where the PTR name belongs is **empty** — FCrDNS failure, observed from the
  receiving side.
- **No `dmarc=` clause at all**, because no policy was published.
- HELO was the dead `deathofagremmie.com` domain, as was the `Message-ID`.

---

## Capture 2 — 2026-08-17, Outlook.com, AFTER the interim fix, BEFORE Postmark

Same sending path — Linode Postfix, `173.255.245.115` — after the same day's
remediation: `mail.surfguitar101.com` unproxied and pointed at the Linode IP, the
Linode PTR set to match, `smtp_helo_name` aligned, and DMARC published at
`p=none`. **Postmark is not in this path**; `EMAIL_HOST` is still `localhost`.

Message was a "send a news story to a friend" (`news.views.email_story`, which
task 04 deletes) to a mailbox created minutes earlier.

```
Authentication-Results: spf=pass (sender IP is 173.255.245.115)
 smtp.mailfrom=surfguitar101.com; dkim=pass (signature was verified)
 header.d=surfguitar101.com;dmarc=pass action=none
 header.from=surfguitar101.com;compauth=pass reason=100
Received-SPF: Pass (protection.outlook.com: domain of surfguitar101.com
 designates 173.255.245.115 as permitted sender)
 receiver=protection.outlook.com; client-ip=173.255.245.115;
 helo=mail.surfguitar101.com; pr=C
Received: from mail.surfguitar101.com (173.255.245.115) by
 DB1PEPF000509E2.mail.protection.outlook.com (10.167.242.52) with Microsoft
 SMTP Server id 15.21.315.6 via Frontend Transport; Mon, 17 Aug 2026 23:53:21 +0000
Received: from jaguar.deathofagremmie.com (localhost.localdomain [127.0.0.1])
    by jaguar.deathofagremmie.com (Postfix) with ESMTP id 0F0BD586565
    for <bgneal43@outlook.com>; Mon, 17 Aug 2026 18:53:21 -0500 (CDT)
DKIM-Signature: v=1; a=rsa-sha256; c=simple/simple; d=surfguitar101.com;
    s=dkim; t=1787010801;
    h=Subject:From:To:Date:Reply-To:From;
From: no_reply@surfguitar101.com
Date: Mon, 17 Aug 2026 23:53:21 -0000
Message-ID: <20260817235321.1920.52741@jaguar.deathofagremmie.com>
Reply-To: bgneal@gmail.com
Return-Path: no_reply@surfguitar101.com
X-SID-PRA: NO_REPLY@SURFGUITAR101.COM
X-SID-Result: PASS
X-MS-Exchange-Organization-SCL: 1
X-Microsoft-Antispam: BCL:0;ARA:…
X-Message-Delivery: Vj0xLjE7dXM9MDtsPTA7YT0wO0Q9MTtHRD0xO1NDTD0z
X-Microsoft-Antispam-Mailbox-Delivery:
    ucf:0;jmr:0;ex:0;auth:1;dest:I;ENG:(…)
```

### What it establishes

**`dmarc=pass action=none` — the first DMARC evaluation this domain has ever
produced.** Capture 1 had no `dmarc=` clause at all. The record published hours
earlier is being read and evaluated. `compauth=pass reason=100` is Microsoft's
composite-authentication verdict; 100 means it passed explicit DMARC
authentication, the strongest available.

**The HELO change is confirmed in flight** — `helo=mail.surfguitar101.com` in
`Received-SPF`, where it was `jaguar.deathofagremmie.com` the same morning.

**It reached the Inbox, confirmed in the headers rather than visually** —
`dest:I` in `X-Microsoft-Antispam-Mailbox-Delivery`, with `jmr:0` (no junk-mail
rule fired) and `BCL:0` (not treated as bulk).

**But the spam score is not pristine, and this is the part worth keeping.**
`X-MS-Exchange-Organization-SCL: 1` looks clean, but `X-Message-Delivery`
decodes to `V=1.1;us=0;l=0;a=0;D=1;GD=1;SCL=3`. Comfortably below the junk
threshold, but not the 0–1 of a well-trusted sender. **Authentication is now
perfect; reputation is still neutral** — exactly the predicted split, and exactly
the argument for moving to a provider whose IP reputation is actively
maintained. Fixing DNS does not retroactively build sending history.

**`Message-ID` — hypothesis confirmed, by format rather than by value.** It was
recorded as *probably* Django rather than Postfix. The value alone proves
nothing, because `myhostname` was deliberately left as
`jaguar.deathofagremmie.com`, so **both** hypotheses predicted that domain would
still appear. The **format** discriminates:

- `20260817235321.1920.52741` is `YYYYMMDDHHMMSS.pid.randrange(100000)` — the
  signature of Python 2.7's `email.utils.make_msgid()`, which is what production
  runs.
- **Postfix's Message-ID would embed its queue ID**, and that queue ID is visible
  in the very same message: `with ESMTP id 0F0BD586565`. It does not appear in
  the Message-ID.

So the header comes from Django via `socket.getfqdn()` on the application host.
**Neither the HELO change nor the move to Postmark will fix it**; it needs the
app host's FQDN changed or a Django-side override. Cosmetic — a plausibility
signal, not an authentication check — but now established rather than suspected.

*Method note worth keeping: a probe that both hypotheses predict is not a probe.
The value was uninformative; only the format separated the two.*

### What it does not establish

**One message, to a mailbox created minutes earlier.** A fresh Outlook account
has no history, no contact graph and no user signal, and is not equivalent to the
established accounts whose owners reported the original problem. Strong evidence
about **authentication**, weak evidence about **reputation** — which is the part
still outstanding.

**It does not independently confirm FCrDNS.** Microsoft renders `Received` as
`from <helo> (<ip>)` and does not display the reverse-DNS name separately, unlike
Gmail's `from HELO (ptr [ip])`. FCrDNS rests on the `dig` verification against
`*.akam.net`. Nothing here contradicts it.

**Two vintage defects are unchanged and expected**: `c=simple/simple`
canonicalization, and `Date: … -0000`. Both are moot after the provider move.

---

## Capture 3 — AFTER Postmark cutover — NOT YET TAKEN

Owned by task 07. Predictions to test, written down in advance so the result
cannot be read to fit:

- `d=surfguitar101.com` DKIM signed with **Postmark's 1024-bit key** — not
  2048-bit, per task 03 Finding 2.
- Postmark's own sending IP and PTR in place of `173.255.245.115`.
- `spf=pass` evaluated against the `pm-bounces` Return-Path; `dmarc=pass`.
- **`Message-ID` still carrying `jaguar.deathofagremmie.com`** on current
  production, or whatever `socket.getfqdn()` returns on the Step 21 VM. A *pass*
  here needs explaining — most likely Postmark rewriting the header — rather than
  being taken as the fix.
- **`SCL` better than capture 2's 3.** This is the one that measures whether the
  provider move bought what it was meant to buy. Capture 2 already reaches the
  Inbox with perfect authentication, so inbox placement alone cannot distinguish
  success from the status quo — the same trap as verifying against Gmail.
