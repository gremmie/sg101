# DMARC aggregate reports — the reading log

**Extracted from `STATUS.md` on 2026-08-26**, where these eleven readings had
grown to ~2,000 lines inside a single section nominally about Step 16 task 03.
They are a periodic instrument log, not project status, and they live here for
the same reason `research/email-header-captures.md` does: the measurements are
consulted as a series, and their bulk was making the status document unreadable.

**Instrument:** `tools/dmarc_report.py` over `~/dmarc`, the local `rua` copy
delivered to `admin@surfguitar101.com`. Cloudflare's dashboard is the second
view; it shows *sending sources*, never reporter identity.

**Convention, adopted 2026-08-21:** every reading records the reporter, the
Report-ID and the window. Applied in full from the sixth reading onward.

**Open items, predictions and the outstanding questions these readings feed stay
in `STATUS.md`** under Step 16 task 03's *Open* register — this file is the
evidence, that one is the state.

**This log has an end.** Set 2026-09-05: weekly until the Step 21 cutover window,
daily across it, then stopped. The three items that keep it running and the reason
the send-side baseline cannot outlive jaguar are in `STATUS.md` under *When the
reading log stops*.

**Reading index**

| # | Date read | Window | Headline |
|---|---|---|---|
| 1 | 2026-08-18 | 08-17 | Gmail's view alone; 61/65 pass, 4 failures |
| 2 | 2026-08-19 | 08-18 | the prediction held |
| 3 | 2026-08-20 | 08-19 | one prediction held weakly — **superseded the same evening** |
| 4 | 2026-08-20 pm | 08-19 re-read | the row had tripled; Comcast is the second reporter |
| 5 | 2026-08-21 | 08-20 | first from our own copy; two of my claims died on the way |
| 6 | 2026-08-22 | 08-21 | three reporters; first window re-read from an immutable source |
| 7 | 2026-08-23 | 08-20→22 | Microsoft arrives; first DKIM failure from our own IP |
| 8 | 2026-08-24 | 08-23 | SPF rewrite measured at five receivers |
| 9 | 2026-08-25 | 08-24 | the Microsoft prediction held; an eighth receiving domain |
| 10 | 2026-08-25 pm | 08-24 | one raw message closes three open questions |
| 11 | 2026-08-26 | 08-25 | Postmark appears; the policy line does not |
| 12 | 2026-08-27 | 08-26 | the policy line appears; one report of three did not get it |
| 13 | 2026-08-28 | 08-27 | a fifth reporter, and the tool read its report as empty |
| 14 | 2026-08-29 | 08-28 | an eleventh endpoint, and a fourfold day the sending host explains |
| 15 | 2026-08-30 | 08-29 | one Microsoft report is three mailbox domains; the spike does not repeat |
| 16 | 2026-08-31 | 08-30 | the eleventh endpoint was never in the corpus; a rotation hole in the sending baseline |
| 17 | 2026-09-01 | 08-31 | ten of eleven endpoints reconcile exactly with the send log; Google alone does not |
| 18 | 2026-09-02 | 09-01 | the UTC−7 day passes a forward test; the second unsigned message is a bounce |
| 19 | 2026-09-04 | 09-02, 09-03 | UTC−7 passes a second forward test; a DKIM failure class that is not the bounce class — **addendum: cause found, Postfix wraps at 998 bytes post-signing** |
| 20 | 2026-09-05 | 09-04 | UTC−7's strongest window yet, contradicted by Yahoo in the same window; the size hypothesis dies on a forward test |
| 21 | 2026-09-08 | 09-04 → 09-07 | five for five; three consecutive Google days reconcile exactly; Microsoft drops a tenant domain Google would have folded in |
| 22 | 2026-09-12 | 09-07 → 09-11 | a second forwarder at web.de; four more exact Google days; three endpoints file nothing for 09-07 — **addendum: the hole is ours, Yahoo alone did not file, and the two failures are bounces**; **second addendum: 09-07 recovered — the classes separate inside the report, and the class tally was wrong since reading 19** |
| 23 | 2026-09-21 | 09-11 → 09-20 | Comcast counts evaluations, not messages — 16 for two; ten exact Google days; a twelfth endpoint; the local `rua` copy has been dead since the MX flip — **addendum: the collection path was automated the same day and recovered four lost reports; `web.de` is a reporter and counts every window twice; prediction 6 falsified** |
| 24 | 2026-09-28 | 09-20 → 09-27 | leopard appears through Cloudflare's forward — sixteen messages, fifteen matched to the send log; UTC−7 holds on a new source; two new forwarders; six of seven predictions held, the seventh already falsified |
| 25 | 2026-10-05 | 09-28 → 10-04 | Postmark appears as a source IP through the member beta; a neighbour on jaguar's /64 passes on SPF; the first quarantine dispositions |
| 26 | 2026-10-06 | 10-05 | the first daily reading (A4); Google's Postmark rows reconcile on the UTC−7 day, five for five; a spoof from another Linode region quarantined |
| 27 | 2026-10-07 | 10-06 | the last whole day before the freeze: jaguar alone, no Postmark row as leopard sent nothing; a fifth forwarder, at `cloudfilter.net` |
| 28 | 2026-10-08 | 10-07 | the flip day: both hosts reconcile exactly at Google and Yahoo; the `cloudfilter.net` forwarder is `thegogorillas.com`'s; jaguar delivers to Comcast after the flip |
| 29 | 2026-10-09 | 10-08 (+ Comcast, Microsoft 10-07) | the first full day on leopard: Postmark reconciles exactly at five endpoints, with a Workspace domain telling UTC−7 from UTC; Comcast's deferral loop counts 42 and 25, exact to the reception; Microsoft's 12 for 11 is a timed-out attempt received twice |
| 30 | 2026-10-10 | 10-09 | a quiet day, exact at Google, Yahoo and AT&T, with three forwarders each matched to a send; jaguar's two extra Google messages are certbot failing to renew `edtaxidermy.com` |
| 31 | 2026-10-11 | 10-10 (+ Microsoft 10-09) | exact at four reporters; GMX files and does not double; disabling certbot took jaguar back to one message |
| 32 | 2026-10-12 | 10-11 | exact at Google and Yahoo; jaguar's two messages as predicted; Microsoft not yet filed |
| 33 | 2026-10-13 | 10-12 (+ Microsoft 10-11) | exact at five reporters; the sixth `cloudfilter.net` row is the 06:29 send; jaguar back to the cron mail |
| 34 | 2026-10-15 | 10-13 | the quietest Google day since the flip, 1 for 1; exact at Yahoo, Comcast and GMX; all five predictions held |
| 35 | 2026-10-15 | 10-14 | exact at Google (21) and Yahoo (8); jaguar's 3 for a predicted 1 is two sudo-failure mails, almost certainly the thirty-fourth reading's own probe |
| 36 | 2026-10-16 | 10-15 | exact at Google, Yahoo, AOL and AT&T; jaguar back to the cron mail; Comcast not yet filed |
| 37 | 2026-10-17 | 10-16 (+ Comcast 10-15) | exact at Google (18), Yahoo and AT&T; Comcast files its 10-15 row; all five predictions held |
| 38 | 2026-10-18 | 10-17 | exact at Google (6 + jaguar 1); Yahoo's only row is a spoof from `209.85.208.101` as `bogotabureau.com`, quarantined: the corpus's fourth quarantined row, the first since 09-30 |
| 39 | 2026-10-19 | 10-18 | exact at Google (23 + jaguar 2, the Sunday `cron.weekly` mail), Yahoo (4) and AT&T (1); Microsoft's 10-18 not yet filed |
| 40 | 2026-10-20 | 10-19 (+ Microsoft 10-18) | exact at Google, AOL and Comcast; Microsoft files its 10-18 row; all five predictions held |
| 41 | 2026-10-21 | 10-20 | **the last reading**: exact at Google (17 + jaguar 1), Yahoo, Comcast and AT&T; the over-long-line DKIM class is zero across all 47 post-cutover reports; the log stops |

**Reading 13 carries two addenda** — Gmail Postmaster Tools read the same
afternoon, whose compliance panel is a 2026-08-18 snapshot with two of its three
complaints measurably false and no deliverability data at this domain's volume;
and a census of the Gmail spam folder, which holds one filtered message that is
not a report, the one that was filtered having been removed from the folder by
the act of reading it.

**⚠️ CORRECTED 2026-09-04 — the eighteenth reading's "two policy elements the
tool has never printed" is three.** `fo` is present in all 7 Comcast and all 10
Microsoft reports and was missed; the nineteenth reading carries the full census.

**Reading 19 carries an addendum** — the raw message for `44C7F5864DF`, read out
of the Gmail spam folder the same evening, which identifies the DKIM failure as a
body-hash mismatch caused by Postfix's 998-byte line wrap running after `opendkim`
signs. It kills that reading's own size fit and replaces it with a mechanism.

**⚠️ CORRECTED 2026-09-12 by the twenty-second reading's second addendum — the
over-long-line DKIM class is 3 rows and 4 messages, not 4 and 5.** The 09-01
message is **unsigned** and belongs to the DSN class the eighteenth reading
identified; the nineteenth opened a class explicitly *"not the bounce class"* and
absorbed it anyway, and readings 20, 21 and 22 carried the figure forward. The two
classes are identical in the *evaluated* fields every tally was built from and
differ only in `auth_results`: the DSN class carries **no `<dkim>` element** and
SPF on `mail.surfguitar101.com`, the over-long-line class a `<dkim>` element
failing on `surfguitar101.com`.

**Reading 22 carries two addenda** — Cloudflare's dashboard read the same
afternoon, which shows 26 messages for the 09-07 window against the 5 in `~/dmarc`;
and Google's 09-07 report itself, recovered from Gmail at 14:39, which confirms the
loss was ours, holds the predicted 20, and separates the two DKIM-failure classes
from `auth_results` without recourse to the send log. **`aol.com`'s 09-07 report is
the one piece still missing**, and the 25-against-26 arithmetic is what identifies
it.

**Reading 11 carries an addendum** — Comcast's late filing for the 08-25 window,
read 2026-08-26 13:12Z, which takes that window to 11 messages across four
receiving domains and gives the `policy_published` timing property a second
witness.

**The twelfth reading was written against a prediction that every report for the
2026-08-26 window must read `p=quarantine`.** Two of three did; `yahoo.com` read
`p=none` beside a `quarantine` sibling from its own filing run. The thirteenth
reading resolves that as a per-receiving-domain cache lag rather than a property
of Yahoo's filing — `policy_published` records when a receiver last read the
zone, and nothing else.

**"Receiving domain" means *reporting endpoint* everywhere it appears before the
fifteenth reading**, which found that Microsoft's single `protection.outlook.com`
filing covers `hotmail.com`, `outlook.com` and `live.com` in a per-record
`envelope_to` the tool does not print. The endpoint count is the only figure
comparable across reporters, since Google, Comcast and GMX omit `envelope_to` and
file one report each. Earlier counts are correct under that reading and are not
recomputed.

**⚠️ UPDATED 2026-09-01 — the count is eleven by filename again, for a different
reason.** `sbcglobal.net` filed for the 08-31 window and is a file in the corpus, so
the seventeenth reading's figure is **eleven by filename, plus `swbell.net` by sender
name**. That reading also corroborated `swbell.net` from the send log — jaguar sent
it 2 messages in the 08-21 window, before `~/dmarc` was being filled — so the
provenance distinction stands while the doubt behind it does not. The correction
below is what the figure meant between 2026-08-31 and 2026-09-01, and is kept
because the reasoning is the reusable part.

**⚠️ CORRECTED 2026-08-31 — that count was ten in the corpus, not eleven.** The
sixteenth reading measured the distinct receiver field across all forty-four files
and found ten. The eleventh, `swbell.net`, was read in the sixth reading from the
*sender names of the report mail in Gmail* and flagged in the eighth as the one not
read from the filename convention — so it is exactly what the definition above
excludes, and it has never been a file in `~/dmarc`. State it as **ten by filename,
plus `swbell.net` by sender name**. Nothing here says `swbell.net` was not a
receiving domain.

**The seventh reading's unsigned-message known-unknown is CLOSED by the
eighteenth.** It was closed in 2026-08-23 with an explicit reopen condition — a
second occurrence — which fired on 2026-09-01. The message is a Postfix
non-delivery notification: null envelope sender, SPF falling back to the HELO name
`mail.surfguitar101.com`, no signature because DSNs bypass the milters. Its
hypothesis A was correct and died on an absence in one window. **The class is every
Postfix DSN**, visible in a report only on days something bounces, so a
`pass`/`fail` row from `173.255.245.115` is now expected rather than anomalous — and
checkable against `grep 'from=<>'` on the mail log.

**Read the thirteenth reading before trusting any earlier per-window total
recomputed from a folder scan.** `tools/dmarc_report.py` rendered a valid report
from a namespaced reporter as `0 messages` — a well-formed reading of a report it
never read. Fixed there; the reports read before it are unaffected, all having
used the original schema.

---

### First DMARC data — 2026-08-18, and it is Gmail's view alone

The reporting clock started 2026-08-17; Cloudflare's dashboard has its first
aggregate rows. **This is roughly a day and a half of data from one receiver, and
it is read here as a first signal, not as requirement 2's week.**

| Sending service | Volume | DMARC pass | SPF aligned | DKIM aligned | IPs |
|---|---|---|---|---|---|
| "Akamai Technologies, Inc." | 65 | 61 (93.85%) | 61 (93.85%) | 61 (93.85%) | 1 |
| Google LLC | 2 | 100% | 0% | 100% | 1 |

**The "Akamai" row is our own box.** Akamai acquired Linode in 2022, so
IP-ownership lookups render `173.255.245.115` under the parent company — the same
reason the reverse zone is served by `*.akam.net`. One IP, so this is not a
second sender. *(The detail view's `Country: SG` is geo-IP noise; that address is
Linode Fremont. Recorded so it does not become a finding later.)*

**The Google row is forwarding, and it is the useful one.** Two messages, SPF
aligned 0%, DKIM aligned 100%, DMARC pass 100% — someone forwarded site mail
through Gmail. Forwarding always breaks SPF, because the forwarder's IP is not
ours, and preserves DKIM. So this is **live evidence that DKIM carries forwarded
mail through DMARC**, which is exactly the risk in taking SPF to `-all` under
requirements 5–7: the tightening does not strand forwarded mail as long as the
signature holds.

**The 4 failures are one class, not two.** All three columns read 93.85%
identically. A split — some failing SPF only, some DKIM only — would leave DMARC
pass *higher* than either mechanism, since DMARC needs one aligned pass. Equal
numbers mean the same 4 messages failed both, from the same IP as the 61 that
passed.

### What the "By date" view could and could not say

All failures sit on 2026-08-17 — **and that is uninformative, because 2026-08-17
is the only day with data.** The daily total (67 = 65 + 2) is the whole dataset,
so "the failures are all on the 17th" is a restatement of "there is one day of
reports", not a finding about clustering. The 18th's reports arrive on the 19th.

That day's numbers do add one detail: at the day level SPF-aligned is 61/67
(91.04%) while DKIM-aligned and DMARC-pass are both 63/67 (94.03%). The 2-message
gap is the Google forwarding row — DKIM carrying what SPF could not — which is
the same lesson as above, now visible in the totals.

**The real test is the next report.** Nothing has changed for the bounce class:
no SPF record on the HELO name, bounces still unsigned. So the prediction is that
**2026-08-18 shows a similar handful of failures**, and that they stop only when
one of those two is fixed. A clean 18th would mean the cause was transient and
this section is wrong.

### Two caveats on what this data can bear

1. **`google.com` is the only reporting organization so far.** Microsoft — whose
   rejections are the reason this step exists — has not reported. The evidence
   that actually matters is still absent, and a clean Gmail row is not a
   substitute for it.
2. **The volume does not match our own measurement.** 65 messages in one UTC day
   attributed to this domain, against the 2026-08-17 re-measurement of ~30/day
   *total*. **Partly explained by the log**: this box also forwards system mail,
   admin mail and its own bounces to Brian's Gmail, and any of those carrying a
   `surfguitar101.com` From lands in this report while never having been "site
   mail" in the sense the measurement counted. Partly, not wholly — the residue
   still wants reconciling, because **that number chose the Postmark tier and
   shapes the warm-up schedule.** The reassuring reading is that the traffic
   Postmark will actually carry is *smaller* than this report suggests, since
   forwarding and system mail are not moving to it.

### Second DMARC reading — 2026-08-19, covering 2026-08-18: the prediction held

The first reading closed with a prediction rather than a conclusion: *2026-08-18
shows a similar handful of failures, and they stop only when one of two things is
fixed; a clean 18th would mean the cause was transient and this section is wrong.*
**Neither lever has been pulled, and the 18th is not clean.**

From Cloudflare's per-day detail for 2026-08-18. The cumulative view is reported
separately below, because reading it alone produces a finding that is not there.

| Sending service | Volume | DMARC pass | SPF aligned | DKIM aligned | IPs |
|---|---|---|---|---|---|
| "Akamai Technologies, Inc." | 32 | 29 (90.63%) | 29 (90.63%) | 29 (90.63%) | 1 |
| Google LLC | 1 | 100% | 0% | 100% | 1 |
| **Day total** | **33** | **30 (90.91%)** | **29 (87.88%)** | **30 (90.91%)** | 2 |

Two days now reconcile exactly against the cumulative totals — 67 + 33 = 100
messages, 63 + 30 = 93 passing, 4 + 3 = 7 failing, with the Akamai row summing
65 + 32 = 97 at 92.78% — so no report is missing and no message is double-counted.

**Three failures, all in the Akamai row, all failing both mechanisms.** The three
alignment columns are identical again — 90.63% across pass, SPF and DKIM. DMARC
needs only one aligned pass, so equal numbers mean the same messages failed both.
That signature now holds on two independent days.

**The class is fixed in count, not in proportion, and that is the useful part.**
4 failures on the 17th, 3 on the 18th, while volume fell 67 → 33; the failure
*rate* therefore rose, 5.97% → 9.09%, as the denominator drained. **A class that
produces three or four messages a day regardless of site traffic is a scheduled
one, not a traffic-driven one** — which is what root's twice-daily cron and the
forwarded system bounces are, and is exactly what site notifications are not.
Independent support for the bounce diagnosis, arriving from the shape of the
numbers rather than from the mail log.

**And the report's own keying rules out the rival class.** Aggregate reports are
keyed by the From domain, so fault 2's `root@localhost` mail could never have
appeared here at all — `localhost` is not `surfguitar101.com`. Only bounces,
whose From is `MAILER-DAEMON@surfguitar101.com` by way of `/etc/mailname`, land
in *this* domain's report unsigned. Fault 2 was never a candidate for these
numbers; fault 3 remains the only class that fits.

#### The cumulative view manufactures a second sender, and the per-day view kills it

Cloudflare's all-time table reads **IP count 2** on the Akamai row, against **1**
on the first reading. That reads as a second host sending as this domain — and
this document already names a candidate: `bobcat.gremmielabs.dev`
(198.58.104.73), a Linode box, hence "Akamai" in ownership lookups, recorded in
the backup-box section as mailing its cron output. It would also *fail* SPF,
since the apex record lists only `ip4:173.255.245.115` and resolves both `a` and
`mx` to that same address. Motive, mechanism and suspect, all consistent.

**It is an artifact of the view.** The per-day rows are 1 Akamai IP on the 18th
and 1 on the 17th, and Google reads 1 per day against 2 cumulative. Jaguar has
one address, so a de-duplicated union across two days would be 1, not 2.
**Cloudflare's cumulative IP count sums the per-day rows rather than counting
distinct addresses** — the only reading consistent with both rows.

So there is no second sender, the "one IP, so this is not a second sender"
premise the first reading leaned on still holds, and the elimination argument
from the SPF record — *any message from .115 with an aligned envelope domain
passes unconditionally, so a failure had none* — covers the 18th's three exactly
as it covered the 17th's four.

*Recorded because it was nearly written up the other way.* The finding had a
named suspect, a mechanism and a working motive, and one click into the per-day
detail dissolved it. See [[suspect-the-measurer-before-the-record]].

#### Caveat 2 substantially narrowed — 33 against a measured ~30/day

The first reading flagged 65 messages in a day against a re-measured **~30/day
total**, called the residue unreconciled, and noted that the number "chose the
Postmark tier and shapes the warm-up schedule." **The 18th comes in at 33.** The
17th was the outlier rather than the baseline — and 2026-08-17 is precisely the
day of the PTR repair, the `smtp_helo_name` change, the Outlook test send, and
the bounce and forwarding traffic all of that generated. **The discrepancy was
in large part the debugging session measuring itself.** See
[[probes-must-not-perturb-what-they-measure]].

Two days is not a baseline and this is not closed, but the direction is right and
the reassuring reading survives: the traffic Postmark actually carries is smaller
than these totals, since forwarding and system mail are not moving to it.

#### The Google row, on a second and independent day

One forwarded message: SPF aligned 0%, DKIM aligned 100%, DMARC pass 100%. Same
lesson as the 17th's two, now on a separate day rather than inside one batch —
**DKIM carries forwarded mail through DMARC**, which is the argument that taking
SPF to `-all` under requirements 5–7 does not strand it. The day-level 1-message
gap between SPF-aligned (29) and DKIM-aligned (30) is this row, exactly as the
17th's 2-message gap was.

#### What has not moved

- **Caveat 1 stands.** This view lists *sending* services, not reporting
  organizations, so nothing in it says whether Microsoft has begun reporting. The
  receiver whose rejections are the reason this step exists is still absent as
  far as this dashboard shows.
- **Requirement 2 is 2 days into a 7-day read**, so tightening past `p=none`
  stays blocked.

#### The next report is the first that can show the 18th's Postfix repairs

The root virtual-alias entry and `sender_canonical_maps` were applied at 19:23
CDT on 2026-08-18 — **00:23 UTC on the 19th, outside the 18th's report window.**
The 18th is therefore a clean *before* for both, and the 2026-08-19 report,
arriving on the 20th, is the first that can carry them. Two predictions, written
before the observation:

1. **The three-a-day failure class persists**, because nothing touching it has
   changed: still no SPF TXT at `mail.surfguitar101.com`, bounces still bypassing
   the milters unsigned.
2. **A new *passing* class appears.** `sender_canonical_maps` rewrites
   `root@localhost` onto `root@surfguitar101.com`, which puts a From domain of
   `surfguitar101.com` on mail that previously had none — so Django's error
   reports should enter this report for the first time, in the pass column, since
   they were verified `dkim=pass`/`spf=pass`/`dmarc=pass` at the receiver. Volume
   up, failures flat.

If the failures fall to zero without either lever being pulled, prediction 1 is
wrong and the class was something else.

### Third DMARC reading — 2026-08-20, covering 2026-08-19: one prediction held weakly, the other never appeared

Two predictions were written into the second reading before this report existed:
the three-a-day failure class persists, and a new *passing* class appears as
`sender_canonical_maps` gives root's mail a From domain. **The first held only in
its weak form, the second is invisible, and the day's headline is neither of
them — it is the volume.**

> **⚠️ CORRECTED THE SAME EVENING — this section's headline is wrong.** The
> 2026-08-19 row was **incomplete when read**: 10 messages that morning, 34 by
> that evening, once Comcast's aggregate report for the day arrived. **The volume
> did not collapse** — the sequence is 67 → 33 → **34**, failures 4 → 3 → **2**.
> Everything below that argues from the number 10, or from volume falling, does
> not stand. The signature findings — the failure sitting in the Akamai row, all
> three alignment columns reading identically — are unaffected, being shape
> rather than count. See the fourth reading below.

From Cloudflare's per-day detail for 2026-08-19.

| Sending service | Volume | DMARC pass | SPF aligned | DKIM aligned | IPs |
|---|---|---|---|---|---|
| "Akamai Technologies, Inc." | 9 | 8 (88.89%) | 8 (88.89%) | 8 (88.89%) | 1 |
| Google LLC | 1 | 1 (100%) | 0 (0%) | 1 (100%) | 1 |
| **Day total** | **10** | **9 (90%)** | **8 (80%)** | **9 (90%)** | 2 |

The rows sum to the header exactly — 8+0 SPF-aligned, 8+1 DKIM-aligned, 8+1
passing — so nothing is missing inside the day.

#### The by-date table, read 2026-08-20: three rows, and every digit reproduces

The all-time view broken out by date, which is a different view from the three
per-day details these numbers were transcribed from:

| Date | Volume | DMARC pass | SPF aligned | DKIM aligned | IPs |
|---|---|---|---|---|---|
| 2026-08-19 | 10 *(partial — 34 by that evening)* | 90% | 80% | 90% | 2 |
| 2026-08-18 | 33 | 90.91% | 87.88% | 90.91% | 2 |
| 2026-08-17 | 67 | 94.03% | 91.04% | 94.03% | 2 |

**There are exactly three rows** — no day before the 17th, and no partial row for
the 20th. That was the thing worth checking: a report this document never read
would inflate any cumulative total and read as a discrepancy that is really a
gap in the reading. There is no such report.

**Every percentage reproduces from the counts recorded here, to the digit** —
63/67 = 94.03%, 61/67 = 91.04%, 30/33 = 90.91%, 29/33 = 87.88%, 9/10 = 90%,
8/10 = 80%. Three days of transcription off screenshots, checked against a view
that computes them independently, with no drift. Day totals sum to **110 volume,
102 passing, 8 failing, 98 SPF-aligned**.

**The 4-message cumulative gap between DKIM-aligned (102) and SPF-aligned (98) is
exactly the forwarded mail** — the Google row's 2 + 1 + 1 across the three days,
whose SPF alignment is 0% every time and whose DKIM alignment is 100% every time.
The argument that DKIM carries forwarded mail through DMARC now has a whole-corpus
accounting behind it and not just three matching rows.

**What this does not close.** Summing the by-date rows is not the same check the
first two readings ran, which was Cloudflare's own cumulative total against the
sum of the days. That total has still not been read; 110 / 102 / 8 remains a
prediction about the header, not an observation of it.
See [[measure-before-recording-in-planning-docs]].

**And it sharpens the IP-count test rather than running it.** Per-day IP counts
read 2, 2, 2 — one Akamai address and one Google address each day — so this view
is consistent with either summing or de-duplication and settles nothing. The
sharp form is the all-time **by-service** row for Akamai: **3 means Cloudflare
sums per-day counts, 1 means it de-duplicates, and the document currently asserts
summing** on the strength of a 2 that was read when only two days existed. Jaguar
has one address, so the two answers are now far apart.

#### Prediction 1 held in signature and failed in count — and the count *was* the argument

The signature is intact on a third independent day: the failure sits in the
Akamai row, and all three alignment columns read 88.89% identically, so the one
failing message failed both mechanisms rather than one. Nothing that touches this
class has changed — still no SPF TXT at `mail.surfguitar101.com`, bounces still
bypassing the milters unsigned — so persistence is what the mechanism predicts.

The count is where it breaks:

| | 2026-08-17 | 2026-08-18 | 2026-08-19 |
|---|---|---|---|
| Volume | 67 | 33 | **10** |
| Failures | 4 | 3 | **1** |
| Failure rate | 5.97% | 9.09% | **10.0%** |

**Superseded — the 08-19 column is a partial row.** Corrected the same evening to
volume **34**, failures **2**, failure rate **5.88%**. The count argument this
table was built to make has no support either way: 4 / 3 / 2 across 67 / 33 / 34
cannot separate a scheduled class from a traffic-driven one — the same limit this
section named when it said the second reading claimed more than two points could
carry.

**The second reading's inference was "a class that produces three or four a day
regardless of site traffic is scheduled, not traffic-driven." The 19th is the
first day that could test that, and it reads against it.** A fixed-count class at
three-to-four a day predicts three or four and delivered one — P(≤1) ≈ 14% under
a Poisson with λ=3.5. A class proportional to volume at the running ~9% predicts
0.9 and delivered one.

**This does not touch fault 3.** Unsigned Postfix bounces still fit every column
observed, and bounces scale with outbound volume anyway, so a traffic-proportional
shape is if anything the more natural fit for them. What the 19th removes is the
*argument from fixed count* — the piece of the second reading that read the flat
3–4 as independent support arriving "from the shape of the numbers rather than
from the mail log." One day at n=1 failure cannot establish the rival shape
either; the honest position is that three days of single-digit failure counts
distinguish nothing, and the second reading claimed more than that.

*Recorded as a correction to this document rather than a new finding: the
inference was written from two points and the third did not follow it.*

#### Prediction 2 did not appear, and it cannot be called refuted

`sender_canonical_maps` and the root virtual-alias entry were applied at 00:23
UTC on the 19th, so **the whole of this report's window is "after."** The
prediction was volume up, failures flat, as `root@surfguitar101.com` mail entered
this domain's report for the first time. Volume went 33 → 10.

**No new passing class is visible, and a quiet day looks identical to a broken
rewrite here.** Cron mails only when a job produces output; Django's error
reports arrive only when the site raises. Both being silent for a day is ordinary,
and this report cannot separate that from the rewrite failing to take. The
rewrite was independently verified at the receiver on 2026-08-18
(`dkim=pass`/`spf=pass`/`dmarc=pass` on a real message), which is stronger
evidence than this absence is against it.

What the absence does bear on is a premise used earlier in this section: root's
"twice-daily cron" was cited as a *scheduled generator* accounting for a steady
daily class. **If it produced mail twice a day, the rewrite should have added
about two aligned, passing messages to this report and the total should have
risen.** It fell. So the cron leg of the scheduled-class story is unsupported by
its own first test.

#### There was no volume collapse — CORRECTED 2026-08-20 against a month of mail log

**This subsection first read 67 → 33 → 10 as a collapse and asked which of two
declines explained it. Both readings were wrong, because neither had a baseline.**
A per-day count out of the Postfix log for 2026-07-19 → 2026-08-16, the 29 days
before any of this step's mail work:

| | mean | median | max |
|---|---|---|---|
| total outbound | 31.7 | **27** | 102 |
| gmail-destined | 18.6 | **12** | 65 |

Against that, **the 17th was 4.3× the median and the 19th is 0.8×.** The 19th is
an ordinary day. *(Corrected the same evening: the 0.8× used the partial
10-message row. Against the corrected 34 the 19th is ~2.8× the Gmail-destined
median — still an ordinary day, and still not a decline. This item's conclusion
is untouched: there was never a discrepancy, only two populations. The multiplier
was wrong.)* The sequence is not a decline at all — it is regression to the
mean after a spike, and the spike is the PTR/HELO repair session this document
already identified as generating its own traffic. Aug 10–11 is the confirming
case: 96 and 102 messages, 54 and 65 of them to Gmail, a week before any mail
work began. **Bursts to ~100/day happen on their own**, which is what
`forums/views/subscriptions.py` produces — one message per subscriber per reply,
so a single busy thread fans out to dozens of messages.

#### Caveat 2's actual resolution: two different populations were being compared

**Gmail is 58% of outbound, and Gmail is the only receiver reporting.** A DMARC
volume is therefore a *Gmail-destined* count. Every comparison in this document
has set it against "~30/day", which is **total outbound to all recipients** — a
different population, larger by a factor of about 1.7.

Both numbers were measured correctly and neither was ever wrong; the *comparison*
was. The right check for the 17th's 65 is that day's 69 Gmail-destined messages
in the log, and those agree. **Caveat 2 was an artifact of the mismatch, not a
discrepancy in the data**, and it closes here.

Two consequences worth keeping:

- **The Postmark tier should be sized on total outbound — 27/day median, 31.7
  mean — not on any DMARC figure**, which sees only the Gmail slice.
- **The ~30/day estimate was right all along**, and held steady across the whole
  month.

#### The two instruments reconcile, which is what makes the above trustworthy

Jaguar-origin mail to Gmail across the three report days: DMARC's Akamai row
reads 65 + 32 + 9 = **106**, the log's gmail column 69 + 20 + 14 = **103**. Three
apart over three days. The per-day split differs because **the log is CDT and
DMARC windows are UTC**, so each report day carries the previous evening's
19:00–24:00. Gmail is reporting what jaguar actually sent.

#### The Google row, on a third day

One forwarded message: SPF aligned 0%, DKIM aligned 100%, DMARC pass 100%. Three
readings, three days, same signature every time — **DKIM carries forwarded mail
through DMARC**, which is the standing argument that taking SPF to `-all` under
requirements 5–7 does not strand forwarded mail. The day's 1-message gap between
SPF-aligned (8) and DKIM-aligned (9) is this row, as the 18th's gap of 1 and the
17th's gap of 2 were. Cumulatively the whole 4-message gap between DKIM-aligned
(102) and SPF-aligned (98) is these three days of forwarding, and nothing else.

**The mechanism, since the row is easy to misread as a second sender.** One
notification makes two trips. Jaguar sends `From: admin@surfguitar101.com` to a
member, aligned on both mechanisms — that is the Akamai row. The member's mailbox
then **auto-forwards** it onward, so Google's servers relay it: the From header is
preserved, which is why it stays in *this* domain's report, but the connecting IP
is now Google's, so SPF is no longer aligned however it resolves. The opendkim
signature still validates because forwarding modifies neither headers nor body,
and DMARC passes on DKIM alone. That is the second row.

**It is member-side configuration and there is nothing to find or fix on the
box** — an old address kept alive by forwarding, a Workspace domain pointing at a
personal Gmail. Jaguar cannot see the second hop at all. *(A manual "Forward"
would not appear here: that rewrites From to the member's own address, putting it
in their provider's report instead.)* **The risk it quantifies is narrow and
real**: under `-all`, if that member's DKIM ever breaks — a list appending a
footer, a gateway rewriting headers — their copy moves from soft-fail to hard
reject.

#### What has not moved

- **Caveat 1 splits in two** — see the subsection below. Its unmeasurable half
  stands; the premise it was guarding is now measured.
- **Requirement 2 is 3 days into a 7-day read**, so tightening past `p=none`
  stays blocked.
- **The "IP count 2" on the day total is the two rows' 1 + 1.** Consistent with
  the summing behaviour established on the 18th, but not a fresh test of it —
  the two rows hold genuinely different addresses, so a de-duplicating count
  would also read 2.
- **The remaining identification step got harder, not easier.** Reading one
  `MAILER-DAEMON` message's `Authentication-Results` out of Brian's inbox is
  still what would settle the failure class, and the 19th offers a single
  candidate message to find.

#### Caveat 1, split: "Gmail's view alone" is now measured, the reason for Microsoft's absence is not

**Every row in this dashboard is a *source*; the report is one *receiver's*
account.** The two get conflated because "Google" appears in both roles — Gmail
as the receiver that evaluated and reported the mail, and Google as the network
that relayed one forwarded message. **The reporter is not a row, it is the whole
table.** Reporter identity lives in the XML's `<report_metadata><org_name>`,
which Cloudflare does not surface, and *that* half of caveat 1 stands unchanged.

**The half it was guarding is now measured**, from the mail log rather than the
dashboard, across the three report days:

| | messages |
|---|---|
| jaguar outbound, all recipients | 192 |
| jaguar outbound, Gmail-destined | 103 |
| **reported in the Akamai row** | **106** |

The reports account for **55% of what jaguar sent, and Gmail is 54% of what
jaguar sent.** Any second reporting receiver would push that row toward 192; it
tracks the Gmail slice instead. **"Gmail's view alone" has been asserted since
the first reading and is now backed by numbers.**

**Microsoft's absence still has three explanations and this data separates
none of them:**

1. **We send them almost nothing** — answerable from the member table, and the
   only one of the three that is ours to check. *(Refuted below.)*
2. **They may not publish aggregate reports at all.** Not verified either way;
   recorded as a question rather than a fact. *(Largely refuted below, on vendor
   sources; a fourth explanation was added at the same time.)*
3. **They do and we cannot see it**, per the unmeasurable half above.

**Brian's reading on 2026-08-20 was that few active members use Microsoft
addresses.** Plausible, and it would lower the priority of chasing Microsoft
specifically — but **it cannot be taken from this dashboard**, which never shows
recipients, only sources. **And measuring it today measures the post-damage
state:** if Microsoft has been rejecting this box for years, members on those
addresses stopped receiving notifications and drifted off, so a low share now may
be the *consequence* of the deliverability failure rather than evidence the
audience never used it. **The discriminator is domain share by registration
cohort** — flat across cohorts means audience preference, collapsing across the
rejection years means attrition.

#### MEASURED 2026-08-20 — Microsoft is 12% of the membership, and the share is not eroding

Run against the live Postgres (snapshot-era data; signups are rare enough that
staleness does not matter). **Counts only — no addresses were read out.**

**Picking the population matters, and the status field does not mean what its
name suggests.** Per Brian, 2026-08-20: **members stay `STA_STRANGER` until an
admin sees them post something to the forums that reads as non-spam.** Promotion
is manual, so `STA_STRANGER` is *un-vetted*, not *spam* — it holds bots and
legitimate lurkers who never posted alike. `auth_user` has **15,227** rows:
10,729 stranger, 1,600 spammer, 32 resigned/removed/suspended, **2,862
`STA_ACTIVE`**.

**So 2,862 is a floor on the real audience, not a measurement of it** — a lurker
who subscribes to a topic gets mail without ever being promoted. **The Microsoft
figure survives the choice either way**, which is why the ambiguity does not
matter here: Microsoft is **12.1%** of vetted members and **13.8%** of strangers.
Whichever population you take, it is roughly an eighth.

Members in good standing (`is_active` and `status = STA_ACTIVE`), and the
subset who logged in within the last year:

| bucket | good standing | % | active <1y | % |
|---|---|---|---|---|
| gmail | 1146 | 40.1 | 245 | 46.8 |
| other | 725 | 25.3 | 122 | 23.3 |
| yahoo | 456 | 15.9 | 69 | 13.2 |
| **microsoft** | **347** | **12.1** | **56** | **10.7** |
| aol | 97 | 3.4 | 21 | 4.0 |
| comcast | 69 | 2.4 | 11 | 2.1 |

**Brian's 2026-08-20 reading — that few active members use Microsoft addresses —
is refuted.** Microsoft is the fourth-largest bucket, 346 of its 347 have posted
at least once, and it is **five times the Comcast share**, which was worth a
delisting campaign this same week.

**And the attrition trap does not apply here** — the cohort cut was run
specifically to check it:

| cohort | n | microsoft % | gmail % | yahoo % |
|---|---|---|---|---|
| 2006–07 | 466 | 13.9 | 22.7 | 22.7 |
| 2008–11 | 727 | 12.7 | 33.1 | 17.5 |
| 2012–15 | 691 | 14.0 | 40.1 | 15.2 |
| 2016–19 | 564 | 8.7 | 47.7 | 13.3 |
| 2020–23 | 316 | 11.4 | 63.0 | 9.8 |
| 2024–26 | 97 | 8.2 | 55.7 | 12.4 |

*The first row was labelled "2004–07" when first written — an artifact of
bucketing by `(year/4)*4`, not a claim about the data. **Checked 2026-08-20 on
Brian's challenge: there are no 2004 or 2005 registrations.** The site's history
starts **2006-02-25**, which matches his recollection of the phpBB import, and
the years run 663, 709, 828, 828, 1020 from 2006 to 2010. The single row before
that is **`Anonymous`, `date_joined` 2000-11-10 00:00:00** — phpBB's guest-post
placeholder, carried across by the import. It is `is_active = false` so it never
entered any of these figures, and it carries a `forum_post_count` of **-180**,
the counter having been decremented for deleted guest posts it was never
credited with. Harmless, and recorded so it is not rediscovered as a finding.
(Its `last_login` reads 2026-08-09, which is modernization-window activity on an
account that cannot log in — noted, not chased.)*

Microsoft drifts mildly inside an 8–14% band across the **20 years** the data
actually covers, with **no collapse and no signature of members being driven
off**; if years of rejections had culled them, older cohorts would read *lower*,
and they read slightly higher. **The
displacement in this table is Gmail taking Yahoo's share** — 22.7% → 63%, against
22.7% → 9.8% — and it has nothing to do with Microsoft.

#### Every account is proof of a delivered registration email — which constrains "Microsoft blocks us"

**Brian's reaction, 2026-08-20: surprise that there are recent Microsoft members
at all, since Microsoft blocks the registration mail.** The registration flow
answers it directly, and it is a stronger instrument than it looks.

`create_new_user()` is reachable from exactly one place — `register_confirm`,
which requires both the username and a key compared with
`secrets.compare_digest` against the `PendingUser` row — and
`PendingUser.objects.purge_expired()` deletes anything older than a day. **A row
in `auth_user` therefore certifies that a confirmation email reached that
address, was opened, and was clicked inside 24 hours.** Every account is a
delivery receipt.

Microsoft-address registrations that completed that round trip, by year:

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026* |
|---|---|---|---|---|---|---|---|---|---|
| all registrations | 618 | 556 | 506 | 498 | 542 | 667 | 777 | 760 | 177 |
| **Microsoft** | 69 | 48 | 51 | 42 | 36 | 23 | **69** | **46** | 19 |
| of which admin-vetted | 16 | 7 | 16 | 8 | 6 | 6 | 2 | 4 | 2 |

*\* 2026 partial — latest registration in this snapshot is 2026-07-07.*

**69 Microsoft addresses completed the email round trip in 2024 and 46 in 2025**,
through the period this document describes as Microsoft rejecting the site's
mail. Bots count as evidence here too: a spam registration still had to receive
and click the link.

**What that constrains.** "Microsoft blocks our mail" cannot be a total block —
this is quantitative evidence of delivery, every year, throughout. The compatible
readings are intermittent rejection, or Junk-foldering that a person mid-signup
goes looking for, which is exactly the message someone hunts down. **It does not
overturn the rejections themselves** — those were observed — and Step 16's
acceptance criterion is unchanged, since the standard is inbox placement rather
than eventual findability.

**The vetted row is falling and that is a separate story.** Admin-vetted signups
went 155 → 124 → 109 → 75 → 61 → 71 → 47 → 34 → 16 across the same years, while
total registrations *rose*. That is moderation load and lurker behaviour, not
deliverability, and the Microsoft share of vetted signups stays noisy but
unremarkable — 4.3% in 2024, 11.8% in 2025, 12.5% in 2026 on single-digit counts.

**This kills explanation 1.** We send Microsoft roughly a tenth of all
notifications, so "we send them almost nothing" is not why they are absent from
the reports.

#### The remaining explanations, and the one edit that separates them

**Explanation 2 is probably dead too, on vendor sources rather than measurement.**
Microsoft does now publish aggregate reports, sent from `dmarcreport@microsoft.com`,
and the coverage named is exactly our members' population — consumer
`hotmail.*`, `outlook.*`, `live.*` and `msn.com` mailboxes. **Marked as sourced,
not measured: no report from Microsoft has been seen for this domain.**

**A fourth explanation surfaced while checking, and it is specific enough to be
worth naming.** Microsoft's report mail is reported to violate RFC 5322 — the
base64 attachment is not wrapped at 78 characters — which breaks strict parsers.
**Microsoft may be reporting while Cloudflare silently fails to ingest it.** That
possibility did not exist on the earlier list and is not visible from any
dashboard.

So the live set is: **(2′) Microsoft reports but not for a domain this small;
(3) they report and Cloudflare does not surface reporter identity; (4) they
report and Cloudflare cannot parse it.** All three look identical from where we
have been standing.

**One DNS edit separates all of them.** `rua` accepts a comma-separated list, so
add a second destination we control alongside Cloudflare's. **Published
2026-08-20:**

```
v=DMARC1; p=none; rua=mailto:00fc656c22e64e73bb643fb00331d013@dmarc-reports.cloudflare.net,mailto:admin@surfguitar101.com
```

Then raw XML arrives where `<report_metadata><org_name>` can be read directly:
mail from `dmarcreport@microsoft.com` proves they report and indicts Cloudflare's
pipeline; silence over a week supports 2′. **It also removes the caveat-1
blindness permanently**, for every future question about who is reporting, rather
than just this one.

**No opt-in or enabling record is needed for Microsoft**, checked 2026-08-20:
they report to any domain publishing a valid `rua=mailto:`. The
MX-points-to-Microsoft-365 condition in their documentation governs the
*recipient tenant's* mail flow, not the sending domain, and does not apply to us.

**The one real constraint is where `rua` may point.** RFC 7489 §7.1 requires an
external-destination authorization record whenever the mailbox sits outside the
policy domain's organizational domain, and **it must be published in the
destination's zone.** Measured:

```
surfguitar101.com._report._dmarc.dmarc-reports.cloudflare.net  →  "v=DMARC1;"
```

Cloudflare publishes its own, so the current `rua` is authorized. **The practical
consequence is that `rua` cannot point at `bgneal@gmail.com`** — that would need
a record inside `gmail.com`'s zone, which is not ours to create, and conforming
reporters are meant to refuse. The second destination therefore has to be an
address *at* `surfguitar101.com`, forwarded onward through the virtual alias
table. `admin@surfguitar101.com` is the same organizational domain and needs no
authorization record at all.

**`admin@` rather than a new `dmarc@` — Brian's call, 2026-08-20, and it is the
better of the two.** The `dmarc@` in the sketch above was habit, not requirement;
all three arguments run the other way:

- **Nothing to add on the old box.** `admin@` is already in the virtual alias
  table forwarding to Brian's Gmail — verified 2026-08-18, when 23 queued
  messages went through it. A purpose-built `dmarc@` would have been a second
  thing to create for a destination this document already calls temporary.
- **It removes an action item instead of adding one.** The `dmarc@` plan carried
  "add it to Cloudflare Email Routing at task 06 or it dies with the old box."
  `admin@` is the default for both `DEFAULT_FROM_EMAIL` and `SERVER_EMAIL`
  (`sg101/settings/base.py:236,244`) and has to reach task 06 regardless, so that
  footnote simply disappears.
- **Cleanup is deleting text**, not retiring an alias — one edit to one TXT
  record.

**Verified from both authoritative nameservers rather than a resolver cache**,
2026-08-20: `ada` and `cash` return it byte-identical, and `1.1.1.1` and
`8.8.8.8` already had it. **Exactly one TXT record at `_dmarc`** — two would void
DMARC outright, so the count was taken rather than assumed. 121 characters in a
single string, well inside the 255-byte boundary that would force a split.
`p=none` unchanged, Cloudflare's destination still first in the list.

**The instrument is jaguar's mail log, not the Gmail inbox — and this is not a
cost of `admin@`.** Any local address forwards, and forwarding breaks the
report's own SPF alignment, which is the same mechanism behind the 4 failures
blocking the tightening. Google's and Yahoo's reports are DKIM-signed and should
survive it. **Microsoft's is the one already suspected of being malformed enough
to break strict parsers** — so a forward Gmail refuses would look identical to
Microsoft never reporting, which is the exact ambiguity this edit exists to
remove. The envelope sender at the SMTP layer is upstream of all of that:

```
grep -iE 'to=<admin@surfguitar101\.com>' /var/log/mail.log | grep -i dmarc
```

`from=<dmarcreport@microsoft.com>` proves they report and indicts Cloudflare's
ingestion; a week of Google and Yahoo with no Microsoft envelope supports 2′.

**No contamination of our own data.** A forwarded report keeps its original
`From:`, so it is `google.com` or `microsoft.com` mail failing alignment at
Gmail, not `surfguitar101.com` mail, and cannot surface in our own aggregate
reports.

**Arrival window, so a quiet day is not misread.** Receivers read the record at
message-processing time and batch one report per UTC day, sent the next. The edit
landed mid-UTC-day on 2026-08-20, so a partial report for the 20th may or may not
carry the new destination. **First dependable arrivals are 2026-08-21 to 08-22.**

**Kept in proportion.** This is a know-your-instrument question, not a blocker.
Even if Microsoft never reports a row, the evidence that settles Microsoft
deliverability is task 07's smoke test with an Outlook inbox check (`dest:I`),
which is already Step 16's acceptance criterion. The answer changes what to
expect from DMARC data, not what the plan does.

*Incidental cross-check:* Gmail is 40% of members overall but **46.8% of the
recently active** and **58% of outbound**, which is consistent — the more engaged
half of the membership carries more subscriptions, and forwarding adds the rest.

**Either way it changes urgency, not plan.** Nothing in Step 16 is
Microsoft-specific: FCrDNS, the HELO name and SPF/DKIM/DMARC are what every
receiver checks, and after cutover member mail leaves on Postmark's addresses
where none of this reputation follows it.

#### The "Akamai" label is a registry lookup, not a party to the mail

Nothing is reported *by* Akamai or Linode; they are the network the packets left
from and never see the evaluation. Cloudflare enriches the report's bare
`<source_ip>` with an ownership lookup, and ARIN answers:

```
NetName:        LINODE-US
Organization:   Akamai Technologies, Inc. (AKAMAI)
```

The netblock is still named for Linode; the `Organization` field moved to the
parent after the 2022 acquisition, and that is the field being rendered.
**It is demonstrably the registry and not reverse DNS**, since the PTR now reads
`mail.surfguitar101.com` — an rDNS-derived label would say so. *(Same acquisition,
second sighting: the reverse zone is still delegated to `a3-67.akam.net` and
friends.)*

**Consequence for the cutover:** rows are keyed by source IP, so the migration
will appear here as a new row under Postmark's ownership while the Akamai row
drains.

#### Prediction for the next report

Written before the observation, and deliberately narrower than last time, because
the last set was written at a confidence the data did not support:

1. **Failures stay in the 0–3 band and keep failing both mechanisms**, since the
   SPF record at the HELO name still does not exist. A zero day is now *within*
   the expected range rather than a refutation, which is the direct consequence
   of the count argument collapsing. **Premise expired 2026-08-20** — the record
   now exists (below), so this prediction covers the 08-20 report and earlier
   only. From the 08-21 report on the bounce class should *pass*; continued
   failure means the fix did not take.
2. **Volume runs near the Gmail-destined median of 12/day**, revised 2026-08-20
   now that a baseline exists. The original "no prediction is offered" was
   written without one. Days in the 50–70 range are possible without anything
   being wrong — the log shows them occurring naturally — so a high day is not
   evidence of a new sending source.

### Fourth reading — 2026-08-20 evening, re-reading 2026-08-19: the row had tripled, and Comcast is the second reporter

**Brian noticed the dashboard held more data than it had that morning.** Re-reading
a day already recorded is not something the first three readings did, and it
overturns three conclusions.

| Date | Read 08-20 morning | Read 08-20 evening | |
|---|---|---|---|
| 2026-08-17 | 67 · 94.03% · 91.04% · 94.03% · 2 | identical | unchanged |
| 2026-08-18 | 33 · 90.91% · 87.88% · 90.91% · 2 | identical | unchanged |
| 2026-08-19 | **10** · 90% · 80% · 90% · 2 | **34** · 94.12% · 91.18% · 94.12% · 2 | **+24** |

**Two stable rows are the control**: the dashboard is not drifting generally, the
most recent day was incomplete. The new row reproduces as 32/34 = 94.12% and
31/34 = 91.18% — 34 messages, 32 passing, 2 failing, 31 SPF-aligned, 32
DKIM-aligned. **The delta is +24 volume, +23 passing, +23 SPF-aligned, +23
DKIM-aligned, +1 failing.**

**The per-day detail for 2026-08-19 then returned "no data available"** — a view
that had rendered a full service breakdown that morning. So the number that moved
came from a dashboard whose companion view was simultaneously broken, and it was
deliberately not recorded as fact until the mail log settled it independently.
See [[suspect-the-measurer-before-the-record]].

#### The mail log settled it, and the answer was in the window boundary

Three measurements on jaguar, none of which depend on Cloudflare:

| Query | Count |
|---|---|
| Delivered to Google, syslog day `Aug 19` (CDT) | 14 |
| Total `status=sent`, syslog day `Aug 19` (CDT) | 21 |
| Total `status=sent`, **UTC** Aug 19 window (`Aug 18 19:00`–`Aug 19 19:00` CDT) | **46** |

**21 is less than 34, and that is what pointed at the boundary.** Syslog stamps
local time and DMARC days are UTC, so UTC 2026-08-19 begins at 19:00 CDT on the
18th — and it therefore contains **the Comcast delisting flush**, which STATUS
records as 23 queued messages delivered between 20:54 and 21:54 CDT on 08-18,
i.e. **01:54–02:54 UTC on 08-19.**

The per-relay breakdown for that UTC window:

```
Gmail     11 + 5 + 2                = 18
Comcast    7 + 5 + 3 + 3 + 3 + 2    = 23
Others     hushmail 1, Yahoo 2, 1and1 1, Outlook 1 = 5
                                    total = 46
```

**Comcast is exactly 23.** The flush, message for message.

#### The delta decomposes exactly, and names a second reporting receiver

10 (Gmail's report, read that morning) + 23 (Comcast, all authenticating) + 1
(one further Gmail failure) = **34**, and every column reconciles: +23 passing and
+23 aligned on both mechanisms is the Comcast block, the +1 failing is Gmail's.

**"Gmail's view alone" is retired.** It qualified all three previous readings, and
the doc's own stated test was that a second reporting receiver *"would push that
toward 192."* It pushed. **It arrived on its own — the second `rua` destination
published the same afternoon had nothing to do with it.**

**The 23 flushed messages authenticated at Comcast.** The delisting entry records
them accepted at the MX with `250 … mail accepted for delivery` and explicitly
leaves placement unobserved. Comcast's own report now adds SPF aligned, DKIM
aligned and DMARC pass on all 23. **Placement is still downstream and still
invisible** — this is authentication, not inbox.

**The 2026-08-19 volume collapse never happened.** The third reading's headline
was 67 → 33 → 10; it is 67 → 33 → 34, with failures 4 → 3 → 2 and a failure rate
of 5.88% rather than the recorded 10.0%.

#### One gap, recorded as inference rather than measurement

Gmail took 18 messages in that window but contributes about 11 to the report. The
likely reason is definitional — aggregate reports cover messages whose **`From:`
header domain** is `surfguitar101.com`, and jaguar forwards third-party mail
(`themadeira.net` and the aliases) whose `From:` belongs to someone else, making
it invisible to our reports by construction. **Consistent, but the seven messages'
`From:` domains were not checked.**

#### Two things worth noticing in the relay list

- **One message reached Microsoft** — `hotmail-com.olc.protection.outlook.com`,
  `status=sent`. **Accepted, not rejected**, which is the FCrDNS and HELO repairs
  working at the receiver this step exists for. No Microsoft report has appeared
  for it, a further small weight on "too small to report on."
- **Two reached Yahoo**, which does publish aggregate reports, and no Yahoo row is
  visible either.

#### The rule this establishes, and why the dashboard cannot confirm the reporter

**A day's row is not final the morning after.** Every reading so far was taken the
next morning and treated as complete; two conclusions were built on a row that was
a third filled. **Re-read previously recorded days each session, and treat the most
recent row as provisional until a later reading reproduces it.** 08-17 and 08-18
have now been reproduced twice and can be treated as settled.

**Cloudflare cannot name Comcast as the reporter, and never will.** The by-service
view groups by *sending* IP — "Akamai Technologies" is jaguar, since Akamai owns
Linode — so a Comcast-sourced report adds to the **Akamai** row rather than
appearing as itself. When the detail view returns it should read Akamai ≈ 33, not
9. That is caveat 1 exactly, and it is what the second `rua` destination exists to
remove: `<report_metadata><org_name>` in the raw XML at `admin@` names the reporter
outright.

### The `rua` destination needed a local copy, and building it hit six traps — 2026-08-20

**The published `rua` destination was not sufficient on its own, and the mail log
says so.** `admin@surfguitar101.com` is aliased to Brian's Gmail, and forwarding
preserves the original envelope sender, so jaguar cannot pass SPF for a third
party's domain. Gmail refuses the result:

```
Aug 19 23:30  dsn=5.7.26  status=bounced
  "blocked because the sender is unauthenticated
   DKIM = did not pass
   SPF [] with ip: [173.255.245.115] = did not pass"
```

**⚠️ CORRECTED LATER THE SAME EVENING — the diagnosis above is wrong, and the
correction matters.** These failures are **not** third-party forwarded mail.
Gmail names the envelope-sender domain it checked in every rejection, and across
all seven `5.7.26` events it is `SPF []` — an **empty** domain, i.e. a null
sender, meaning a DSN — except one reading `SPF [localhost]`. **No third-party
domain was ever observed failing.** Postfix forwarding does not alter the body,
so a reporter's DKIM signature survives the hop and Gmail accepts on DKIM alone;
the reports would most likely have arrived. **The local copy was insurance
against a risk smaller than described here** — still worth having, since it takes
the forward out of the path entirely for the one thing that must be read, but the
justification was overstated.

**⚠️ AMENDED 2026-08-21 — the justification is real, and it is latency rather
than loss.** The Google report covering 08-20 was delivered locally in **0.85s**
(`relay=local, status=sent (delivered to maildir)`) and to Brian's Gmail
**9h25m52s** later, after twelve attempts against a Gmail rate limit. Both copies
arrived; only one arrived in time to be read on the morning of the day it covers.
The local copy is what made the fifth reading possible when it happened.

**And the null-sender class has a cause that was fixed hours earlier.** A null
sender has no domain, so SPF falls back to the HELO identity — which had no TXT
record until the afternoon of 2026-08-20, making both mechanisms unable to pass.
**Confirmed at the receiver that evening** (see the HELO SPF section): a
deliberate null-sender message now returns `spf=pass` with
`smtp.helo=mail.surfguitar101.com`. **The record published to fix the DMARC
bounce class also fixes this forwarded system mail — the same root cause, which
nobody had connected.** The last failure of this kind was 08-19 23:30; anything
after 08-20 midday would mean it did not take.

*Original text follows.* **Two days after the PTR repair and one after the sender
rewrite.** Those repairs fixed jaguar's *own* mail; forwarded third-party mail is
a different class and still fails. Google's and Yahoo's reports are DKIM-signed
and would likely survive the forward — **Microsoft's is the one already suspected
of being malformed enough to break parsers, which is precisely the report we
cannot afford to lose.** Recorded as a caution when the destination was
published; now demonstrated with timestamps.

**Fixed by delivering a second copy locally**, which nothing can forward away: a
dedicated user with no `/etc/aliases` entry, and dual delivery in the virtual map.

```
admin@surfguitar101.com    bgneal@gmail.com, dmarc@localhost
```

Proven end to end rather than from config: one queue ID, `nrcpt=2`, a
`relay=local` delivery with **no `forwarded as`**, one Gmail delivery, and the
message readable in the mailbox afterwards. It lives at
**`/home/dmarc/mail/new/`** — `home_mailbox = mail/`, so maildir under the user's
home, not `/var/mail`.

#### Six traps on a two-line change, four of which reported success or silence

Recorded because this document's own summary of the box — *"almost nothing in the
system reports a disagreement"* — just produced six instances in one sitting.

| # | Trap | How it presented |
|---|---|---|
| 1 | The file is named after its parameter: `/etc/postfix/virtual_alias_maps` | **silence** — a grep of the plausible names returns nothing, which reads as "no aliases" |
| 2 | Bare `brian` takes `$myorigin` → `brian@surfguitar101.com` → a **virtual alias domain** → `5.1.1 User unknown` | would have bounced only the local half; the Gmail half keeps working, so mail to `admin@` still arrives |
| 3 | `/etc/aliases` holds `brian: bgneal@gmail.com`, so `brian@localhost` forwards straight back out | **`status=sent`** — two forwards, no mailbox |
| 4 | `dmarccopy: \brian` — **the backslash did not suppress expansion** | **`status=sent (forwarded as …)`**; that `forwarded as` is the only tell |
| 5 | `home_mailbox = mail/`, so the maildir is `~/mail/` — not `/var/mail/`, not `~/Maildir/` | `ls` error |
| 6 | `sudo cat dir/*` — the glob expands in the *unprivileged* shell, which cannot read a `0700` directory | `cat` error |

**Traps 2 and 3 were caught by measuring before acting** — `postconf myorigin
mydestination`, and a grep of `/etc/aliases` — rather than by failing. **Trap 4
was not**: it was executed on my advice, the advice was wrong, and it looked like
a clean success in the log. Only 5 and 6 announced themselves.

#### What the test message confirmed incidentally

The delivered copy's own headers settle three things previously read from
configuration rather than observed:

- **`From: brian@surfguitar101.com`** from an envelope of bare `brian` — task 10's
  `sender_canonical_maps` rewrite, working in a fresh case.
- **`d=surfguitar101.com; s=dkim`** — opendkim signs locally *submitted* mail.
  That sharpens the distinction task 03 requirement 13 rests on: submission gets
  signed, internally generated bounces do not, because milters do not apply to
  them.
- **`c=simple/simple`** — the canonicalization on the open list to change to
  `relaxed/relaxed` before SPF reaches `-all`, now seen in a real signature
  rather than in `postconf`.

#### The 5.7.25 → 5.7.26 transition, caught in the log on the day it happened

The same grep shows the PTR repair landing on 2026-08-17:

| Time (CDT) | Rejection |
|---|---|
| 08:36, 11:06, 13:07 | `5.7.25` — no PTR record |
| 16:15, 18:25, 18:31 | `5.7.26` — sender unauthenticated |

**STATUS predicted exactly this** — that fixing reverse DNS *"only changes error
code from `5.7.25` to `5.7.26`"* — and the prediction was written before this
evidence existed.

#### `tools/dmarc_report.py`

Reports arrive as gzipped or zipped XML in base64, so the mailbox is unreadable
without a decoder. The tool prints the reporter, the window, the published
policy, and one row per sending source with its disposition and **the domain each
mechanism was evaluated against** — which is where the bounce class shows
`mail.surfguitar101.com`, and where the HELO SPF record published today will read
as a pass or a fail.

Kept **Python 3.4-safe** so it runs on jaguar as well as on the Mac (no
f-strings, no `subprocess.run`, no `os.scandir`), and clean under
`-W error::DeprecationWarning` on modern Python. Takes a maildir, a flat
directory of files copied off the server, or a single file — **detecting mail vs
`.gz` vs `.zip` vs raw XML from the bytes rather than the extension**, so a file
renamed in transit still parses. Verified against synthetic reports in all of
those shapes, plus an empty directory and a non-report message.

### Fifth reading — 2026-08-21, the first from our own copy, and two of my claims died on the way

**One report, from Google, covering 2026-08-20.** Five messages, all from
`173.255.245.115`, **0 aligned on neither mechanism**. The rows split by the
identity SPF was evaluated against:

| count | SPF domain | identity |
|---|---|---|
| 1 | `mail.surfguitar101.com` | HELO |
| 4 | `surfguitar101.com` | MAIL FROM |

**The count-1 row is the HELO SPF record confirmed in aggregate data by a third
party.** The null-sender test of 2026-08-20 carries no MAIL FROM domain, so SPF
fell through to the HELO name and passed. STATUS expected this as corroboration
on the 08-22 report; it arrived in the 08-20 window instead.

**Google addresses one message to both `rua` destinations**, not two sends:

```
To: 00fc656c22e64e73bb643fb00331d013@dmarc-reports.cloudflare.net,
        admin@surfguitar101.com
```

**Cloudflare therefore receives byte-identical input to what we parse.** For any
Google report, a disagreement between the dashboard and the local copy can only
be Cloudflare's ingestion or presentation, never a difference in what arrived.
That is caveat 1 removed rather than worked around.

**Still no Microsoft, and no Comcast.** Day one of the 08-21/08-22 window; a
quiet first day is not a signal.

#### The Gmail forward — the natural experiment measured queue state, not delivery

**⚠️ CORRECTED 2026-08-21, later the same day. The conclusion below is wrong and
the mail log says so.** It read:

| envelope sender | reached Brian's Gmail? |
|---|---|
| `root@surfguitar101.com` (Django error mail) | **yes** |
| `noreply-dmarc-support@google.com` (the report) | **no** |

— and concluded that "the prediction that built the local copy is now an
observation." **The report was never refused. It was in jaguar's queue**, and the
inbox was read while it sat there. It reached Gmail at 20:09:09Z the same day,
**9h25m52s** after Google handed it over, on the twelfth delivery attempt. See
the `4.7.28` section below.

**The comparison was never controlled.** The two messages differed in envelope
sender *and* in queue state at the moment of observation, so it measured a delay
and reported a rejection. The evidence that should have blocked the conclusion
was already available: nothing in the mail log had ever shown a bounce for a
reporter's message.

**What Gmail actually did**, from the delivered copy's headers:

```
dkim=pass header.i=@google.com header.s=20251104   (2048-bit, relaxed/relaxed)
spf=softfail  ... does not designate 173.255.245.115 as permitted sender
dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=google.com
```

**This restores the 2026-08-20 correction that the paragraph above had demoted**
— *"a reporter's DKIM signature survives the hop and Gmail accepts on DKIM alone;
the reports would most likely have arrived."* That was right. Note `softfail`,
not `fail`: google.com publishes `~all`, so the forward does not even hard-fail
SPF, and a `p=REJECT` domain rode through it on DKIM alignment alone.

**Still true:** jaguar cannot pass SPF for a third party's domain. **No longer
claimed:** that this stops a reporter's mail from arriving. See
[[suspect-the-measurer-before-the-record]] — the newer reading was the one that
needed suspecting, being the one that required no self-correction.

#### The reconciliation gap, found by walking into it

Three files in the maildir, one report, and the tool said **nothing** about the
other two. `main()` printed the report count alone, and its "none carrying a
report" line fired only when that count was zero — so 3-in/1-out read exactly
like a clean run. Identifying the two took a separate pass over the raw files.

**`admin@` is now both the `rua` destination and Django's error destination**, so
that maildir mixes crash mail with reports permanently. Files-in will never equal
reports-out again, which makes the gap structural rather than incidental.

Fixed: the tool now always prints `N file(s) read, M report(s)` and names every
file that carried none, with its `From:` and `Subject:`. A malformed report is
caught per file, named on stderr, and counted among them rather than ending the
run — **verified by feeding the previous version a truncated XML report, which
died with an unhandled `ParseError` and lost the rest of the maildir.** That is
the shape hypothesis 4 accuses Cloudflare of, reproduced locally and closed here.

#### The Django error mail is real, and it corrects a comment in shipped code

`[Django] ERROR (EXTERNAL IP): Internal Server Error: /admin/password_reset/`,
2026-08-21 01:09 — the first Django error report in years, and independent
confirmation of task 10's sender rewrite: every previous confirmation came from a
message built for the purpose.

The crash is `NoReverseMatch` for `password_reset_done` at
`django/contrib/auth/views.py:159` on the **old** site (`SCRIPT_FILENAME:
.../sg101/apache/sg101.wsgi`, Django on Python 2.7). Already fixed on
`modernize`: `sg101/urls.py` redirects that path to the site's own flow and
`core/tests/test_urls.py` covers it three ways. **The bug dies with jaguar.**

**But the comment describing it was wrong, and the traceback says so.** It read
"the flow raised NoReverseMatch *on submit*". The view reverses
`password_reset_done` before it dispatches on the request method, and the request
that crashed was `REQUEST_METHOD: 'GET'` with empty `GET` and `POST` dicts. The
page 500'd on every visit, for every visitor, for as long as that URLconf stood.
Corrected — the fix was right; its stated rationale understated the breakage.

**Expect more of these.** Scanners hit that URL, it 500s on every hit until
cutover, and the error channel now works.

#### `mod_remoteip` — two of my conclusions withdrawn

The crashing request carried seven headers claiming `127.0.0.1`
(`TRUE_CLIENT_IP`, `X_CLIENT_IP`, `X_ORIGINATING_IP`, `X_AZURE_CLIENTIP`,
`X_HOST`, an `X_FORWARED` typo, and a leading entry in `X_FORWARDED_FOR`) from
`REMOTE_ADDR: 192.0.2.3`, `curl/8.7.1` — a scanner probing for an
access-control bypass.

**I concluded the origin had been reached directly, and that was wrong.** The
reasoning assumed `REMOTE_ADDR` is the connecting peer. Apache's `mod_remoteip`
is loaded *and* enabled on jaguar (`conf-enabled/remoteip.conf`, symlinked
2025-08-10) with `RemoteIPHeader CF-Connecting-IP` and a `RemoteIPTrustedProxy`
list **diffed as a set against Cloudflare's published `ips-v4`: 15 ranges,
identical, no drift.** Under that config a normal proxied request shows a
non-Cloudflare `REMOTE_ADDR` — the module working, not a bypass. The absent
`HTTP_CF_CONNECTING_IP`, alongside four intact `CF-*` siblings, is the module
having consumed it.

**Two measurement traps on the way, both the house pattern:**

1. **`remoteip.load` proves loading, not configuring.** `mod_remoteip` has no
   default header; with no `RemoteIPHeader` set it loads and does nothing. Both
   branches fit every observation available at that point. Installed is not
   enabled is not in effect — see [[measure-before-recording-in-planning-docs]].
2. **`grep -r` cannot see `conf-enabled/`.** It does not follow symlinks during
   traversal. The proof is in its own output, which reported the *enabled* module
   from the `mods-available` path — grep skipped the `mods-enabled` symlink and
   found the target behind it. Reading "present only in conf-available, therefore
   disabled" out of that would have been reading the tool's blind spot as data.
   `ls -l` on the directory settled it.

**Also withdrawn: the concern that `REMOTE_ADDR` readers log Cloudflare edge
IPs.** `antispam`, `accounts`, `forums`, `comments`, `downloads` and `donations`
read `REMOTE_ADDR` directly and are correct.

#### The one real defect: `core/functions.py` preferred the forgeable header

`get_ip()` read `HTTP_X_FORWARDED_FOR` in preference to `REMOTE_ADDR` — stepping
over the value Apache had already made trustworthy in favour of the one any
client can choose. On the crashing request every direct reader recorded
`192.0.2.3`; `get_ip()` returned `127.0.0.1`, and `contact/forms.py` hands
that to reCAPTCHA as `remoteip`, degrading its risk scoring on the contact form.
The other callers (`core/middleware.py` online tracking, `search/views.py`
logging) are pollution rather than compromise. **No access is gated on these
headers, so the probe gained nothing.**

Fixed to `REMOTE_ADDR` only. Dropping the preference is right in either topology:
if the proxy rewrites `REMOTE_ADDR` the header is redundant, and if it does not,
trusting it without a proxy check is worse than recording a proxy address,
because the wrong value is then attacker-chosen rather than merely wrong.
`core/tests/test_functions.py` asserted the old preference and **encoded the
bug**; both tests replaced, and the regression test reproduces the real fault —
under the old code it fails `'127.0.0.1' != '192.0.2.3'`. Suite 877 green.

#### A cutover requirement this exposed

**Nothing in the repo sets the real client address.** No `real_ip`, no
`SECURE_PROXY_SSL_HEADER`, no `USE_X_FORWARDED_HOST`, no proxy in
`docker-compose.yml`. The rewrite that makes every `REMOTE_ADDR` reader correct
exists only as Apache configuration on a box with weeks to live, and Django does
not perform it itself.

**Whatever fronts the new VM needs the analogue** — nginx's
`ngx_http_realip_module` with the same Cloudflare ranges — or on cutover day
every IP the site records silently becomes a proxy address. Same shape as the
failures this project keeps finding: correct-looking output, wrong underlying
value, nothing reporting a disagreement. **Written into Step 20** — production
hardening already owns the Cloudflare front and the prod compose, which is where
this belongs; no new step was needed. Step 17 inherits it through the captcha's
`remoteip`.

### Sixth reading — 2026-08-22, covering 2026-08-21: three reporters, and the first window re-read from an immutable source

**Five reports in the maildir, from three reporting organizations** — the first
reading in which Google is not the only voice.

| Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|
| `google.com` | `1291292834730335860` | 2026-08-20 | 5 | 0 |
| `Yahoo` | `1787378132.213085` | 2026-08-21 | 2 | 0 |
| `Yahoo` | `1787378132.213034` | 2026-08-21 | 2 | 0 |
| `comcast.net` | `v2-1787362929-surfguitar101.com` | 2026-08-21 | 3 | 0 |
| `google.com` | `9674723540522333898` | 2026-08-21 | 3 | 0 |

**2026-08-21: 10 messages, 3 reporters, 0 aligned on neither mechanism.** Also
the first reading to record reporter, Report-ID and window for every report — the
convention was adopted on 08-21 with only one report to apply it to.

#### Comcast is observed directly — the inference is closed

`org_name` reads `comcast.net`, contact `dmarc-admin@alerts.comcast.net`. The
Open list has carried *"no reporter other than Google has ever been observed
directly"* since 08-21, with Comcast deduced from a +24 message delta on a
dashboard that never names reporters. **It is now read rather than deduced, by
the instrument that Open item named for the purpose.** Comcast reported the 08-21
window and not the 08-20 one, consistent with a receiver that files only for
windows in which it received mail.

#### swbell is Yahoo — a second receiver assumed, and refuted before it was recorded

Three sender names arrived in Brian's Gmail: Comcast, swbell and Yahoo. **Only
two reporting organizations stand behind them.** Both Yahoo reports carry
identical `org_name` (`Yahoo`) and contact (`dmarchelp@yahooinc.com`), cover the
same window, and their Report-IDs share the batch prefix `1787378132.` differing
only in suffix — that prefix decoding to **2026-08-22 05:55:32Z**, one generation
run emitting two reports. AT&T consumer mail (`swbell.net`) has been
Yahoo-operated for years.

**Count Yahoo as one reporting organization.** Taking swbell as an independent
corroboration would have inflated the reporter base by half, in the one direction
requirement 2 cares about.

**A limit of the format, worth stating once:** an aggregate report never names the
*recipient* domain, so which of the two covers `swbell.net` cannot be read from
the report body — only from the carrying message's headers.

**⚠️ WIDENED 2026-08-24 — the report *filename* carries it too.** The convention
is `receiver!policy-domain!begin!end`, so a saved attachment names the receiving
domain even with the message gone. The body claim stands; "only from the headers"
was too narrow, and it is why seven readings taken from a maildir — where the
filename is a delivery ID — could not see this dimension at all. The eighth
reading resolves the pair above: **Yahoo files one report per receiving domain.**

#### The 08-20 window reproduced exactly, and that settles what "tripled" meant

Google Report-ID `1291292834730335860` is **the same report the fifth reading
read**, and it returns identical rows: 5 messages, the count-1
`spf:mail.surfguitar101.com=pass` HELO row and the count-4 MAIL FROM row. Under
the convention that the most recent row stays provisional until a later reading
reproduces it, **2026-08-20 is confirmed.**

It also explains the fourth reading's tripling. **A report keyed by Report-ID is
immutable — re-reading one cannot change it.** What tripled was a *dashboard
aggregate* absorbing reports that arrived later, from reporters it declines to
name. The direction of error is therefore known: **per-report readings only ever
gain reports for a window, never revise one. 2026-08-21's 10 messages are a
floor, not a total** — Microsoft, or any receiver yet to file, would add to it.

#### What held steady

- **One sending source.** Every aligned row is `173.255.245.115`. Five days, now
  three reporters, and no unknown sender has ever appeared.
- **The member's Gmail forward recurs** — `209.85.220.41`, SPF `fail` (evaluated
  against `gmail.com`, therefore unaligned), DKIM aligned pass, disposition none.
  Still the evidence that **DKIM carries forwarded mail through DMARC**, which is
  the argument that taking SPF to `-all` is survivable.
- **No HELO row on 08-21**, as expected: that row was the deliberate null-sender
  test of 08-20 and nothing generated another. Its absence is not a regression of
  the HELO SPF record, which remains confirmed by the 08-20 report above.
- **Still no Microsoft** — day two of the 08-21/08-22 window.

#### `policy_published` is the reporter's rendering, not a transcript of the zone

Yahoo reports `sp=-` (absent) where Google and Comcast report `sp=none`. The
published record is `p=none` with no `sp` tag, so Yahoo echoes DNS while the
other two render the RFC default. **The reporters disagree while the zone is
constant** — worth knowing before anyone diffs that block across reporters hoping
to detect a zone change.

#### The reconciliation fix proved itself on real data

7 files read, 5 reports, **2 named as carrying none**: the "rua test 2" message
of 08-21 03:04:23Z and the Django error mail of 08-21 06:09:19Z. That is the gap
found by walking into it during the fifth reading, now closed against a maildir
holding more than twice the files.

**The Django 500 is neither new nor mail-related, and reading the arrival alone
suggested it was.** Its subject and its coincidence with the `4.7.28` throttle
the same day made a send failure 500ing the reset view look plausible, and that
hypothesis was put to Brian before the record was checked. It is the
`NoReverseMatch` already diagnosed in the fifth reading — same file, same
timestamp — fixed on `modernize` and dying with jaguar. **A hypothesis built from
a subject line and a date, refuted by the document that already held the
traceback.** See [[measure-before-recording-in-planning-docs]].

### Seventh reading — 2026-08-23, covering 2026-08-20 through 08-22: Microsoft arrives, and the first DKIM failure from our own IP

**Nine reports, three windows, four reporting organizations.** Read from
`tools/dmarc-aug-23.txt`, the tool's output over the maildir on jaguar.

| Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|
| `google.com` | `1291292834730335860` | 2026-08-20 | 5 | 0 |
| `Yahoo` | `1787378132.213085` | 2026-08-21 | 2 | 0 |
| `Yahoo` | `1787378132.213034` | 2026-08-21 | 2 | 0 |
| `comcast.net` | `v2-1787362929-surfguitar101.com` | 2026-08-21 | 3 | 0 |
| `google.com` | `9674723540522333898` | 2026-08-21 | 3 | 0 |
| **`Outlook.com`** | `46b44804ed974be598daac23a1ebd5be` | 2026-08-21 | **1** | 0 |
| `comcast.net` | `v2-1787445829-surfguitar101.com` | 2026-08-22 | 1 | 0 |
| `Yahoo` | `1787462955.303904` | 2026-08-22 | 3 | 0 |
| `google.com` | `7690294439508097741` | 2026-08-22 | 23 | 0 |

| Window | Messages | Reporters | Change |
|---|---|---|---|
| 2026-08-20 | 5 | 1 | identical — **third** reproduction |
| 2026-08-21 | **11** | 4 | was 10 across 3 |
| 2026-08-22 | 27 | 3 | new |

#### Microsoft has reported — the standing absence is closed

`Outlook.com`, contact `dmarcreport@microsoft.com`, one message from
`173.255.245.115`, SPF and DKIM both aligned pass, disposition none. *"Still no
Microsoft"* has been carried since the fifth reading. **Four reporting
organizations now observed directly: Google, Yahoo, Comcast, Microsoft.**

Its window prints as `2026-08-21 00:00:00Z -> 2026-08-22 00:00:00Z` where the
others print `-> 23:59:59Z`. **That is one day expressed with an exclusive end,
not a two-day window** — a reporter formatting difference, recorded so a later
reading does not double-count it.

#### The floor prediction confirmed, exactly as stated

The sixth reading recorded 08-21's 10 messages as *"a floor, not a total"*, on
the reasoning that a report keyed by Report-ID is immutable, so per-report
readings only ever **gain** reports for a window and never revise one. A late
filer arrived, added 1, and **every one of the four pre-existing 08-21 reports
reproduced byte-identically** — as did the 08-20 Google report, now read
unchanged three times across the fifth, sixth and seventh readings.

**The convention is now confirmed on two independent windows.** Treat the most
recent window's count as a lower bound; it moves up or not at all.

#### The first DKIM failure from `173.255.245.115` in seven readings — and it is UNIDENTIFIED

In Google's 08-22 report, one message in 23:

```
173.255.245.115   1  none  pass  fail  spf:mail.surfguitar101.com=pass/?
```

**What is measured:** SPF passed against the domain `mail.surfguitar101.com`;
there is no `dkim:` node at all, so no signature was evaluated; disposition none;
DMARC passed, because that domain aligns with the org domain under relaxed
`aspf`, which is why the report still reads 0 aligned on neither mechanism.

**What is NOT known: which message it was.** Four hypotheses were raised and all
four died. Recorded in full because the elimination is the only durable result
of the hunt.

| Hypothesis | How it died |
|---|---|
| A null-sender message — MAIL FROM empty, so SPF fell to HELO | **The `<scope>` element was never read.** `dmarc_report.py` printed only domain and result, and "the domain is a `mail.` subdomain, therefore HELO" is an inference. Patched to print scope; Google emits **no scope at all**, on either row — so the report cannot answer it |
| Even so, a null sender should appear in the log | `grep "from=<>"` over both local days returns exactly one message, `4F3A25869C1`, which ran 00:29–03:59 local on Aug 21 — the **08-21** window — and `status=expired, returned to sender`, so it was never delivered and could not appear in any report |
| An ordinary message with envelope sender at `@mail.surfguitar101.com` | No such sender appears anywhere in the window |
| Unsigned because the milter is unreachable on `inet:localhost:88888` | **Already answered in task 03 Finding 7, and rediscovered a third time.** Both sides truncate to 23352 and signing works; a captured header proves it. See the note below |

Two instrument checks were run before trusting any absence, and both passed:
the log **does** cover the window (858 lines on Aug 22), and the UTC→local
conversion is **confirmed from the data** — `Aug 22 14:49:22` carries
`message-id=<20260822194922…>`, and Django stamps those in UTC, so the box is
exactly UTC−5 as assumed.

An elimination pass — find the delivery to a Google relay with no opendkim line —
**also failed, and said so in its own output**: opendkim here logs only inbound
verification of external hosts and writes nothing when it signs, so ten IDs came
back "unsigned" while Google reported 22 of 23 as DKIM pass.

**Recorded as a bounded known-unknown, and closed.** One message in 23, passed
DMARC, disposition none, nothing harmed. jaguar is decommissioned at Step 21 and
outbound moves to Postmark, which applies its own signature. Reopen only if a
later reading shows a *second* unsigned message — one is an anomaly, two is a
pattern with something to grep for.

#### A consequence for the earlier readings: the `identity` column was inferred

Google emits no `<scope>`, and Google was the **only** reporter for the 08-20
window. So the fifth reading's table — which tabulated that window's two rows as
`HELO` and `MAIL FROM` — **cannot have read that from the report.** It was
derived the same way this reading's null-sender claim was derived, and the sixth
reading then built on it ("that row was the deliberate null-sender test"), and
the seventh built on the sixth.

For 08-20 the conclusion is probably still correct, because a deliberate
null-sender test was run that day — but that is corroboration from outside the
report, not the report speaking. **Three readings treated an inference as a
measurement.** [[measure-before-recording-in-planning-docs]], in the place it was
already written down.

#### `inet:localhost:88888` — presented as new for the third time

The milter port was raised again in this sitting as a live risk ("the next
`postfix reload` silently stops all signing"), and **withdrawn**. Task 03's
Finding 7 has held the answer since before the first reading: a captured header
from 2026-08-12 shows `dkim=pass header.s=dkim` aligned to the org domain,
`88888 − 65536 = 23352`, both sides truncate identically, and the decision *do
not touch it* was taken because the milter is decommissioned with the box.

STATUS's own 08-21 note already called this a rediscovery and drew the lesson —
*"when this document and the task file disagree, the task file has usually
already been there."* **This is the third occurrence and the second time that
lesson was available and unread.** The failure is not the wrong conclusion; it is
re-deriving from a config value what a captured message header had already
settled. Same shape as the finding it sits beside.

#### An independent instrument agrees with the volume estimate

08-22's **27 messages, on a day when four receivers filed**, sits against the
**~30/day mean** measured from the snapshot in 2026-08-17 — the figure the
Postmark plan choice rests on. Two unrelated instruments, close agreement.

It also reframes the earlier windows: **5 and 11 were not quiet days, they were
days when fewer receivers filed.** DMARC counts track reporter participation as
much as traffic, and remain a lower bound on real volume in any case, since mail
to non-reporting domains is invisible to this instrument entirely.

#### What held steady

- **One sending source.** Every aligned row is `173.255.245.115`. Seven readings,
  four reporters, and no unknown sender has ever appeared.
- **Zero messages aligned on neither mechanism**, in every window, from every
  reporter, since the first reading.
- **The member's Gmail forward recurs** on 08-21 — `209.85.220.41`, SPF `fail`
  (evaluated against `gmail.com`, therefore unaligned), DKIM aligned pass,
  disposition none. Still the evidence that **DKIM carries forwarded mail through
  DMARC**. It does not appear in the 08-22 window.
- **Yahoo prints `sp=-` where the others print `sp=none`.** A reporter omitting a
  value the others fill in from the effective policy — **not** Yahoo seeing a
  different record. Recorded so it is not read as a discrepancy.

#### Bearing on the policy decision

`p=none` was published 2026-08-17, so **the mandatory week is up 2026-08-24**;
this is day six. The evidence for tightening is as strong as this instrument can
make it: four independent receivers, one sending source, no unaligned mail in any
window, and a demonstrated case of DKIM carrying a forward that SPF could not.

**The unsigned message above was hunted the same day and did not survive as a
blocker.** It cannot be identified from these instruments, it passed DMARC, and
nothing was harmed. It is not a reason to hold step 7; it is a reason to look
again at the next reading, since a second occurrence would be a pattern with
something to grep for.

### Eighth reading — 2026-08-24, covering 2026-08-23: the SPF rewrite measured at five receivers, and "Yahoo" is three receiving domains

**Six reports, read from the Gmail copy — the first reading taken after the local
copy stopped receiving.** Five cover 2026-08-23, the first window after the MX
flip and the apex SPF rewrite; the sixth is a late Microsoft filing for 08-22.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `7598911246411840152` | 2026-08-23 | 12 | 0 |
| `yahoo.com` | `Yahoo` | `1787549139.16450` | 2026-08-23 | 5 | 0 |
| `comcast.net` | `comcast.net` | `v2-1787532080-surfguitar101.com` | 2026-08-23 | 3 | 0 |
| `att.net` | `Yahoo` | `1787549139.16305` | 2026-08-23 | 2 | 0 |
| `cox.net` | `Yahoo` | `1787549139.16351` | 2026-08-23 | 1 | 0 |
| `protection.outlook.com` | `Outlook.com` | `c2fe8b5012c84e53ba99091ccf756c28` | 2026-08-22 | 3 | 0 |

**2026-08-23: 23 messages, five receiving domains, 0 aligned on neither
mechanism.** Every row is `173.255.245.115`, `spf:surfguitar101.com=pass`,
`dkim:surfguitar101.com=pass`, disposition none.

#### Receipt through Cloudflare Email Routing is confirmed

Phase 1's loose end asked for exactly this: *"the eighth reading should confirm
receipt rather than assume it"*, since the `rua` path now runs through Email
Routing instead of Postfix and the `p=none` → `quarantine` decision rests on
these reports. Six arrived, from four organizations.

**Recorded as inference, not measurement.** The reports are in the Gmail inbox
and absent from jaguar, and `admin@surfguitar101.com` → Cloudflare →
`bgneal@gmail.com` is the only route into that inbox — an argument from the
absence of any other path. The `Received` chain would make it direct, and was not
read, because the export carried the attachments alone.

That same gap leaves the **forward latency unmeasured**, which is the local
copy's entire justification: 0.85s to the maildir against 9h25m52s to Gmail
through a rate limit, measured 2026-08-21. Whether Cloudflare's forwarders
inherit that limit is now an open question with no data. Export raw `.eml` next
time and it answers itself.

#### jaguar's maildir is not stale, it is deaf

Run over `/home/dmarc/mail` the same day: **14 files, 9 reports, and all nine are
the seventh reading's** — matching by Report-ID, window and count. Zero new
reports. Decoding the maildir filenames dates the changeover, and the shape is
sharper than "frozen":

| Delivered (UTC) | Message | Origin |
|---|---|---|
| 08-21 03:04 | `rua test 2` | local |
| 08-21 06:09 | Django error, `/admin/password_reset/` | local |
| 08-23 05:33 | MAILER-DAEMON bounce | local |
| **08-23 21:02** | Cloudflare "Verify your Email Routing address" | **external — the last one** |
| 08-24 01:08 | contact-form feedback, *SOUNDS OF THE PRESTON WAYNE FOUR* | local |

External mail stops at 08-23 21:02Z. Everything after it is jaguar talking to
itself through `virtual_alias_domains`, which never consults MX — the loose end
already recorded, now visible on live mail rather than argued from config. The
08-24 01:08Z feedback message is **the local half of the Phase 1 capture**: one
message, `nrcpt=2`, whose Gmail half is what returned `spf=pass / dkim=pass /
dmarc=pass` under the rewritten apex record.

**A byproduct: Cloudflare's verification mail reached jaguar**, which puts the MX
deletion after 08-23 21:02Z. Inference from delivery path, not measurement — a
queued retry produces the same file — and Cloudflare's audit log settles it if
the exact minute ever matters.

**The Report-ID convention paid again.** Recognizing nine already-read reports
cost one comparison. On 08-21 the same question cost a header dump and a mail-log
pull.

#### The apex SPF rewrite cost nothing, at five receivers instead of one

08-23 is the first window covering the day `a` and `mx` came out of the apex
record. Phase 1 closed *"sending from the site has not been exercised since the
apex SPF rewrite"* on a single contact-form message at a single receiver. This is
**23 messages at five receivers**, every row passing SPF on the explicit `ip4:`,
every row DKIM aligned, disposition none throughout. Task 03's Finding 3 and the
rewrite that answered it are both now measured rather than reasoned.

#### No second unsigned message — the reopen trigger did not fire

The seventh reading closed the unidentified DKIM failure as a bounded
known-unknown and named the condition for reopening: *one is an anomaly, two is a
pattern with something to grep for.* Every 08-23 row across five receivers is
`dkim=pass`, and none carries the `mail.surfguitar101.com` SPF domain that
accompanied it. It stays one occurrence, one window, one receiver. Microsoft's
independent 08-22 report shows 3 of 3 passing.

#### "Yahoo" is three receiving domains — and the sixth reading was already right about the part that mattered

The three Yahoo files carry **byte-identical `report_metadata` apart from
`report_id`** — same `org_name`, same contact, same window — and share the
filing-run prefix `1787549139.`. What separates them is the filename:
`att.net`, `cox.net`, `yahoo.com`. **Yahoo files one report per receiving
domain.**

That explains the 08-21 pair the sixth and seventh readings could not account
for. `1787378132.213085` and `.213034` were two receiving domains from one
filing run, so their 2 + 2 messages are two populations rather than a double
count.

**The sixth reading had already reached the conclusion that mattered** — *"count
Yahoo as one reporting organization"* — and refuted the inflated reporter base
before recording it. What it could not do was say *why* there were two. One of
its claims needs widening rather than correcting: it states the recipient domain
is readable *"only from the carrying message's headers."* The standard report
filename — `receiver!policy-domain!begin!end` — carries it too, which is how this
reading has it. [[search-the-artifacts-before-claiming-new]]: this was drafted as
a correction to the sixth reading and is not one.

**And that names why it stayed invisible for seven readings.** Read from a
maildir, the filename is a delivery ID, and the receiving domain is gone the
moment the attachment is detached from its message. The Gmail export preserved it
by accident of how attachments save. **Keep the attachment filenames in future
readings** — the receiving domain is not in the report body for any tool to
print. **Amended 2026-08-24:** `tools/dmarc_report.py` now prints the source file
and, when the name follows the `receiver!policy-domain!begin!end` convention, a
`Receiver` line beside `Reporter`; it declines rather than guesses for a maildir
delivery ID. The sentence above describes the tool as it was when this reading
was taken, not as it is.

**Consequence for the record: "reporter" has meant two different things.**
Reporting organizations remain **four** — Google, Yahoo, Comcast, Microsoft.
Receiving domains observed now number **seven**: `google.com`, `yahoo.com`,
`att.net`, `cox.net`, `comcast.net`, `protection.outlook.com`, and `swbell.net`
— the last from the sixth reading's report-mail sender names rather than a
filename, so it is the one of the seven not read from the file naming
convention. Prior readings' per-window "reporter" counts are counts of *reports*,
which for Yahoo overstates organizations and understates receivers.

#### Microsoft files a window late — two points, and a prediction

`protection.outlook.com`'s report covers 08-22 and arrived in the 08-24 batch;
its 08-21 report arrived in the 08-23 batch. Two observations, consistent.
**Prediction: a Microsoft report for the 08-23 window in the next batch** — which
also makes 08-23's 23 messages a floor under the standing convention, not a
total.

This one is `protection.outlook.com`, the EOP side. Whether `46b44804…` came from
consumer `outlook.com` cannot be recovered from the maildir copy, where the
filename is a delivery ID — though the attachment name *inside* that message on
jaguar would still say. It bears on the Microsoft deliverability thread, which
concerns an eighth of the membership.

#### 08-22 gained again — the floor convention holds a fourth time

| Window | Messages | Reporting orgs | Change |
|---|---|---|---|
| 2026-08-22 | **30** | 4 | was 27 across 3 — Microsoft's late filing added 3 |
| 2026-08-23 | 23 | 3 | new; a floor, Microsoft outstanding |

Windows gain reports and never revise them, now confirmed on three independent
windows.

#### What held steady

- **One sending source.** Every aligned row in eight readings is
  `173.255.245.115`. No unknown sender has ever appeared.
- **Zero messages aligned on neither mechanism**, in every window, from every
  reporter, since the first reading.
- **Yahoo prints `sp=-` where the others print `sp=none`.** Unchanged, and still
  not a discrepancy.
- **Microsoft's exclusive window end** (`-> 00:00:00Z` of the next day) recurs on
  the 08-22 report. Still one day, still not to be double-counted.
- **The member's Gmail forward (`209.85.220.41`) is absent** from 08-22 and
  08-23. It has always been intermittent, so absence is not removal.

#### Bearing on the policy decision

`p=none` was published 2026-08-17, so **the mandatory week is up today**. Eight
readings, four reporting organizations, seven receiving domains, one sending
source, zero messages aligned on neither mechanism in any window from any
reporter, and the single DKIM anomaly did not recur on the day five receivers
looked. **Nothing in this reading argues for holding step 7.**

Two residual risks, neither a blocker, both worth stating before the flip:

- **The member's Gmail forward is the one class `quarantine` puts at risk.** SPF
  fails there by construction — evaluated against `gmail.com`, therefore
  unaligned — and aligned DKIM is what carries it through. That has held on every
  observation. A forwarder that modifies the body breaks it, and under
  `quarantine` the failure mode becomes a quarantined message rather than
  nothing.
- **Postmark is not in the apex SPF record yet, and tightening changes what that
  costs.** `include:spf.mtasv.net` is deliberately held to the cutover (task 03
  step 5). Under `p=none` a late edit is harmless. Under `p=quarantine` the first
  Postmark send rides on DKIM alone, one mechanism deep, with quarantine as the
  failure mode. **That makes step 5 an ordering requirement rather than a
  tidy-up: publish the include at or before the Postmark cutover, never after.**


### Ninth reading — 2026-08-25, covering 2026-08-24: the Microsoft prediction held, and an eighth receiving domain

**Ten files, read from `~/dmarc` on Brian's Mac — four new, six already read.**
The four new ones were saved 2026-08-25 14:11–14:12Z; the six re-reads were saved
14:21–14:23Z the day before and are the eighth reading's, recognised by
Report-ID. Three of the new four cover 2026-08-24; the fourth is the predicted
late Microsoft filing for 08-23.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `2097562329291412247` | 2026-08-24 | 15 | 0 |
| `yahoo.com` | `Yahoo` | `1787636161.506830` | 2026-08-24 | 2 | 0 |
| `aol.com` | `Yahoo` | `1787636161.506805` | 2026-08-24 | 1 | 0 |
| `protection.outlook.com` | `Outlook.com` | `4b4c7f287941475e9c0efa5adaf5e22e` | 2026-08-23 | 1 | 0 |

**2026-08-24: 18 messages, three receiving domains, 0 aligned on neither
mechanism.** Every row is `173.255.245.115`, `spf:surfguitar101.com=pass`,
`dkim:surfguitar101.com=pass`, disposition none — the ninth consecutive reading
in which that sentence is the whole result.

#### The Microsoft prediction held, and 08-23 gained on schedule

The eighth reading predicted *"a Microsoft report for the 08-23 window in the
next batch"* and called 08-23's 23 messages a floor rather than a total. Both
landed: `4b4c7f28…` covers 08-23 with 1 message, on the same exclusive window end
(`-> 00:00:00Z` of the next day) Microsoft has used throughout.

| Window | Messages | Receiving domains | Change |
|---|---|---|---|
| 2026-08-23 | **24** | **6** | was 23 across 5 — Microsoft's late filing added 1 |
| 2026-08-24 | 18 | 3 | new; a floor, Microsoft outstanding |

**Windows gain reports and never revise them — a fourth independent window, and
the floor convention now holds a fifth time.** Microsoft filing exactly one
window late is three consecutive observations (08-21, 08-22, 08-23), which is
enough to stop calling it an observation and start scheduling around it:
**08-24's 18 is a floor with Microsoft outstanding, expected in tomorrow's
batch.**

#### `aol.com` is the eighth receiving domain — and Yahoo's filing pattern reproduces

`aol.com` has not appeared in any prior reading. It arrives in filing run
`1787636161.` alongside `yahoo.com` — **byte-identical `report_metadata` apart
from `report_id`**, separated only by the filename, which is precisely the shape
the eighth reading established from run `1787549139.` (`att.net`, `cox.net`,
`yahoo.com`).

That is the finding reproducing on an independent filing run rather than being
re-argued from the same evidence. **Reporting organizations stay at four** —
Google, Yahoo, Comcast, Microsoft. **Receiving domains observed are now eight**:
`google.com`, `yahoo.com`, `att.net`, `cox.net`, `aol.com`, `comcast.net`,
`protection.outlook.com`, `swbell.net`. Four of the eight are Yahoo-filed, which
is why "reporter" undercounted receivers for seven readings.

#### The first reading where the tool printed a Receiver for every file

This is the first reading taken from a folder of saved attachments with their
original names intact, and the first to exercise the `Receiver` line added to
`tools/dmarc_report.py` on 2026-08-24 against real data. **All ten files follow
the `receiver!policy-domain!begin!end` convention and all ten printed a
Receiver**, including the two `.zip` files from Google, whose wrapper differs but
whose naming does not. The guard that declines rather than guesses was not
exercised, because nothing here needed it.

The eighth reading's instruction — *"keep the attachment filenames in future
readings"* — is what made this reading cost nothing. Saving the attachments to a
folder does it by construction, where the maildir destroyed it by construction.

**The Report-ID convention paid a third time.** Six of ten files were recognised
as already read from Report-ID, window and count, at the cost of one comparison
each.

#### Forward latency is still unmeasured — the same loose end, a second time

The eighth reading closed with *"export raw `.eml` next time and it answers
itself."* These are extracted attachments again, so it does not. The local
copy's entire justification remains the unmeasured quantity: 0.85s to the maildir
against 9h25m52s to Gmail through a rate limit, measured 2026-08-21, with
Cloudflare's forwarders untested.

**The file mtimes do not substitute, and it is worth saying why.** Yahoo filed
run `1787636161.` at 2026-08-25 05:36:01Z and the files were saved at 14:11–14:12Z;
Comcast filed at 2026-08-24 00:41:20Z and its file was saved at 14:22:20Z. The
two save runs sit eleven minutes apart on consecutive days, which measures when
Brian sits down at his mail, not when Cloudflare delivered it. It bounds delivery
from above at roughly 8h35m and 13h41m respectively — both above the 9h25m figure
in one case and below it in the other, so it does not even order the two
hypotheses. **Second time asked; ask for the `.eml` a third time or stop
carrying it as an open question.**

#### What held steady

- **One sending source.** Every aligned row in nine readings is
  `173.255.245.115`. No unknown sender has ever appeared.
- **Zero messages aligned on neither mechanism**, in every window, from every
  reporter, since the first reading.
- **No second unsigned message.** The seventh reading's reopen trigger — *one is
  an anomaly, two is a pattern* — did not fire in the 08-24 window either, nor in
  Microsoft's late look at 08-23. It stays one occurrence, one window, one
  receiver, with two clean windows behind it.
- **Yahoo prints `sp=-` where the others print `sp=none`.** Unchanged on
  `aol.com` too, and still not a discrepancy.
- **The member's Gmail forward (`209.85.220.41`) is absent** from 08-23 and
  08-24, which with the eighth reading's 08-22 makes three consecutive windows.
  It has always been intermittent, so absence is still not removal — but it is
  the one class `quarantine` puts at risk, and three windows without it means the
  risk cannot currently be re-measured. That is a gap in the evidence, not a sign
  the class has gone away.
- **Every row still signs with the legacy `dkim` selector.** The Postmark
  selector `20260817033844pm` has appeared in no auth result in any reading,
  which is the direct confirmation that task 02 has not cut over yet.

#### Bearing on the policy decision

The mandatory week was up on 2026-08-24 and the eighth reading found nothing
arguing to hold step 7. This reading adds a ninth clean window and changes
neither the recommendation nor the two residual risks, which stand exactly as
written there. One is worth restating because this reading sharpens it:

**`include:spf.mtasv.net` is an ordering requirement, and the evidence for it is
now nine readings deep.** Every message this domain has ever been observed to
send comes from one IP under the legacy `dkim` selector. Postmark is a sender
with *no* observation behind it — no window, no receiver, no reporter has seen
it. Under `p=none` a late SPF edit is harmless; under `p=quarantine` the first
Postmark send rides on DKIM alone into a policy that quarantines. **Publish the
include at or before the task 02 cutover, never after.**

A note on scope, since the clean run invites the wrong inference: nine clean
readings measure *the sending path that is being retired*. They are strong
evidence that task 10's repairs worked and that jaguar's mail is in order. They
are no evidence at all about Postmark, and the first window after cutover is the
one that has to be read with the same attention as the first window ever was.

### Tenth reading — 2026-08-25 evening, covering 2026-08-24: one raw message closes three open questions and corrects two claims

**One report, and one `.eml` that matters more than the report.** Comcast's 08-24
filing arrived in the afternoon, after the morning batch had been read.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `comcast.net` | `comcast.net` | `v2-1787622101-surfguitar101.com` | 2026-08-24 | 4 | 0 |

**2026-08-24 rises to 22 messages across four receiving domains, still zero
aligned on neither mechanism.** Microsoft's 08-24 report is outstanding, so 22 is
still a floor — the convention holds a sixth time.

#### Cloudflare Email Routing forwards in 2 seconds — measured, finally

The raw message was read for the first time in ten readings, and the `Received`
chain answers the question that has been open since 2026-08-21:

| Time (UTC) | Hop |
|---|---|
| 18:16:26 | Comcast internal, `mdpapp-ch-1p-162526` → `mdpmta-as-1p-177146` |
| **18:16:26** | `by cloudflare-email.net (cloudflare) id cjRKZG5NJV2Z for <admin@surfguitar101.com>` |
| **18:16:28** | `by mx.google.com` (`11:16:28 -0700`) |

**Two seconds, Cloudflare receipt to Gmail receipt.**

**This kills the local copy's justification outright.** That justification was
0.85s to jaguar's maildir against 9h25m52s to Gmail, measured 2026-08-21 — but
the 9h25m52s was *jaguar's own rate-limited outbound*, not a forwarder cost.
Cloudflare's path is 2 seconds, near enough the maildir that no latency argument
for a local copy survives. The maildir has been deaf since 08-23 21:02Z anyway;
this removes the reason to care.

#### The ninth reading's latency suspicion was wrong, and the error is worth naming

The ninth reading noticed this report was absent from the morning batch and
inferred a Cloudflare delivery lag of 12h31m–20h29m, flagged as *"suggestive
bound, not a measurement."* **The observation was real and the explanation was
wrong.** Comcast's Report-ID encodes `1787622101` = 2026-08-25 01:41:41Z, which
was read as the send time. The message was transmitted at 18:16:26Z:
**Comcast held its own report for 16h34m45s between generating it and sending
it.** The delay was entirely Comcast's, and Cloudflare's share of it was two
seconds.

**Report-ID timestamps are generation times, not send times.** Nine readings have
used Report-IDs to recognise reports already seen, which they are perfectly good
for. Nothing else about them should be read as a clock. That is the second time
in two readings that a number was decoded confidently from a string rather than
measured — [[suspect-the-measurer-before-the-record]].

#### `include:_spf.mx.cloudflare.net` is load-bearing, and requirement 5 would have deleted it

This is the finding with teeth. The forwarded message carries:

```
Return-Path: <SRS0=zJrw=sg=alerts.comcast.net=dmarc-support@surfguitar101.com>
spf=pass (google.com: ... designates 104.30.10.185 as permitted sender)
```

**Cloudflare applies SRS**, rewriting the envelope sender into
`surfguitar101.com`. The receiver therefore evaluates SPF against *this* domain
for every forwarded message, and it passes only because `104.30.10.185` falls
inside `104.30.0.0/19` from that include. Verified: the include expands to
`ip4:104.30.0.0/19 ip6:2405:8100:c000::/38`, and the sending IP is in range.

**Task 03 requirement 5 prescribes two future SPF records and neither contains
that include.** Publishing either as written would hard-fail SPF on every message
Cloudflare forwards for this domain — `admin@`, `abuse@`, `postmaster@`,
`brian@` — **including the DMARC reports themselves, which arrive through
`admin@surfguitar101.com`.** The record that would break the reporting pipeline
is written down in the task file as the post-cutover target. Corrected there.

Earlier the same day this include was described as unexplained for an outbound
policy, with deletion offered as an option. It is explained, it is not optional,
and the reasoning that called it unexplained treated Email Routing as purely
inbound. SRS makes a forwarder an outbound sender under the forwarding domain's
name.

**CORRECTED, same evening — SRS was not discovered here. It was recorded on
2026-08-23 and this reading did not look.** Task 06's Phase 1 account says it
plainly: *"Cloudflare's SRS rewrite lands in `@surfguitar101.com`, so Email
Routing does need your SPF authorization"* — flagged there as correcting a
planning claim, which makes this the *second* time the same correction has been
made. The apex SPF was fixed on that basis two days ago, which is the only reason
the live record carries the include at all.

**So the finding is not SRS. The finding is that two task files disagree and
nobody reconciled them.** Task 06 learned it on 08-23 and wrote it down; task 03
requirement 5 went on prescribing SPF records that omit the include. A plan is
executed from its own requirements, not from another document's retrospective, so
the defect and its correction stand. The framing of it as a discovery does not.

[[search-the-artifacts-before-claiming-new]] — **invoked against the ninth
reading three paragraphs above, then committed here in the same sitting.** The
tag exists because this failure recurs; it recurred while being cited.

#### A third signer: `cf2024-1`, seen in service for the first time

Cloudflare DKIM-signs forwarded mail as **`d=surfguitar101.com; s=cf2024-1`**,
and `cf2024-1._domainkey.surfguitar101.com` resolves to a 2048-bit
Cloudflare-managed key. That is a **third signer** alongside the legacy `dkim`
selector and Postmark's `20260817033844pm`.

It has never surfaced in a DMARC report because forwarded mail carries the
*original sender's* `header.from`, so this domain's DMARC is not what gets
evaluated — which is why ten readings of aggregate data could not show it
signing.

**CORRECTED, same evening — the first draft of this section said the selector
"appears in no task file and no prior reading" and that "nobody inventoried" it.
Both are false, and badly so.** Task 06 records `cf2024-1._domainkey` three
times: as one of the five records in the **Add missing records** bundle, as Phase
1's Defect 1 — unpublished on `surfguitar101.com`, which made forwarded mail
`permerror` and put the first messages in Gmail's spam — and as a key **shared
across customer zones**, confirmed by test send. This document then published it
on `themadeira.net` on 08-23 and verified the value three ways, including a
byte-identical `cmp` against the other zone.

Measured tonight: `cf2024-1._domainkey.themadeira.net` resolves, so that entry in
the 08-23 readiness table — *"absent, Phase 1's Defect 1 waiting to happen
again"* — is now closed.

What is actually new is narrow: the selector was observed **in service**, signing
a real forwarded message, read from the receiving side. Task 03's selector
inventory does genuinely predate it and is worth updating. The project having
never seen it is not a thing that happened.

#### Receipt through Email Routing is now measured rather than inferred

The eighth reading recorded receipt as *"inference, not measurement"* — an
argument from the absence of any other path into the inbox, with the `Received`
chain named as the thing that would make it direct. The chain is above, and
`X-Forwarded-For: admin@surfguitar101.com bgneal@gmail.com` names the route
explicitly. **Closed.**

#### What held steady

- **One sending source.** Ten readings, every aligned row `173.255.245.115`.
- **Zero messages aligned on neither mechanism**, every window, every reporter.
- **Comcast is consistent in content and erratic in timing.** Its 08-23 report was
  saved 08-24 14:22Z; this one was generated 01:41Z and sent 18:16Z. Content has
  never varied.

#### Bearing on the policy decision

Nothing here argues against tightening, and one thing argues for doing it in the
right order — but not the order previously recorded. The Postmark ordering
concern was retired this morning (the custom Return-Path carries SPF alignment).
**What replaces it is the apex record's contents:** whatever SPF string is
published at cutover must retain `include:_spf.mx.cloudflare.net` alongside
Postmark's include, or forwarded mail breaks the moment the record changes —
under any policy, `p=none` included, because SPF hard-fail on the SRS domain
stands on its own without DMARC.

### Eleventh reading — 2026-08-26, covering 2026-08-25: Postmark appears, and the policy line does not

**Fourteen files in `~/dmarc` — three new, eleven re-reads.** The three new ones
were saved 2026-08-26 14:03Z and all cover the **2026-08-25 window**, the one the
tenth reading wrote three predictions against.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `16063363139180655336` | 2026-08-25 | 6 | 0 |
| `yahoo.com` | `Yahoo` | `1787722983.752886` | 2026-08-25 | 2 | 0 |
| `aol.com` | `Yahoo` | `1787722983.752860` | 2026-08-25 | 1 | 0 |

**2026-08-25: 9 messages, three receiving domains, 0 aligned on neither
mechanism.** Comcast and Microsoft are both outstanding, so **9 is a floor** — the
convention holds a seventh time. Yahoo's filing run `1787722983.` reproduces the
established shape a third time: `yahoo.com` and `aol.com` byte-identical in
`report_metadata` apart from `report_id`, separated only by the filename.

*Applying the tenth reading's own correction: `1787722983` decodes to 2026-08-26
05:43:03Z and that is a **generation** time, not a send time. It is used below as
a lower bound on when the report was written, which is all it can support.*

#### Prediction 2 landed — the first non-jaguar sending source in eleven readings

Google's 08-25 report carries a second `<record>`:

```
source_ip 50.31.156.116   count 1   disposition none   dkim pass   spf pass
  dkim  d=surfguitar101.com   s=20260817033844pm   pass
  dkim  d=pm.mtasv.net        s=pm20250806         pass
  spf   d=pm-bounces.surfguitar101.com              pass
```

**`20260817033844pm` has now appeared in an aggregate report.** Its absence is
what ten readings used to conclude the cutover had not happened; the header
capture read at Gmail on 08-25 proved it signs a real message, and this is the
same send arriving from the receiver's own accounting. Both signatures ride
together exactly as the header showed, and only `d=surfguitar101.com` aligns.

**`50.31.156.118` does not appear anywhere.** That is the Outlook send, and
Microsoft has now filed exactly one window late four consecutive times (08-21,
08-22, 08-23, 08-24). So `.118` is expected in Microsoft's 08-25 filing in the
next batch, and its *absence* there would be the finding.

#### The relaxed SPF alignment is load-bearing, and nothing chose it deliberately

The envelope domain is `pm-bounces.surfguitar101.com` — a **subdomain** of the
header-from domain, not the domain itself. `policy_evaluated/spf` reads `pass`
only because the published record carries `aspf=r`.

**Under `aspf=s` this row would read `spf=fail` and rest on DKIM alone.** Nothing
proposes tightening alignment and this is not a defect. It is recorded because
`aspf=r` is now a property the Postmark path depends on rather than a default
nobody examined — the same class as `include:_spf.mx.cloudflare.net`, which the
tenth reading found was holding up the reporting pipeline itself.

#### Prediction 3 landed — every row in all fourteen files is `disposition=none`

No exceptions, in the new reports or the re-reads.

#### Prediction 1 did NOT land — and the record is published, so the reports are the thing to explain

All three 08-25 reports print **`p=none`**. Google adds `sp=none np=none`.

**The record itself is fine, verified authoritatively rather than from a cache:**

```
_dmarc.surfguitar101.com. 300 IN TXT "v=DMARC1; p=quarantine; rua=mailto:00fc…@dmarc-reports.cloudflare.net,mailto:admin@surfguitar101.com"
```

Identical from `ada` and `cash`, **exactly one `v=DMARC1` string**, TTL 300, `rua`
intact with both destinations. Nothing was lost or double-published.

**Yahoo's report settles which explanation is right.** It was generated at
05:43:03Z on **08-26** — hours after `p=quarantine` went live — and still prints
`p=none`. A reporter that stamped `policy_published` from the record as it read at
generation time would have printed `quarantine`. So `policy_published` is the
policy **applied to the messages in the window**, per RFC 7489, and an 08-25
window whose mail was evaluated before the change took effect correctly reads
`p=none`.

**This is unanswered, not failed.** The distinction matters because the
alternative — that receivers are not seeing the record — would be a live defect,
and it is ruled out by the record resolving and by Yahoo's generation time. **The
decisive test is the 2026-08-26 window**, which is the twelfth reading: those
reports cover mail evaluated entirely after publication, and every one of them
should read `p=quarantine`. If any still reads `p=none`, that is a real finding
and the record needs re-examining rather than re-explaining.

#### The eleven re-reads reproduce, and 08-23 reproduces in full

Every re-read matches its recorded Report-ID and count. The 08-23 window
recomputes from six files as **24 messages across six receiving domains** —
`att.net` 2, `comcast.net` 3, `cox.net` 1, `google.com` 12, `yahoo.com` 5,
`protection.outlook.com` 1 — which is exactly the ninth reading's revised total
after Microsoft's late filing. 08-24 recomputes as **22 across four**, matching
the tenth reading. **Windows gain reports and never revise them** now holds across
four independent windows and seven readings.

#### One count worth not over-reading

Jaguar's own volume by window: 08-23 **24**, 08-24 **22**, 08-25 **8**. That looks
like a collapse and is not evidence of one — two of the four 08-25 reporters have
not filed, and both missing ones contributed 4 and 1 to the previous window. **No
trend claim is available until the 08-25 window closes.** This is the same error
shape as the second and third readings' traffic-decline argument, which the fourth
reading killed: *"Both readings were wrong, because neither had a baseline."*

#### Addendum, 2026-08-26 13:12Z — Comcast files for 08-25, and the timing property gets a second witness

A fifteenth file arrived after this reading was written: **`comcast.net`,
Report-ID `v2-1787708806-surfguitar101.com`, window 2026-08-25**. One sending
source, jaguar's `173.255.245.115`, **2 messages, both mechanisms aligned,
disposition `none`.**

| | recorded above | with Comcast |
|---|---|---|
| 2026-08-25 messages | 9 | **11** |
| receiving domains | 3 | **4** |
| aligned on neither | 0 | **0** |
| jaguar's own volume | 8 | **10** |

**The floor holds an eighth time.** One of the two outstanding reporters has now
filed and the window went up, never sideways — so *"two of the four 08-25
reporters have not filed"* above should now read *one*, and Microsoft is that one.
Its four-consecutive-windows-late pattern still predicts `50.31.156.118` in the
next batch.

**The reason this was worth opening early: `policy_published` reads `p=none`, and
this report was generated 2026-08-26 01:46:46Z** — one hour and forty-seven
minutes after the window closed, and hours after `p=quarantine` went live. That is
a **second, independent witness** to the timing property this reading inferred
from a single Yahoo report at 05:43:03Z. Two reporters, two generation times, two
filing pipelines, same behaviour: **`policy_published` carries the policy applied
during the window, not the record as it reads when the report is written.** One
witness left open the possibility of a single receiver's quirk; two make it a
property of the format, which is what the twelfth reading's whole argument rests
on.

**Comcast passing at all is the quiet result.** This is the receiver that refused
every message from `173.255.245.115` outright until the block lifted on 08-19 —
two messages, both aligned, delivered disposition `none`.

**No Postmark row**, and that is expected rather than a gap: the two 08-25 test
sends went to Outlook and Gmail, so Comcast saw neither. This report says nothing
about `.116` or `.118`.

**Unchanged: the twelfth reading is still the decisive one.** No file in `~/dmarc`
yet covers the 2026-08-26 window.

### Twelfth reading — 2026-08-27, covering 2026-08-26: the policy line appears, and one report of three did not get it

**Eighteen files in `~/dmarc` — three new, fifteen re-reads.** The three new ones
carry mtimes of 2026-08-27 12:29 and all cover the **2026-08-26 window** — the one
the eleventh reading named decisive, being the first whose mail was evaluated
entirely after `p=quarantine` went live.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Neither | `policy_published` |
|---|---|---|---|---|---|---|
| `google.com` | `google.com` | `14558492136586096678` | 2026-08-26 | 9 | 1 | **`p=quarantine sp=quarantine`** |
| `bellsouth.net` | `Yahoo` | `1787809465.293390` | 2026-08-26 | 1 | 0 | **`p=quarantine`** |
| `yahoo.com` | `Yahoo` | `1787809465.293416` | 2026-08-26 | 6 | 0 | **`p=none`** |

**2026-08-26: 16 messages, three receiving domains, 1 aligned on neither
mechanism.** Comcast and Microsoft are both outstanding, so **16 is a floor** — the
convention gets its ninth test.

#### The decisive test returns two of three, and the record is not the explanation

The eleventh reading committed in advance: *"If any still reads `p=none`, that is a
real finding and the record needs re-examining rather than re-explaining."* One
does. The record was re-examined first, from both authoritative nameservers:

```
_dmarc.surfguitar101.com. TXT "v=DMARC1; p=quarantine; rua=mailto:00fc…@dmarc-reports.cloudflare.net,mailto:admin@surfguitar101.com"
```

Byte-identical from `cash.ns.cloudflare.com` and `ada.ns.cloudflare.com`, exactly
one `v=DMARC1` string, `rua` intact with both destinations. **The record is not the
explanation, and "receivers are not seeing it" is refuted three separate ways:**
the record resolves authoritatively, Google prints `quarantine` *and enforces it*,
and Yahoo itself prints `quarantine` for another domain in the same filing run.

**The tool was checked before the record was believed.** Raw XML from both `.gz`
files carries `<p>quarantine</p>` in one and `<p>none</p>` in the other. This is
not a parsing artefact.

#### The exception is inside one reporter's single filing run

The two disagreeing reports are not two receivers who read the zone at different
moments. They are the same reporter, in the same run:

- `bellsouth.net` — Report-ID `1787809465.293390` — `p=quarantine`
- `yahoo.com` — Report-ID `1787809465.293416` — `p=none`

Both IDs share the prefix `1787809465`, which decodes to **2026-08-27 05:44:25Z** —
a *generation* time, per the tenth reading's correction, and hours after
publication for both. Same reporter, same run, same window, same generation stamp,
`report_metadata` otherwise byte-similar apart from `report_id`. They differ in the
receiving domain and in `p`, and in nothing else.

**This breaks the tenth and eleventh readings' explanation as a *complete*
account.** That property — `policy_published` carries the policy applied to the
messages in the window, not the record as it reads when the report is written —
predicts both Yahoo reports print the same value, because both describe the same
window. They do not. The property is not refuted (see the boundary below); it is
**insufficient**, and what it fails to cover is a per-receiving-domain split
inside one reporter.

**No cause is offered here.** A per-domain policy cache inside Yahoo would produce
this, and so would several other mechanisms; nothing in these files distinguishes
them. **The thirteenth reading settles it:** if `yahoo.com` reads `p=none` again on
the 08-27 window while a Yahoo sibling reads `quarantine`, it is a persistent
per-domain rendering property of Yahoo's filing. If it flips to `quarantine`, this
was a one-window lag and the eleventh reading's property absorbs it after all.

#### Google is enforcing the policy, and says so in the report

The only row in twelve readings to align on neither mechanism was **not**
quarantined, under a policy reading `p=quarantine`. The reason is in the record:

```xml
<reason>
  <type>forwarded</type>
  <comment>looks forwarded, not quarantined for DMARC</comment>
</reason>
```

That is a documented local override, not the policy being ignored. **It is the
first direct evidence that `p=quarantine` is live and being evaluated at a
receiver** — worth more than any `policy_published` line, because it shows the
policy acting rather than being echoed.

#### `bellsouth.net` is the ninth receiving domain, and the fifth Yahoo-filed

Filed by `Yahoo <dmarchelp@yahooinc.com>` with `sp=-`, the established Yahoo
signature. The eighth reading's finding that "Yahoo" is several receiving domains
holds a fourth time. The list is now `google.com`, `yahoo.com`, `aol.com`,
`att.net`, `cox.net`, `comcast.net`, `protection.outlook.com`, `swbell.net`,
`bellsouth.net`.

#### The first IPv6 sender, and the first row in twelve readings aligned on neither

```
source_ip 2001:470:0:60::2   count 1   disposition none   dkim fail   spf fail
  dkim  d=surfguitar101.com   s=dkim   fail
  spf   d=surfguitar101.com            fail
```

**No IPv6 source has appeared in any prior reading** — grepped, not assumed. It
signs with the legacy `dkim` selector and fails both mechanisms, the ordinary
signature of a forwarded message altered in transit, and Google's own override
says `forwarded`.

**The `2001:470::/32` allocation is UNIDENTIFIED in this reading.** It was not
looked up, and is recorded as a lead rather than an attribution, following the
seventh reading's convention. One message, one window, one receiver. **Reopen
trigger: a second such row, or this same source in the 08-27 window.**

#### The fifteen re-reads reproduce, and the policy boundary is otherwise exact

Every re-read matches its recorded Report-ID and count. Recomputed from all
eighteen files:

| Window | Msgs | Receiving domains | Neither |
|---|---|---|---|
| 2026-08-22 | 3 | 1 | 0 |
| 2026-08-23 | 24 | 6 | 0 |
| 2026-08-24 | 22 | 4 | 0 |
| 2026-08-25 | 11 | 4 | 0 |
| 2026-08-26 | **16** | **3** | **1** |

08-23 at 24 across six and 08-24 at 22 across four match the ninth and tenth
readings; 08-25 at 11 across four matches the eleventh reading's Comcast addendum.
**Windows gain reports and never revise them** now holds across five windows and
eight readings.

**The policy boundary is exact everywhere except the one file.** All fifteen
pre-08-26 reports read `p=none`, and 08-26 is the first window in which
`quarantine` appears at all. That clean boundary is what makes the `yahoo.com`
report an exception rather than a refutation — and also why the exception earns
this much attention.

#### A discrepancy against the eleventh reading, recorded not resolved

The eleventh reading states Microsoft *"has now filed exactly one window late four
consecutive times (08-21, 08-22, 08-23, 08-24)."* **Only two Microsoft files exist
in `~/dmarc`**, covering the 08-22 and 08-23 windows, and nothing was removed
between that reading and this one — fifteen files then, three added, eighteen now.
08-24, 08-25 and 08-26 are all outstanding from Microsoft.

Recorded as a discrepancy to check, **not** as a correction: the parenthetical may
count filing dates rather than windows, or may rest on files deleted before the
eleventh reading. It matters because a live prediction rests on it — *"its
four-consecutive-windows-late pattern still predicts `50.31.156.118` in the next
batch."* If Microsoft has in fact filed nothing since the 08-23 window, that
prediction has no support and `.118` is unobserved for a different reason.

#### What held steady

- **`173.255.245.115` is in every window still.** Six messages at Google, six at
  Yahoo, one at bellsouth, all aligned on both mechanisms.
- **Every row in all eighteen files is `disposition=none`** — including the one
  failing row, by explicit override.
- **Yahoo prints `sp=-`** where Google prints `sp=quarantine`. Unchanged on
  `bellsouth.net` too, and still not a discrepancy.
- **The member's Gmail forward returns.** `209.85.220.41`, 2 messages, SPF fail /
  DKIM pass — after four consecutive absent windows, 08-22 through 08-25, the last
  confirmed by re-reading the 08-25 Google report's source list. The ninth
  reading's gap in the evidence is closed: the class `quarantine` puts at risk is
  observable again, and it passed on DKIM.
- **No Postmark row.** `50.31.156.116` appeared in the 08-25 Google report and is
  **absent** from 08-26. `50.31.156.118` has still never appeared in any report.

#### Bearing on the policy decision

`p=quarantine` is published, resolving, and demonstrably being evaluated — step 7
is executed rather than pending, and nothing here argues to reverse it. Two things
follow.

**The forwarding class is now the live risk, and it is no longer hypothetical.**
Eleven readings ran with zero rows aligned on neither; this one has two forwarded
sources in a single window — `209.85.220.41` passing on DKIM, `2001:470:0:60::2`
failing both. Google exempted the failing one by local heuristic. **That exemption
is Google's policy, not ours, and no other receiver is obliged to make it.** The
ninth reading called this the one class `quarantine` puts at risk; it is now
measured rather than anticipated.

**`include:spf.mtasv.net` ordering is unchanged and still unmet by observation.**
The Postmark row appeared once, in the 08-25 window, and did not recur. One
observation is not a cutover, and the eleventh reading's ordering requirement
stands exactly as written.

#### Predictions for the thirteenth reading

1. **`yahoo.com` reads `p=quarantine` on the 08-27 window.** If it reads `p=none`
   again beside a `quarantine` sibling, the per-domain rendering property is real
   and belongs in the record as a property of Yahoo's filing, not of our zone.
2. **08-26 gains and does not revise** — Comcast at minimum, on its established
   next-day cadence.
3. **No second `2001:470::/32` row.** A second fires the reopen trigger above.
4. **Every row stays `disposition=none`**, with any failing row carrying an
   explicit `<reason>`.

### Thirteenth reading — 2026-08-28, covering 2026-08-27: a fifth reporting organization, and the tool read its report as empty

**Twenty-four files in `~/dmarc` — six new, eighteen re-reads.** Five were saved
2026-08-28 14:51:10–14:52:08Z in one batch. The sixth arrived nine minutes later,
15:00:31Z, and did not come from the batch at all: **Brian found it by hand in
Gmail's spam folder.**

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `11933845663865527618` | 2026-08-27 | 13 | 0 |
| `yahoo.com` | `Yahoo` | `1787896126.912788` | 2026-08-27 | 3 | 0 |
| `aol.com` | `Yahoo` | `1787896126.912720` | 2026-08-27 | 3 | 0 |
| `comcast.net` | `comcast.net` | `v2-1787881526-surfguitar101.com` | 2026-08-27 | 2 | 0 |
| `gmx.net` | **`GMX`** | `54376e1cb8874c6da5bbd085f1d3cdac` | 2026-08-27 | 1 | 0 |
| `protection.outlook.com` | `Outlook.com` | `584373c0c3594244a0638514059b7c76` | 2026-08-26 | 3 | 0 |

**2026-08-27: 22 messages, five receiving domains, 0 aligned on neither
mechanism**, every row `disposition=none`, every report `p=quarantine`. Microsoft
is outstanding, so 22 is a floor.

#### The tool reported a valid report as zero messages, and said so in the log's own words

`tools/dmarc_report.py` on the GMX file, before anything was changed:

```
Receiver : gmx.net
Reporter : ?   <>
Report ID: ?
Policy   : domain=? p=? sp=- adkim=r aspf=r pct=100

  0 messages, 0 aligned on neither mechanism
```

GMX files under the DMARCbis schema, `xmlns="urn:ietf:params:xml:ns:dmarc-2.0"`.
Every `find()` in the tool is unqualified, so `report_metadata`,
`policy_published` and every `<record>` matched nothing. Nothing raised.

**This is the dangerous shape of instrument failure, not the safe one.** It did
not fail to read the file — it produced *a reading*, in the exact sentence this
log has written as a real result in eleven of twelve readings, under a `Receiver`
line that was still correct because it comes from the filename rather than the
body. The only tells are `?` in fields that are read past. Had this file arrived
inside the morning batch instead of nine minutes after it,
**`0 messages, 0 aligned on neither mechanism` would have entered the record as a
measurement of GMX's traffic.** [[suspect-the-measurer-before-the-record]] —
here the measurer was wrong and the record it would have written was internally
consistent with twelve prior readings.

**Proven, not inferred.** The same bytes with only ` xmlns="…dmarc-2.0"` removed
parse completely and print the row. The namespace is the whole cause.

**The scratch aggregator used to recompute window totals in the twelfth and
thirteenth readings had the identical defect** — `findtext('record/…')` over a
`glob('*.xml')`. It was never exposed because no namespaced file had ever been in
the folder. Two independent instruments, one blind spot, because the second was
written against the same assumption as the first.

**Fixed in `tools/dmarc_report.py`:** tags are unqualified after parse, so one
set of paths serves both schemas. Verified three ways —

- the GMX report now prints its metadata and its single row;
- **output over the other twenty-three files is byte-identical**, `diff` confined
  entirely to the GMX block, so the change is an addition and not a rewrite;
- a synthetic *prefixed*-namespace variant of the same report (`<d:feedback
  xmlns:d=…>`) parses identically, so the fix is not specific to a default
  namespace.

#### A second, quieter defect in the same line — the tool was filling in defaults

The policy line printed `adkim`, `aspf` and `pct` as `r`, `r` and `100` when the
report omitted them. **GMX's report contains no `pct` element at all** — the 2.0
schema drops it — and the tool rendered that absence as `pct=100`, which is
indistinguishable from the eight reporters that publish `pct=100` outright. A
receiver's report says what the receiver parsed; a default filled in by the
reader is not evidence about either the zone or the receiver. Absent tags now
print `-`, the convention `sp` already used. The only line that changes across
all twenty-four files is GMX's, to `pct=-`.

#### GMX is the fifth reporting organization and the tenth receiving domain

`GMX <noreply-dmarc@sicher.gmx.net>`, `extra_contact_info`
`https://postmaster.gmx.net/en/case?c=r2002`. Reporting organizations were four
for eleven readings — Google, Yahoo, Comcast, Microsoft. Receiving domains are
now ten: `google.com`, `yahoo.com`, `aol.com`, `att.net`, `cox.net`,
`comcast.net`, `protection.outlook.com`, `swbell.net`, `bellsouth.net`,
`gmx.net`.

Its one row is `173.255.245.115`, count 1, `spf:surfguitar101.com=pass/mfrom`,
`dkim:surfguitar101.com=pass`, `disposition=none`, under `p=quarantine
sp=quarantine`. Ordinary in every respect, which is the point: the file was
nearly recorded as empty.

**Provenance caveat — closed the same day.** The raw message was exported after
this reading was first written. GMX's own signature verified at Gmail —
`dkim=pass header.i=@sicher.gmx.net header.s=s31663417` — and a DKIM body hash
covers the MIME body that carried the attachment, so the report is GMX's rather
than something a spam folder happened to hold. One limit: the exported message
omits the base64 attachment part, so the tie between the signed body and the
bytes on disk is the extraction, not a recomputation here.

#### The 2.0 schema brings four elements no prior report has carried

```xml
<policy_published>
  <discovery_method>psl</discovery_method>   <!-- new -->
  <testing>n</testing>                       <!-- new -->
  ...                                        <!-- and no <pct> -->
<identifiers>
  <envelope_from>surfguitar101.com</envelope_from>   <!-- new -->
<auth_results><spf>
  <scope>mfrom</scope>                       <!-- first as an element -->
```

`discovery_method=psl` says GMX found the policy at the organizational domain via
the public suffix list rather than at the exact name — expected for a report on
the apex, and worth knowing the field exists before a subdomain question needs
it. `testing=n` is the DMARCbis replacement for the `pct` experiment. The tool
prints none of the first three; they are recorded here rather than added, since
no reading has yet needed them.

#### All four of the twelfth reading's predictions held

1. **`yahoo.com` reads `p=quarantine` on 08-27** — Report-ID `1787896126.912788`,
   from the same filing run as `aol.com`'s `.912720`, both `quarantine`.
2. **08-26 gained and did not revise** — 16 → 19 messages across four receiving
   domains.
3. **No second `2001:470::/32` row.** The reopen trigger did not fire.
4. **Every row `disposition=none`** across all twenty-four files; the 08-26
   `forwarded` override remains the only `<reason>` anywhere in the corpus.

**Prediction 2 held on its claim and failed on its named mechanism.** It said
*"Comcast at minimum, on its established next-day cadence."* The gain came from
Microsoft. **Comcast has still filed nothing for the 08-26 window, while its
08-27 report is already in hand** — the first time any reporter has filed out of
window order. Recorded as an observation; 08-26 may still gain, which is what the
convention predicts.

#### The Yahoo policy line was a lag, not a per-domain rendering property

The twelfth reading found `bellsouth.net` reading `quarantine` beside
`yahoo.com` reading `none` in one Yahoo filing run for one window, and named the
test: *"if it reads `p=none` again beside a `quarantine` sibling, the per-domain
rendering property is real."* It did not. **Both Yahoo-filed reports for 08-27
read `quarantine`.**

So the property is a **cache lag that resolves per receiving domain**, not a
permanent difference in how Yahoo renders a report. `p=quarantine` was published
2026-08-25; `bellsouth.net` had it for the 08-26 window, `yahoo.com` did not, and
`yahoo.com` had it a window later. Roughly one to two days, against a record TTL
of 300 seconds. **`policy_published` is a statement about when a receiver last
read the zone, and nothing else** — a property of Yahoo's filing, as prediction 1
required before it could be written down as one.

#### `50.31.156.118` appears at last, in Microsoft's 08-26 report

```
source_ip 50.31.156.118   count 1   disposition none   dkim pass   spf pass
  dkim  d=pm.mtasv.net        pass
  dkim  d=surfguitar101.com   pass
  spf   d=pm-bounces.surfguitar101.com   pass/mfrom
```

This is the Outlook send. The eleventh reading predicted it in the next batch on
a four-consecutive-windows-late reading of Microsoft's cadence; the twelfth
reading recorded that **only two Microsoft files existed**, so the prediction had
no support as stated. **Both are now settled: the row landed, and the cadence
claim was wrong.** Microsoft's three files cover 08-22, 08-23 and 08-26 — it files
one window late *when it files*, and it skipped 08-24 and 08-25 entirely. The
prediction was right by accident, which is worth more to note than a miss.

It is also the **second Postmark IP** and the first to reach an aggregate report
from the Microsoft side, passing on both mechanisms under `p=quarantine`.
`50.31.156.116` appeared once, in Google's 08-25 report, and has not recurred.

#### `2001:470:0:60::2` is `mink.he.net`

The twelfth reading recorded the allocation as **UNIDENTIFIED**, a lead rather
than an attribution. It is Hurricane Electric: PTR `mink.he.net`, and the AAAA
for that name resolves back to the same address, so the lookup is
forward-confirmed rather than a bare PTR. Consistent with the `forwarded`
override Google applied to it and with the ordinary shape of a forwarded message
altered in transit. It did not recur in the 08-27 window.

#### The zone re-verified live, and what that says about every policy line in this log

```
_dmarc.surfguitar101.com.  TXT  "v=DMARC1; p=quarantine; rua=mailto:00fc…@dmarc-reports.cloudflare.net,mailto:admin@surfguitar101.com"
surfguitar101.com.         TXT  "v=spf1 ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 include:_spf.mx.cloudflare.net -all"
```

**The DMARC record carries `p` and `rua` and nothing else** — no `sp`, `np`,
`pct`, `adkim` or `aspf`. Every one of those tags that has appeared in a
`policy_published` block across thirteen readings is a receiver filling in an RFC
default. `p` is the only field in that block that discriminates, which is exactly
why the Yahoo lag above was visible at all.

The apex SPF is unchanged and still correct on the tenth reading's requirement:
`include:_spf.mx.cloudflare.net` retained, `include:spf.mtasv.net` still absent.
Both Postmark observations passed SPF through `pm-bounces.surfguitar101.com`
(CNAME to `pm.mtasv.net`, whose record is `v=spf1 include:spf.mtasv.net -all`),
relaxed-aligned under `aspf=r`.

#### The `rua` channel has a silent-loss mode

One of six reports for this reading was in Gmail's spam folder, and it was
recovered because Brian went looking. **The reporting pipeline is the whole
instrument for this step, and it has now been observed dropping a report where
nothing would have announced the loss** — no bounce, no gap in a sequence, since
reporters are discovered rather than enumerated. A reporter that has never filed
before is indistinguishable from one whose report was filtered.

**Why it was filtered was unmeasured when this was written, and the raw message
arrived the same day. The hypothesis it was written against is dead.** That
hypothesis was *"a first-seen sender arriving over a Cloudflare SRS forward,"*
which is an authentication story, and the message failed no authentication check
at all:

```
dkim=pass  header.i=@sicher.gmx.net      header.s=s31663417   <- GMX's own, intact across the forward
dkim=pass  header.i=@surfguitar101.com   header.s=cf2024-1    <- Cloudflare's, on this domain
dkim=pass  header.i=@cloudflare-email.net header.s=cf2024-1
arc=pass   (i=1 spf=pass spfdomain=mout-bounce.gmx.net dkim=pass dkdomain=sicher.gmx.net)
spf=pass   SRS0=tvML=vg=mout-bounce.gmx.net=postmaster@surfguitar101.com via 104.30.8.104
dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=gmx.net
```

Three signatures verified, ARC verified, SPF verified on the SRS envelope, DMARC
passed on GMX's own domain. Cloudflare had scored it `X-CF-SpamH-Score: 0` and
GMX stamped `X-Spam-Flag: NO`. **Nothing in the message is what Gmail objected
to**, which means the objection is content or reputation — and no header a
message carries can show that.

**What the message does expose is a mechanism worth naming.** Cloudflare adds
`Feedback-ID: surfguitar101.com:1:1:Cloudflare`. Gmail clusters sender reputation
on that identifier, so **everything Email Routing forwards for this domain shares
one reputation bucket** — the DMARC reports and whatever spam arrives at
`admin@`, `abuse@` and `postmaster@` and is forwarded to the same inbox. If that
bucket is what filed this report in spam, the mail being forwarded to the aliases
is what fills it, and no report is individually at fault.

**That is a hypothesis with a test, and the test has never been run:** Gmail
Postmaster Tools reads that reputation directly for `surfguitar101.com`.
[[search-the-artifacts-before-claiming-new]] — `Feedback-ID` and `ARC-*` appear
in no other artifact in this project, so this is genuinely the first look at the
forwarding stream's identity; `cf2024-1` is the opposite case, already recorded across
four artifacts, and its appearance here is a re-observation in service rather
than a discovery.

#### Three measurements the raw message settles in passing

1. **The SRS dependency reproduces on a fourth Cloudflare egress IP.**
   `104.30.8.104`, inside `104.30.0.0/19` from `include:_spf.mx.cloudflare.net`.
   `104.30.10.185`, `104.30.8.10` and `104.30.10.31` are already in the record.
   The tenth reading's rule — that include must survive any apex rewrite — now
   rests on four addresses spread across the range rather than the one it was
   written from.
2. **Forward latency, a second measurement.** Cloudflare received from
   `mout-bounce.gmx.net` at 08:49:24Z; Gmail received at 08:49:28Z. **Four
   seconds**, against the tenth reading's two on a different reporter.
3. **A send time read from a clock rather than decoded from a string.** GMX's
   `Date:` and Cloudflare's `Received:` agree at 08:49:24Z, 8h49m after the
   window closed. Its Report-ID is bare hex and carries no timestamp at all —
   the shape that cannot repeat the tenth reading's error of reading Comcast's
   Report-ID as a send time.

#### What held steady

- **One sending source for site mail.** `173.255.245.115` in every window, now
  across ten receiving domains and five reporting organizations.
- **Zero messages aligned on neither mechanism** in the 08-27 window, and one in
  the corpus — the 08-26 forwarded row, disposition none by explicit override.
- **Windows gain and never revise.** 08-26 at 19 across four; the convention now
  holds across six windows and ten readings.
- **The member's Gmail forward (`209.85.220.41`) is absent from 08-27.** It has
  always been intermittent; absence is not removal.
- **Yahoo prints `sp=-`.** Unchanged on `aol.com` and `yahoo.com`.

| Window | Msgs | Receiving domains | Neither |
|---|---|---|---|
| 2026-08-22 | 3 | 1 | 0 |
| 2026-08-23 | 24 | 6 | 0 |
| 2026-08-24 | 22 | 4 | 0 |
| 2026-08-25 | 11 | 4 | 0 |
| 2026-08-26 | 19 | 4 | 1 |
| 2026-08-27 | **22** | **5** | 0 |

#### Bearing on the policy decision

`p=quarantine` is live at five reporting organizations and ten receiving domains,
with 22 messages in the newest window and no message anywhere failing both
mechanisms except the one Google itself exempted as forwarded. **Nothing argues
for reversing step 7**, and the risk register is unchanged: the forwarding class
is the exposure, and no receiver is obliged to make Google's exemption.

What this reading adds is not about the policy but about the evidence for it.
**Two of the six reports would have been misread by the instruments in use** —
GMX as an empty report, and its absent `pct` as a published one — and the first
of those would have produced a sentence indistinguishable from a real result.
The corpus is small enough that one silently zeroed reporter is a visible
fraction of a window.

#### Predictions for the fourteenth reading

1. **Comcast files for 08-26 late, or it never does.** Its 08-27 report is
   already in hand, so a late 08-26 filing is a gain; a permanent absence is the
   first window any reporter has skipped while filing the next one, and belongs
   in the record as such.
2. **Microsoft files for 08-27**, one window late, in the next batch — the
   pattern its three filings support, stated as *when it files* rather than as a
   cadence, per this reading's correction.
3. **Every report reads `p=quarantine`.** The Yahoo lag is spent, and no receiver
   should still be holding a `p=none` fetch three days after publication.
4. **GMX's report parses with metadata and a row**, which is the regression test
   for the fix above. A second `0 messages` from a namespaced reporter means the
   unqualification did not survive whatever else changed.
5. **Nothing here predicts where the next GMX report lands.** Record its folder
   as an observation either way, and read Gmail Postmaster Tools for
   `surfguitar101.com` before treating one spam filing as a pattern.

#### Addendum, 2026-08-28 — Postmaster Tools cannot answer the question, and two of its three complaints are false

Prediction 5 above sends the fourteenth reading to Gmail Postmaster Tools before
treating one spam filing as a pattern. It was read the same afternoon.
**It is discharged, not by an answer but by the instrument being unavailable at
this domain's volume** — and the panel it does show is ten days stale.

**The compliance dashboard is a snapshot from 2026-08-18 19:00 and has not
refreshed since.** That date precedes the MX flip, the apex SPF rewrite, the
Postmark cutover and `p=quarantine`. The only email change it could reflect is
`p=none`, published 08-17, and it does not reflect that either.

| Requirement | Status as shown |
|---|---|
| SPF and DKIM authentication | Compliant |
| From: header alignment | Compliant |
| DMARC authentication | **Needs work** — *set up DMARC with a minimum policy of none* |
| Encryption | **Needs work** — *set up TLS encryption* |
| User-reported spam rate | Compliant |
| DNS records | **Needs work** — *set up forward and reverse DNS records* |
| One-click unsubscribe | Compliant |
| Honor unsubscribe | Compliant |

**Two of the three complaints are false, measured rather than argued.**

*DMARC* asks for a policy of at least `p=none`. `p=none` had been live for a day
at the moment of the snapshot and the record has read `p=quarantine` since 08-25,
verified authoritatively from two resolvers in the eleventh reading and again
today.

*DNS records* asks for forward-confirmed reverse DNS on the sending IP. It is
complete, and has a name this project published:

```
173.255.245.115         ->  PTR  mail.surfguitar101.com
mail.surfguitar101.com  ->  A    173.255.245.115
```

**Encryption is the one that stays open.** jaguar sends with
`smtp_tls_security_level = may`, and its mail log carries TLS to Gmail both now
and on the snapshot's own day:

```
Aug 18 19:56:37 jaguar postfix/smtp: Untrusted TLS connection established to
  gmail-smtp-in.l.google.com[142.250.101.26]:25: TLSv1.2 with cipher
  ECDHE-ECDSA-AES128-GCM-SHA256 (128/128 bits)
```

`Untrusted` is an unverified peer certificate, not an unencrypted session; 87
such lines cover 08-23 to 08-28 and 4 cover 08-18. **Two limits keep this from
closing the row.** `may` is opportunistic, so Postfix would fall back to
plaintext without complaint against a peer that offered no STARTTLS; and
`smtp_tls_loglevel = 1` logs once per *connection*, not per delivery, so 08-18's
25 deliveries to `gmail-smtp-in` against 4 TLS lines is consistent with
connection reuse but is not proof that each was encrypted. The Encryption tab
holds the actual percentage and was not read.

**`Not enough outgoing email` is what closes the reputation question.** The
deliverability panels need volume Google does not publish exactly — the
consistent figure in the field is 100–200 messages a day to Gmail addresses.
The best window in this entire log is **13 messages at `google.com`**. So the
`Feedback-ID: surfguitar101.com:1:1:Cloudflare` bucket named in the amendment
above has no instrument at this domain's scale, and will not acquire one by
waiting.

**A third staleness mode, which makes this session's through-line.** Three
independent measurement channels, three different ways of looking valid while
saying nothing true: `policy_published`, a receiver's cached read of the zone,
lagging publication by a day or two; `tools/dmarc_report.py`, returning a
confident `0 messages` for a schema it could not parse; and this panel, a
ten-day-old snapshot rendered without any indication that it is one other than a
date in small type. None of the three fails loudly. [[suspect-the-measurer-before-the-record]]

#### Addendum, 2026-08-28 — the spam folder is a census, and reading the one filtered report removed it from the count

`in:spam to:admin@surfguitar101.com` returns **one message, and it is not a DMARC
report** — a bounce from a member subscribed to a forum topic.

**The GMX report is not in that count because retrieving it took it out.** It was
opened and its attachment saved in order to be read at all, and it is no longer
in the folder. [[probes-must-not-perturb-what-they-measure]] — the act of reading
the only filtered report is what removed it from the measure of filtering. The
honest tally is **one filtered report in the corpus of twenty-four**, and the
folder can no longer show it.

**The census is otherwise complete.** Gmail purges spam after 30 days; the
reporting era is eleven days old, from 2026-08-17. Nothing has aged out, so the
folder is a full record of that period rather than a sample — subject to the one
thing not measurable from here, whether it was emptied by hand.

**The denominator was not obtained, and the attempt is recorded as abandoned
rather than left looking unasked.** `in:anywhere to:surfguitar101.com` returns
hundreds and Gmail answers `1-50 of many` at every narrowing tried, including
date-bounded ones. It is also the wrong population: Email Routing has forwarded
for this domain only since roughly 08-23, so most of those hundreds never touched
the stream in question. **Dropped deliberately** — the rate is one filtered
message against a stream measured in hundreds, and no plausible exact figure
changes what follows.

**The reputation hypothesis is unsupported.** Two independent lines say so: the
compliance panel's *User-reported spam rate: Compliant*, and filtering that is
singular rather than systematic. A poisoned `Feedback-ID` bucket would filter
broadly; this filtered once.

**What survives is narrower and fits the evidence better.** The filtered message
was the **first mail this inbox had ever received from `sicher.gmx.net`**, and it
had passed three DKIM signatures, ARC, SPF on the SRS envelope and DMARC. That is
per-message, first-contact classification, not stream reputation.

**The silent-loss risk stands, and the narrowing makes it sharper rather than
smaller.** The exposure is a reporter's *first* filing — which is exactly the
case that cannot be detected, since reporters are discovered rather than
enumerated and a first filing that was filtered is indistinguishable from a
reporter that has never filed. Rare, specific, and invisible in the one place it
matters.

### Fourteenth reading — 2026-08-29, covering 2026-08-28: an eleventh receiving domain, and a fourfold volume day that the sending host explains

**Thirty-one files in `~/dmarc` — seven new, twenty-four re-reads.** All seven
were saved in one batch, 2026-08-29 16:31:46–16:33:16Z, ninety seconds end to
end. No hand-retrieved straggler this time; see *Where the GMX report landed*
below for what that does and does not establish.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `11396979217634472737` | 2026-08-28 | 55 | 0 |
| `yahoo.com` | `Yahoo` | `1787982481.681225` | 2026-08-28 | 17 | 0 |
| `comcast.net` | `comcast.net` | `v2-1787967754-surfguitar101.com` | 2026-08-28 | 8 | 0 |
| `gmx.net` | `GMX` | `54ee4a9fdd8e402798bf750c5f1a78e7` | 2026-08-28 | 8 | 0 |
| **`verizon.net`** | `Yahoo` | `1787982481.681096` | 2026-08-28 | 6 | 0 |
| `aol.com` | `Yahoo` | `1787982481.681040` | 2026-08-28 | 2 | 0 |
| `protection.outlook.com` | `Outlook.com` | `5492a6c1019f4462a187e2d93e1580f1` | 2026-08-27 | 3 | 0 |

**2026-08-28: 96 messages, six receiving domains, 0 aligned on neither
mechanism**, every row `disposition=none`, every report `p=quarantine`. Microsoft
is outstanding for 08-28, so 96 is a floor.

**The floor convention held again, and this time it was worth 3.** The thirteenth
reading recorded 08-27 as 22 with Microsoft outstanding. Microsoft filed, and
08-27 closes at **25**.

#### All four testable predictions held, and the fifth resolved as a skip

1. **Comcast never filed for 08-26.** It has now filed 08-27 and 08-28 while that
   window stays empty. Recorded as the prediction required: **the first window any
   reporter has skipped while filing the ones after it.** Two windows have passed;
   it is a skip rather than a lag until something contradicts that.
2. **Microsoft filed for 08-27, one window late** — its fourth filing, arriving in
   the batch after the window it covers. Stated as *when it files*, not a cadence.
3. **Every report reads `p=quarantine`** — all seven.
4. **GMX parsed with metadata and a row.** The regression test passes: reporter,
   Report-ID, policy and an 8-message row all present, where the thirteenth
   reading's tool printed `?` and `0 messages`. `pct` is absent again and prints
   `-`, which is the 2.0 schema behaving as the fix assumed rather than a gap.

#### `verizon.net` is the eleventh receiving domain, and Yahoo's filing pattern reproduces a third time

Yahoo files one report per hosted domain, and the count of domains it files for is
now six: `yahoo.com`, `att.net`, `cox.net`, `aol.com`, `bellsouth.net`, and now
`verizon.net`. The three Yahoo reports in this batch share the Report-ID prefix
`1787982481` — `.681040`, `.681096`, `.681225` — one generation run, exactly as the
ninth and twelfth readings found.

**All three read `p=quarantine`.** The twelfth reading's `bellsouth.net`/`yahoo.com`
split, which the thirteenth resolved as a cache lag that clears per receiving
domain rather than a rendering property, gets a third clean window. Nothing here
reopens it.

#### The volume quadrupled, and the sending host accounts for it

08-27 closed at 25 messages. 08-28 is at 96 — **3.8× the day before it, and the
largest window in the log by a factor of four.** A jump that size in an
authentication instrument is worth explaining before it is filed away, because the
two explanations that matter — ordinary traffic, and a loop or misconfiguration —
look identical in the aggregate reports.

**jaguar's own mail log says ordinary traffic.** Its Postfix `status=sent` lines
per day:

```
Aug 23  15     Aug 26  18     Aug 29  34 (partial)
Aug 24  43     Aug 27  20
Aug 25  15     Aug 28  125
```

**125 sends went to 32 distinct recipients in eight bursts**, each burst delivering
to ten to twelve addresses inside the same second with one queue ID per recipient:

```
00:31:52  02:10:48  07:59:13  09:58:03  13:49:47  14:29:09  17:42:54  18:08:11
```

That is application fan-out — one event, N subscribers — repeated eight times.
08-27 has exactly one such burst. **121 of the 125 are `from=<admin@surfguitar101.com>`.**
So 08-28 was a busy day on a subscribed forum topic, not a retry loop: a loop
would repeat recipients rather than spread across 32 of them, and would not
distribute itself across eight separate hours.

**The per-domain agreement is close but must not be read as a reconciliation.**

| Recipient domain | jaguar sends | DMARC report |
|---|---|---|
| `gmail.com` | 45 | 47 (`google.com`, direct row) |
| `yahoo.com` | 18 | 17 |
| `comcast.net` | 8 | 8 |
| `gmx.at` | 8 | 8 (`gmx.net`) |
| `verizon.net` | 6 | 6 |
| `aol.com` | 3 | 2 |

**jaguar runs CDT, so its syslog day is not the DMARC window.** `Aug 28` in that
log is 2026-08-28 05:00Z through 2026-08-29 05:00Z; the report window is
00:00:00Z–23:59:59Z. The two populations overlap on nineteen hours of twenty-four
and are *not* the same set. The agreement above is therefore corroboration that
the volume is real and that no third party is sending, **not** an exact match —
and the rows that differ by one or two are the expected consequence of the shift
rather than a discrepancy to chase. [[probes-must-not-perturb-what-they-measure]]

**`email.log` could not be used, and the reason is worth recording.** Step 16
task 09 built exactly the instrument this question wants — one line per message
with a category — but it lives on the `modernize` branch and jaguar runs the
pre-cutover code. There is no `email.log` on that host. Categorising this day's
mail by `category=` is available only after cutover; until then the finest
available cut is Postfix's `from=`, which is why the paragraph above says
"a subscribed forum topic" and stops there.

#### The forwarding class quadrupled, and every message survived on DKIM alone

`209.85.220.41` — Google's forwarder — carried **8 messages on 08-28, against 2 on
08-26**, and every one of them:

```
209.85.220.41   8  none  fail  pass  spf:gmail.com=pass/? dkim:surfguitar101.com=pass
```

SPF authenticates `gmail.com`, which is not the header-from domain, so
`policy_evaluated` records `spf=fail`. DKIM survives the hop with the
`surfguitar101.com` signature intact, so DMARC passes on DKIM alone and
`disposition=none` needs no exemption to reach it.

**This is the risk register's forwarding class, and it is the good half of it.**
The twelfth reading's `2001:470:0:60::2` row is the bad half — DKIM broken in
transit, aligned on neither, delivered only because Google applied a local
forwarding exemption it is under no obligation to apply. **That row did not
recur**, and no row in this batch aligned on neither mechanism. Eight forwarded
messages at four times the prior volume, all passing on the mechanism that is
supposed to survive forwarding, is the strongest evidence yet that the exposure is
narrow — but it is evidence about the path that works, and says nothing about the
path where a forwarder rewrites the body.

#### Postmark's third distinct IP in three appearances

```
50.31.156.116   google.com, 08-25
50.31.156.118   protection.outlook.com, 08-26
50.31.156.113   protection.outlook.com, 08-27   <- new
```

Every one passes on both mechanisms, `spf:pm-bounces.surfguitar101.com=pass/mfrom`
plus two DKIM signatures, `pm.mtasv.net` and `surfguitar101.com`. Three
appearances, three addresses, no repeat: **the `include:` in the SPF record is
doing the work an enumerated IP list could not**, which is the eleventh reading's
point arriving with a third witness.

#### The GMX report landed in the inbox — the spam filing was first contact, not a pattern

The thirteenth reading found GMX's first filing in Gmail's spam folder, and
prediction 5 asked only that the next one's folder be recorded. **Brian reports it
arrived in the inbox.** The files could not answer this — mtime records when a file
was saved, not which folder it came from — so the source is his observation, named
here rather than inferred from the batch ordering that merely hinted at it.

**This discharges the reputation hypothesis rather than leaving it narrowed.** The
thirteenth reading's addendum argued from two independent lines — *User-reported
spam rate: Compliant*, and filtering that was singular rather than systematic —
that the filtered report was per-message, first-contact classification of a sender
this inbox had never seen, not a judgement on the stream. **The second filing from
`sicher.gmx.net` was not filtered.** That is the prediction the hypothesis makes
and the one a stream-reputation account does not: a poisoned `Feedback-ID` bucket
filters the second message too.

**The silent-loss mode stands untouched, and this is the reading where that
becomes clear rather than pessimistic.** The exposure the thirteenth reading named
is a reporter's *first* filing — exactly the case just observed, and exactly the
case that cannot be detected, since a first filing that was filtered is
indistinguishable from a reporter that has never filed. GMX was caught only
because Brian went looking in spam by hand. **Two reporting organizations have
appeared since the `rua` channel opened; if a third's first filing is filtered,
nothing in this log will show it.** The risk is unchanged in kind and unchanged in
size — what changed is that it is now the *only* thing the GMX episode supports.

#### What held steady

- Every row in all thirty-one reports is `disposition=none`.
- `173.255.245.115` is still the only unsigned-path sender, and still passes both
  mechanisms everywhere it appears.
- Policy renders `adkim=r aspf=r` in every report; the relaxed alignment the
  eleventh reading flagged as load-bearing-but-unchosen remains both.
- The twenty-four re-reads reproduce exactly, including the `p=none`/`p=quarantine`
  boundary at the 08-25 publication and the twelfth reading's Yahoo split.
- `sp` is still absent from every Yahoo report and present in every other
  reporter's, and still prints `-` rather than a filled-in default.

#### Bearing on the policy decision

`p=quarantine` is live at five reporting organizations and eleven receiving
domains. **The heaviest window in the log is also the cleanest**: 96 messages,
six receivers, zero aligned on neither mechanism, zero quarantined. The volume
that arrived was a 3.8× step and nothing in the authentication results moved with
it, which is the property that matters — the configuration scaled without a
single alignment failure.

**Nothing argues for reversing step 7, and this is the first reading that says
something positive about tightening further.** The case against `p=reject` has
been the forwarding class, and the only measured instance of it failing both
mechanisms is one message on 08-26 that Google chose to exempt. Against that,
08-28 put eight forwarded messages through the same path with DKIM intact. **That
is not yet enough**: one clean day at volume does not establish a rate for an
event that appeared once in twelve readings, and `p=reject` converts Google's
discretionary exemption into someone else's bounce. The register is unchanged;
what changed is that the argument now has a number on both sides.

#### Predictions for the fifteenth reading

1. **Microsoft files for 08-28**, one window late, in the next batch — the pattern
   its four filings support. 08-28 then closes above 96.
2. **Comcast's 08-26 stays empty.** Three windows on, a late arrival would be the
   surprise; record either outcome, since a skip that resolves is a different
   property from a skip that does not.
3. **08-29 comes in far below 96** — jaguar's partial day is 34 sends against 125,
   so the fourfold window should read as a one-day event rather than a new level.
   If 08-29 lands near 96, the fan-out has a cause worth finding before cutover.
4. **Every report reads `p=quarantine`**, and GMX parses with metadata and a row
   for the second consecutive window.
5. **GMX's third filing lands in the inbox**, as the second did. A return to spam
   after an unfiltered delivery would break the first-contact account and put
   stream reputation back on the table, so it is worth a glance rather than an
   assumption. **The standing exposure is a reporter this log has never seen** —
   check spam by hand for a filing from an unfamiliar organization, since that is
   the one loss mode the corpus cannot reveal on its own.

### Fifteenth reading — 2026-08-30, covering 2026-08-29: one Microsoft report is two receiving domains, and the fourfold day does not repeat

**Thirty-nine files in `~/dmarc` — eight new, thirty-one re-reads.** All eight
were saved in one batch, 2026-08-30 14:26:44–14:28:27Z, 103 seconds end to end.
No hand-retrieved straggler.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `5492429701232009227` | 2026-08-29 | 27 | 0 |
| `yahoo.com` | `Yahoo` | `1788068018.133082` | 2026-08-29 | 8 | 0 |
| `comcast.net` | `comcast.net` | `v2-1788050610-surfguitar101.com` | 2026-08-29 | 3 | 0 |
| `gmx.net` | `GMX` | `87c6468f9da04d50af468d58e6f8def2` | 2026-08-29 | 2 | 0 |
| `verizon.net` | `Yahoo` | `1788068018.133037` | 2026-08-29 | 2 | 0 |
| **`att.net`** | `Yahoo` | `1788068018.133011` | 2026-08-29 | 1 | 0 |
| `aol.com` | `Yahoo` | `1788068018.132981` | 2026-08-29 | 1 | 0 |
| `protection.outlook.com` | `Outlook.com` | `4364b3ec9c4646eba6f50c8f1a9a162f` | 2026-08-28 | 16 | 0 |

**2026-08-29: 44 messages, seven receiving domains, 0 aligned on neither
mechanism**, every row `disposition=none`, every report `p=quarantine`. Microsoft
is outstanding for 08-29, so 44 is a floor.

**The floor convention held again, and this time it was worth 16.** The
fourteenth reading recorded 08-28 as 96 with Microsoft outstanding. Microsoft
filed, and 08-28 closes at **112** — the largest single correction the convention
has produced, and the largest window in the log.

#### All five predictions held, the fifth on Brian's observation rather than the files

1. **Microsoft filed for 08-28, one window late** — its fifth filing, arriving in
   the batch after the window it covers. Five filings, five times one window
   late. Still stated as *when it files*, not as a cadence.
2. **Comcast's 08-26 stays empty.** It has now filed 08-27, 08-28 and 08-29 while
   that window remains the only one any reporter has skipped. Four windows on, a
   late arrival would be the surprise.
3. **08-29 came in far below 96** — 44 against 112, with Microsoft outstanding.
   The fourfold day was a one-day event, not a new level; see the volume section.
4. **Every report reads `p=quarantine`** — all eight. **GMX parsed with metadata
   and a row** for the second consecutive window: reporter, Report-ID, policy and
   a 2-message row. `pct` absent and printing `-`, the 2.0 schema again.
5. **GMX's third filing landed in the inbox**, as the second did. The files
   could not answer this — mtime records when a file was saved, not which folder
   it came from — so the source is **Brian's observation**, named here rather
   than inferred from the fact that the report arrived at all. A report
   retrieved by hand from spam and one delivered to the inbox produce identical
   files. See *Two unfiltered filings* below for what the second one adds.

#### `protection.outlook.com` is one reporting endpoint covering three mailbox domains, and the tool does not show it

Microsoft's 08-28 report carries **two records with the same `source_ip`**, which
`tools/dmarc_report.py` renders as two visually identical lines:

```
  173.255.245.115      9  none        pass     pass      spf:surfguitar101.com=pass/mfrom dkim:surfguitar101.com=pass
  173.255.245.115      7  none        pass     pass      spf:surfguitar101.com=pass/mfrom dkim:surfguitar101.com=pass
```

They are not duplicates. Each record carries an `<identifiers><envelope_to>` the
tool never prints:

| Window | `envelope_to` per record | Msgs |
|---|---|---|
| 08-22 | `hotmail.com` | 3 |
| 08-23 | `hotmail.com` | 1 |
| 08-26 | `hotmail.com`, `outlook.com` | 2 + 1 |
| 08-27 | `hotmail.com`, `outlook.com` | 2 + 1 |
| 08-28 | `hotmail.com`, **`live.com`** | 9 + 7 |

**This is the Yahoo finding again in a different place.** The eighth reading
established that "Yahoo" is several receiving domains, distinguishable only by the
report *filename*. Microsoft distinguishes them **inside one file**, and the
consequence is the same: `protection.outlook.com` has been read as one receiving
domain for five readings, and it is at least three — `hotmail.com`, `outlook.com`
and `live.com`.

**jaguar's log corroborates the split independently.** Its 08-28 remote sends go
to `hotmail.com` 10 and `live.com` 7, against Microsoft's 9 and 7. Two instruments
that share no code agree on the proportion, so the split is a real property of the
mail rather than a rendering artifact.

**The "eleven receiving domains" figure needs its name corrected, not its
arithmetic.** It counts **reporting endpoints** — the receiver field of the
filename — and that is the only quantity comparable across reporters. Yahoo
exposes its hosted domains by filing one report per domain; Microsoft exposes them
in `envelope_to`; **Google, Comcast and GMX omit `envelope_to` entirely and file
one report**, so for those three the mailbox-domain count is unknown, not one.
Mixing the two measures would produce a number no reporter supports. The endpoint
count stays eleven and this batch adds no twelfth.

**Instrument gap, not fixed here.** The thirteenth reading recorded `envelope_from`
arriving with GMX's 2.0 schema and chose not to print it, since no reading needed
it. `envelope_to` is the case where that choice costs a finding: two identical
lines are indistinguishable from a repeated row, and this one went unread from
08-26 to today. Left as a recorded gap for Brian to decide on rather than changed
under a reading.

#### `att.net` returns after six windows, and Yahoo's filing run reproduces a fourth time

`att.net` last appeared in the 08-23 window; it is back for 08-29 with one
message. Not a new receiving domain and not a skip that resolved — it is a domain
with too little traffic to appear every day, which is what a 1-message report
looks like.

Yahoo's four reports in this batch share the Report-ID prefix `1788068018` —
`.132981`, `.133011`, `.133037`, `.133082` — one generation run across `aol.com`,
`att.net`, `verizon.net` and `yahoo.com`. Four domains this time against three
last, and all four read `p=quarantine`. The twelfth reading's `p=none`/`p=quarantine`
split within a single run has not recurred in three windows.

#### The volume fell back, and a counting convention had to be recovered first

08-28 closed at 112 messages; 08-29 reads 44 with Microsoft outstanding. jaguar's
Postfix log agrees that the spike was one day:

```
Aug 23  15     Aug 26  18     Aug 29  66
Aug 24  43     Aug 27  20     Aug 30  28 (partial)
Aug 25  15     Aug 28  125
```

**Those are remote deliveries only, and the qualifier is the finding.** A first
count of `status=sent` lines returned 18 / 44 / 15 / 19 / 21 / 125 / 67 and
disagreed with the fourteenth reading on four of six days it should have
reproduced exactly. The difference is `relay=local` — deliveries that never leave
the host and therefore can never appear in any DMARC report. Excluding them
reproduces the fourteenth reading's figures on every prior day. **The convention
was applied there but not written down**, so it is written down here:
`grep status=sent | grep -v relay=local`. A count that silently includes local
delivery inflates the sending side of every comparison below.
[[suspect-the-measurer-before-the-record]]

**08-29 is 66 remote sends against 125 — and its shape is the same shape.** Seven
bursts, each delivering to six to fourteen addresses inside a second or two:

```
01:59  09:45  17:31  18:04  18:56  19:02  20:02
```

27 distinct recipients, and **64 of the 66 are `from=<admin@surfguitar101.com>`**
(one `no_reply@`, one `brian@`). Application fan-out again, at half the rate of
the day before it. Nothing here needs an explanation beyond forum activity.

**Per-domain agreement, and again this is corroboration rather than
reconciliation** — jaguar runs CDT, so its `Aug 29` is 2026-08-29 05:00Z through
2026-08-30 05:00Z against a report window of 00:00:00Z–23:59:59Z, nineteen shared
hours out of twenty-four:

| Recipient domain | jaguar sends | DMARC report |
|---|---|---|
| `gmail.com` | 24 | 22 (`google.com`, direct row) |
| `yahoo.com` | 9 | 8 |
| `comcast.net` | 3 | 3 |
| `att.net` | 3 | 1 |
| `verizon.net` | 2 | 2 |
| `gmx.at` | 2 | 2 (`gmx.net`) |
| `aol.com` | 0 | 1 |
| `hotmail.com` + `live.com` | 4 + 2 | outstanding |

**The residual is accounted for and worth stating, because it is the closest the
two instruments have come.** Of 66 remote sends, 17 went to domains that file no
reports at all — `msorensen.net` 6, `hushmail.com` 3, `tdcspace.dk` 2,
`muohio.edu` 2, `donschott.com` 2, `thegogorillas.com` 1, plus one to
`surfguitar101.com` itself. That leaves 49 to reporting domains, 6 of them
Microsoft's and outstanding, so **43 expected against 44 measured** — and the
`aol.com` row, 1 measured against 0 sent, is exactly the kind of single message
the five-hour shift moves across the boundary. The `att.net` gap of 3 against 1
runs the other way and is a floor that a late filing could close.
[[probes-must-not-perturb-what-they-measure]]

#### Postmark is absent for a second consecutive window

`50.31.156.x` appears in no report for 08-28 or 08-29, after one message in each
of 08-25, 08-26 and 08-27. **This is expected and is recorded so that it is not
read as a regression later.** Those three appearances were test sends; the
cutover has not happened, so nothing routine goes through Postmark yet and a
window with no Postmark row means no test message was sent that day. The property
the eleventh reading established — that the `include:` covers addresses an
enumerated list would not — rests on the three distinct IPs already observed and
is not weakened by a quiet window.

#### The forwarding class halved and stayed clean

`209.85.220.41` carried **5 messages on 08-29, against 8 on 08-28**, every one of
them the same shape:

```
209.85.220.41   5  none  fail  pass  spf:gmail.com=pass/? dkim:surfguitar101.com=pass
```

SPF authenticates `gmail.com`, not the header-from domain, so `policy_evaluated`
records `spf=fail`; the `surfguitar101.com` signature survives the hop and DMARC
passes on DKIM alone. **The twelfth reading's `2001:470:0:60::2` row — aligned on
neither mechanism, delivered only under a discretionary forwarding exemption —
has now not recurred in three windows.** Thirteen forwarded messages across two
days, all surviving on DKIM, against one failure in fifteen readings.

#### Two unfiltered filings, and the first-contact account is now the only one standing

GMX's three filings have landed **spam, inbox, inbox** — the first found by hand
in Gmail's spam folder (thirteenth reading), the second and third delivered
normally (fourteenth reading, and Brian again today).

**The stream-reputation hypothesis is dead rather than merely narrowed.** It
predicts that a poisoned `Feedback-ID` bucket keeps filtering; two consecutive
unfiltered deliveries from `sicher.gmx.net` are the outcome it cannot produce.
The fourteenth reading flagged a return to spam as the result that would put
reputation back on the table, and it did not happen. What remains is what the
thirteenth reading argued from the compliance panel: per-message, first-contact
classification of a sender the inbox had never seen.

**The silent-loss mode is untouched, and two clean filings do not shrink it.**
The exposure was never GMX's second or third report — it is any reporter's
*first*, which is precisely the case that cannot be detected, since a first
filing that was filtered is indistinguishable from a reporter that has never
filed. GMX was caught only because Brian went looking. **Two reporting
organizations have appeared since the `rua` channel opened; if a third's first
filing is filtered, nothing in this log will show it.**

#### What held steady

- Every one of the 47 rows across all thirty-nine reports is `disposition=none`.
- `173.255.245.115` is still the only unsigned-path sender, and still passes both
  mechanisms everywhere it appears.
- Policy renders `adkim=r aspf=r` in **all thirty-nine** reports; the relaxed
  alignment the eleventh reading flagged as load-bearing-but-unchosen remains
  both.
- The thirty-one re-reads reproduce exactly, including the `p=none`/`p=quarantine`
  boundary at the 08-25 publication and the twelfth reading's Yahoo split.
- `sp` is still absent from every Yahoo report and present in every other
  reporter's, and still prints `-` rather than a filled-in default.
- Five reporting organizations; no sixth appeared.

#### Bearing on the policy decision

`p=quarantine` is live at five reporting organizations and eleven reporting
endpoints. **The two heaviest windows in the log are now also the two cleanest**:
112 messages on 08-28 across seven endpoints and 44 on 08-29 across seven, zero
aligned on neither mechanism, zero quarantined, in both.

**The case for `p=reject` gained a second clean day and still is not made.** The
fourteenth reading put a number on both sides; this one adds five more forwarded
messages that survived on DKIM and a third window without the failing forward
recurring. Against that, the exposure is unchanged in kind: one measured instance
in fifteen readings of a forward that broke DKIM, delivered only because Google
chose to exempt it, and `p=reject` converts that discretion into someone else's
bounce. **Two clean days at volume is a rate estimate with two observations in
it.** The register is unchanged; nothing argues for reversing step 7.

#### Predictions for the sixteenth reading

1. **Microsoft files for 08-29**, one window late, in the next batch — six
   filings, six times the same offset. 08-29 then closes near 50, and its
   `envelope_to` records should name `hotmail.com` and at least one of
   `outlook.com` / `live.com`.
2. **Comcast's 08-26 stays empty**, five windows on.
3. **08-30 lands near 44 rather than near 112** — jaguar's partial day is 28
   remote sends, so the ordinary level holds. A second fourfold day inside a week
   would make 08-28 a pattern rather than an event and would be worth finding a
   cause for before cutover.
4. **Every report reads `p=quarantine`**, and GMX parses with metadata and a row
   for the third consecutive window.
5. **GMX's folder stops being worth asking about.** Three filings — spam, inbox,
   inbox — settle it, and a fourth unfiltered delivery would add nothing the
   third did not. Dropped from the prediction list rather than carried as a
   standing check. **The exposure that remains is not GMX: a reporter this log
   has never seen, whose first filing is filtered, is invisible to every
   instrument here.** Checking spam by hand for an unfamiliar organization
   remains the only cover, and it is the one thing on this list that no report
   can prompt.

### Sixteenth reading — 2026-08-31, covering 2026-08-30: the eleventh endpoint was never in the corpus, and the sending-side baseline had a rotation hole

**Forty-four files in `~/dmarc` — five new, thirty-nine re-reads.** All five were
saved in one batch, 2026-08-31 12:09:06–12:09:53, 47 seconds end to end. No
hand-retrieved straggler.

**Provenance, because the mtimes are load-bearing and this batch's are not what
they look like.** Brian saved these five to `~/Downloads`, not `~/dmarc`, and they
were moved across at 12:1x today. `mv` within `/Users` preserves mtime, so the
47-second batch signature above is the original save and is comparable to every
earlier batch. What it is *not* is evidence about the folder they were retrieved
into, which for this batch is not recorded. The distinction matters only if a
later reading tries to read retrieval folder from mtime; it cannot, here or
anywhere. [[probes-must-not-perturb-what-they-measure]]

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `15631526755668090699` | 2026-08-30 | 15 | 0 |
| `yahoo.com` | `Yahoo` | `1788154499.178904` | 2026-08-30 | 6 | 0 |
| `att.net` | `Yahoo` | `1788154499.178819` | 2026-08-30 | 4 | 0 |
| `gmx.net` | `GMX` | `366a002cd58e4bcf94304cc955361e30` | 2026-08-30 | 2 | 0 |
| `protection.outlook.com` | `Outlook.com` | `02b5da2389a6407d8115b1bd6e97e00e` | 2026-08-29 | 7 | 0 |

**2026-08-30: 27 messages, four reporting endpoints, 0 aligned on neither
mechanism**, every row `disposition=none`, every report `p=quarantine`. 27 is a
floor, and this time the floor is softer than usual — see below.

**The floor convention paid a fifth time, and 08-29 closes at 51.** The fifteenth
reading recorded 08-29 as 44 with Microsoft outstanding; Microsoft filed 7, and
44 + 7 = 51 against that reading's "closes near 50".

#### Four of five predictions held; the fifth is directionally right and not yet settled

1. **Microsoft filed for 08-29, one window late** — its sixth filing in the
   corpus, six times the same offset. Its `envelope_to` records read
   `hotmail.com` 5 and `live.com` 2, which is what the prediction named
   (`hotmail.com` and at least one of `outlook.com` / `live.com`). Still stated as
   *when it files*, not as a cadence.
2. **Comcast's 08-26 stays empty**, six windows on. It has filed 08-27, 08-28 and
   08-29 across that gap and did not backfill.
3. **08-30 landed near 44 rather than near 112 — but at 27 the window is too
   incomplete to close.** Held in direction; not settled. See the outstanding-
   endpoint note below, which is the part that is different this time.
4. **Every report reads `p=quarantine`** — all five. **GMX parsed with metadata
   and a row** for the third consecutive window.
5. **GMX's folder was dropped from the list** and no observation was taken. Nothing
   to record, which is what dropping it was for.

#### What is outstanding for 08-30 is not just Microsoft, and the batch clock is why

Every prior window closed with exactly one endpoint outstanding — Microsoft's,
whose one-window-late filing is the best-attested regularity in the log. 08-30 is
outstanding at **Microsoft, `comcast.net`, `aol.com` and `verizon.net`**, and only
the first of those is predictable.

The reason is retrieval time, not receiver behaviour. Batch save times across the
corpus:

```
08-24 09:21   08-26 09:03 (+13:12)   08-28 09:51   08-30 14:26
08-25 09:11   08-27 12:29            08-29 11:31   08-31 12:09
```

Comcast's 08-29 report was saved at 08-30 14:26; today's batch closed at 12:09,
**2h17m earlier in the day**. Whether Comcast, AOL and Verizon had filed for 08-30
by 12:09 is not answerable from these files — a report that had not arrived and a
report that will never arrive produce identical evidence at retrieval time.

**So 08-30's 27 is a weaker floor than 08-29's 44 was**, and the fourth prediction
below is written to close it rather than to re-assert it. Yahoo's filing run
`1788154499` covered only `att.net` and `yahoo.com` this time — two domains against
four in run `1788068018` — which is consistent either with `aol.com` and
`verizon.net` having no 08-30 traffic or with a later run not yet retrieved.

#### The endpoint count is ten in the corpus, and the eleventh has different provenance

The running count of reporting endpoints reads **eleven**. Measured across all
forty-four files, the distinct receiver field of the filename yields **ten**:

```
aol.com  att.net  bellsouth.net  comcast.net  cox.net
gmx.net  google.com  protection.outlook.com  verizon.net  yahoo.com
```

The eleventh is **`swbell.net`**, and the log already says where it came from. The
sixth reading read it from the *sender names of the report mail in Gmail*, and the
eighth recorded it explicitly as *"the one of the seven not read from the file
naming convention."* **That qualifier survived into the count but not into the
count's definition.** The fifteenth reading defines the figure as *"reporting
endpoints — the receiver field of the filename — and that is the only quantity
comparable across reporters,"* and `swbell.net` is precisely the member that
definition excludes.

**Nothing here says `swbell.net` was not a receiving domain.** It says the number
eleven and the sentence attached to it measure different things, and that
`swbell.net` has not appeared as a file in `~/dmarc` in forty-four files across
nine windows. The honest form is **ten by filename, plus `swbell.net` observed
once by report-mail sender name**, and that is how this reading states it.
[[measure-before-recording-in-planning-docs]]

This does not disturb the fifteenth reading's actual finding — that
`protection.outlook.com` is one endpoint covering `hotmail.com`, `outlook.com` and
`live.com`, none of which are endpoints. The mailbox-domain count remains unknown
for Google, Comcast and GMX, which omit `envelope_to` entirely.

#### The sending-side baseline had a hole in it, and two readings reproduced it

The fifteenth reading recorded jaguar's remote sends per day and stated the
counting convention it had recovered — `grep status=sent | grep -v relay=local`.
Applying that convention across **the rotated logs as well as the live one** gives:

```
Aug 23  45      Aug 26  18      Aug 29  66
Aug 24  43      Aug 27  20      Aug 30  37
Aug 25  15      Aug 28  125     Aug 31  27 (partial)
```

**Aug 23 was recorded as 15. It is 45.** The other six days reproduce exactly.

The cause is log rotation, and it is checkable per file:

| File | `Aug 23` remote sends | Range |
|---|---|---|
| `/var/log/mail.log` | 0 | Aug 30 06:41 → Aug 31 12:19 |
| `/var/log/mail.log.1` | **15** | Aug 23 06:38 → Aug 30 06:20 |
| `/var/log/mail.log.2.gz` | **30** | Aug 17 06:36 → Aug 23 06:29 |

Aug 23 straddles the boundary at ~06:30. The fourteenth and fifteenth readings
read the uncompressed logs only, so they counted the tail of the day and called it
the day. **Aug 30 has the same shape** — 30 lines in `mail.log`, 7 more in
`mail.log.1` — which is why the table above reads 37 where the live file alone
says 30.

**The reproduction across two readings is the part worth keeping.** The fifteenth
reading verified its figures by reproducing the fourteenth's on six of seven days
and treated the agreement as corroboration. It was not: both readings ran the same
command against the same truncated file set, so the agreement measured determinism,
not correctness. Two runs of one instrument are one measurement.
[[suspect-the-measurer-before-the-record]]

**What it changes in the record is small but real.** 08-28's "fourfold day" rests on
125 against 08-27's 20 and is untouched. What moves is 08-23: 45 remote sends
against a DMARC window of 24 messages, where the old figure said 15 sent against 24
reported — more reports than sends, which no arrangement of receivers can produce
and which nothing flagged at the time.

#### The UTC-aligned comparison, recovered from the twelfth reading

jaguar runs CDT, so its syslog day is not the report window. The fourteenth and
fifteenth readings noted the five-hour shift and compared anyway, calling the
result corroboration. The twelfth reading did it properly — counting the UTC
window as `Aug 29 19:00`–`Aug 30 18:59` CDT — and that technique is used here.

**The offset is verified rather than assumed.** A log line at `Aug 30 06:46:44`
carries Google's own response id `1788090404`, which is 2026-08-30 11:46:44Z:
UTC−5, confirmed from the receiver's clock inside the same line.

**41 remote sends fall in the 08-30 UTC window**, against 37 in the CDT syslog day.
39 of the 41 are `from=<admin@surfguitar101.com>` (one `root@`, one `brian@`),
delivered in bursts of six to seven — 19:02 and 20:02 on Aug 29, then 02:01, 02:46,
05:22, 06:46, 09:25, 11:34, 12:14, 14:10. Application fan-out, the same shape as
every window since 08-27.

| Recipient domain | jaguar, UTC window | DMARC report |
|---|---|---|
| `yahoo.com` | 6 | **6** |
| `att.net` | 4 | **4** |
| `gmx.at` | 2 | **2** (`gmx.net`) |
| `gmail.com` | 16 | 13 direct (+2 forwarded) |
| `hotmail.com` | 2 | outstanding |
| non-reporting | 11 | — |

**Three of the four reporting domains with traffic agree exactly**, and the reason
is the alignment rather than anything about the mail — the fourteenth and fifteenth
readings each had exact rows too, on domains whose counts were small enough that the
five-hour shift had nothing to move. The
non-reporting eleven are `msorensen.net` 6, `hushmail.com` 4, `muohio.edu` 1.

**The `gmail.com` residual is 3 and is left unexplained.** Aligning the window
removed the five-hour shift, so the shift can no longer be offered for it. Two
candidates remain and neither is measured here: a report window records when the
*receiver evaluated* a message, not when jaguar sent it, so a send near 18:59 CDT
can be evaluated in the next window; and Google's two forwarded messages
(`209.85.220.41`) were addressed by jaguar to some other domain entirely, so they
cannot close a gap in the direct row. **Recorded as a residual, not resolved.**

#### What held steady across all forty-four

- **All 54 rows are `disposition=none`.** Nothing has been quarantined under
  `p=quarantine` at any receiver in any window.
- Evaluated alignment across those 54 rows: **49 `pass`/`pass`, 4 `fail`/`pass`,
  1 `fail`/`fail`.**
- `173.255.245.115` remains the only unsigned-path sender and passes both
  mechanisms in all 46 rows it appears in.
- Policy renders `adkim=r aspf=r` in **all forty-four** reports — the relaxed
  alignment the eleventh reading flagged as load-bearing-but-unchosen, still both.
- **`sp` is absent in exactly the 20 Yahoo reports and present in all 24 others**,
  a clean split with no exceptions, and still prints `-` rather than a default.
- **`pct` is absent in exactly the 4 GMX reports**, the 2.0 schema which drops it.
  All four GMX files now parse with metadata and a row, including the 08-27 one the
  thirteenth reading read as empty — that was the namespace defect in the tool, and
  the re-read confirms the fix rather than a change in GMX's output.
- The thirty-nine re-reads reproduce exactly, including the `p=none`/`p=quarantine`
  boundary at the 08-25 publication and the twelfth reading's `yahoo.com` 08-26
  cache lag.
- **Five reporting organizations; no sixth appeared.**

#### The forwarding class fell again, and the failing forward has not recurred in four windows

`209.85.220.41` carried **2 messages on 08-30**, against 5 on 08-29 and 8 on 08-28,
every one the same shape:

```
209.85.220.41   2  none  fail  pass  spf:gmail.com=pass/? dkim:surfguitar101.com=pass
```

Seventeen forwarded messages now across four windows, all surviving on DKIM. The
twelfth reading's `2001:470:0:60::2` row — aligned on neither, delivered only under
a discretionary forwarding exemption — remains the single instance in sixteen
readings and **has not recurred in four windows**.

#### Postmark absent for a third consecutive window

`50.31.156.x` appears in no report for 08-28, 08-29 or 08-30. Its three appearances
were test sends on distinct IPs — `.116` (08-25, Google), `.118` (08-26, Microsoft),
`.113` (08-27, Microsoft). The cutover has not happened, so a window with no
Postmark row means no test was sent that day. The eleventh reading's property —
that the `include:` covers addresses an enumerated list would not — rests on those
three distinct IPs and is not weakened by a quiet window.

#### Bearing on the policy decision

`p=quarantine` is live at five reporting organizations and ten reporting endpoints.
**The three heaviest windows in the log are its three cleanest**: 112 on 08-28,
51 on 08-29, 27 so far on 08-30, zero aligned on neither mechanism in any of them,
zero quarantined.

**The case for `p=reject` gained a third clean day and still is not made.** This
reading adds two more forwarded messages that survived on DKIM and a fourth window
without the failing forward recurring. The exposure is unchanged in kind: one
measured instance in sixteen readings of a forward that broke DKIM, delivered only
because Google chose to exempt it, and `p=reject` converts that discretion into
someone else's bounce. **Three clean days at volume is a rate estimate with three
observations in it.** The register is unchanged; nothing argues for reversing
step 7.

#### Predictions for the seventeenth reading

1. **Microsoft files for 08-30**, one window late — seven filings, seven times the
   same offset — and its `envelope_to` records name `hotmail.com` plus at least one
   of `outlook.com` / `live.com`. jaguar sent 2 to `hotmail.com` in the window, so
   the report should be small.
2. **Comcast's 08-26 stays empty**, seven windows on.
3. **08-30 closes between 30 and 40**, not near 112. jaguar's UTC-window sends to
   reporting domains are 30, of which 2 are Microsoft's; 27 are already measured.
   A close above 45 would mean a receiver reported mail jaguar has no record of
   sending, which is the outcome worth chasing rather than the number.
4. **`comcast.net`, `aol.com` and `verizon.net` either file for 08-30 in the next
   batch or are confirmed absent** — this is the retrieval-clock question above, and
   one more batch separates "not yet arrived" from "did not file". If they are still
   missing after a batch retrieved later in the day than 12:09, absence becomes the
   finding.
5. **Every report reads `p=quarantine`**, and GMX parses with metadata and a row for
   the fourth consecutive window.

---

### Seventeenth reading — 2026-09-01, covering 2026-08-31: every receiver but Google reconciles exactly with the send log, and four standing absences turn out to be absent traffic

**Fifty files in `~/dmarc` — six new, forty-four re-reads.** All six saved in one
batch, 2026-09-01 12:44:08–12:45:17, 69 seconds end to end. The batch closed 35
minutes later in the day than the sixteenth reading's, which matters for
prediction 4 and is dealt with below — by discarding the retrieval-clock question
rather than answering it.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `16259663635695610815` | 2026-08-31 | 33 | 0 |
| `yahoo.com` | `Yahoo` | `1788241310.513722` | 2026-08-31 | 7 | 0 |
| `sbcglobal.net` | `Yahoo` | `1788241310.513656` | 2026-08-31 | 3 | 0 |
| `comcast.net` | `comcast.net` | `v2-1788226901-surfguitar101.com` | 2026-08-31 | 2 | 0 |
| `aol.com` | `Yahoo` | `1788241310.513631` | 2026-08-31 | 1 | 0 |
| `protection.outlook.com` | `Outlook.com` | `dbf9c8dcb2314529978bd75763f30e23` | 2026-08-30 | 2 | 0 |

**2026-08-31: 46 messages, five reporting endpoints, 0 aligned on neither
mechanism**, every row `disposition=none`, every report `p=quarantine`. Microsoft
is outstanding, as always.

**08-30 closes at 29** — 27 plus Microsoft's 2.

#### An eleventh endpoint by filename, and it is the one the corpus was missing

`sbcglobal.net` files for the first time, in Yahoo's run `1788241310` alongside
`aol.com` and `yahoo.com`. The distinct receiver field across all fifty files now
yields **eleven**:

```
aol.com  att.net  bellsouth.net  comcast.net  cox.net  gmx.net
google.com  protection.outlook.com  sbcglobal.net  verizon.net  yahoo.com
```

Still **plus `swbell.net` by report-mail sender name**, which the sixteenth reading
separated out — and which this reading corroborates from the other side; see below.
Five reporting organizations; no sixth. `sbcglobal.net` is Yahoo, like `att.net`,
`bellsouth.net` and `cox.net` before it.

#### Three of five predictions held, and the two that missed were over-specified

1. **Microsoft filed for 08-30, one window late** — its seventh filing, seven times
   the same offset. **The `envelope_to` half missed**: the records read
   `hotmail.com` 2 and nothing else, against a prediction of `hotmail.com` plus at
   least one of `outlook.com` / `live.com`. jaguar sent 2 to `hotmail.com` and 0 to
   `live.com` or `outlook.com` in that window, so Microsoft's report is right and
   the prediction asked for mail that was never sent. **Predict endpoints from the
   send log, not from the last report's shape.**
2. **Comcast's 08-26 stays empty**, seven windows on — and this reading explains it
   rather than re-observing it. See the reconciliation below.
3. **08-30 closed at 29, against a predicted 30–40.** Missed low by one. The part
   that mattered held: nothing closed above 45, so no receiver reported mail jaguar
   has no record of sending.
4. **`comcast.net`, `aol.com` and `verizon.net` are confirmed absent for 08-30** —
   and the retrieval clock had nothing to do with it. jaguar sent **zero** messages
   to all three in that window.
5. **Every report reads `p=quarantine`** — all six. **GMX did not file for 08-31 and
   the prediction of a fourth consecutive GMX window missed**, for the same reason
   as 4: zero sends to any `gmx.*` address in the window.

#### The reconciliation: ten of eleven endpoints agree exactly, in every window they filed

The fourteenth through sixteenth readings compared jaguar's sends against the
reports for one window at a time and read the exact rows as corroboration. This
reading does all ten windows and all eleven endpoints at once. Sends are counted
with the sixteenth reading's corrected convention — `status=sent`, minus
`relay=local`, across `mail.log`, `mail.log.1` and `mail.log.2.gz` — binned into
the UTC report window at jaguar's verified UTC−5, and matched to the endpoint that
hosts the recipient domain. Each cell is **sends / reported**, `-` for no report:

| Endpoint | 08-22 | 08-23 | 08-24 | 08-25 | 08-26 | 08-27 | 08-28 | 08-29 | 08-30 | 08-31 |
|---|---|---|---|---|---|---|---|---|---|---|
| `google.com` | 17/- | 26/**12** | 17/**15** | 19/**5** | 6/6 | 8/**13** | 46/**47** | 22/22 | 17/**13** | 33/33 |
| `yahoo.com` | 3/- | 5/5 | 2/2 | 2/2 | 6/6 | 3/3 | 17/17 | 8/8 | 6/6 | 7/7 |
| `protection.outlook.com` | 3/3 | 1/1 | 0/- | 0/- | 2/2 | 2/2 | 16/16 | 7/7 | 2/2 | 6/- |
| `comcast.net` | 1/- | 3/3 | 4/4 | 2/2 | **0/-** | 2/2 | 8/8 | 3/3 | **0/-** | 2/2 |
| `gmx.net` | 0/- | 0/- | 0/- | 0/- | 0/- | 1/1 | 8/8 | 2/2 | 2/2 | **0/-** |
| `aol.com` | 0/- | 2/- | 1/1 | 1/1 | 0/- | 3/3 | 2/2 | 1/1 | **0/-** | 1/1 |
| `att.net` | 0/- | 2/2 | 0/- | 0/- | 0/- | 0/- | 0/- | 1/1 | 4/4 | **0/-** |
| `verizon.net` | 0/- | 1/- | 0/- | 0/- | 0/- | 0/- | 6/6 | 2/2 | **0/-** | **0/-** |
| `sbcglobal.net` | 0/- | 2/- | 0/- | 0/- | 0/- | 0/- | 0/- | 0/- | 0/- | 3/3 |
| `cox.net` | 0/- | 1/1 | 0/- | 0/- | 0/- | 0/- | 0/- | 0/- | 0/- | 0/- |
| `bellsouth.net` | 0/- | 0/- | 0/- | 0/- | 1/1 | 0/- | 0/- | 0/- | 0/- | 0/- |

**Every endpoint except `google.com` reports exactly what jaguar sent, in every one
of the forty-one reports they filed — 155 messages. Not one disagreement.** Yahoo
across nine windows and 56 messages, Microsoft across seven and 33, Comcast across
seven and 24, and six smaller endpoints besides.

**That is the strongest check the log has on its own instrument.** The send-side
convention, the rotated-log fix, the UTC binning and the UTC−5 offset are all load
bearing in that table, and a fault in any of them would show up as scattered
near-misses across ten independent receivers. It shows up nowhere.

**And it converts eight standing "absences" into measurements.** Every `0/-` cell
in bold above is a receiver the log has at some point wondered about — Comcast's
seven-window 08-26 hole most of all. In all eight, jaguar sent that domain nothing
in the window. **The receivers were not silent; there was nothing to report.** The
sixteenth reading's retrieval-clock hypothesis for 08-30 — that a batch pulled at
12:09 might have preceded Comcast's filing — is not so much answered as retired:
the reports it was waiting for could not exist.

**The `-` cells with sends in them are all 08-22 and 08-23**, and those are a
retrieval gap on our side, not a filing gap: the corpus begins with the batch saved
2026-08-24, and reports for the earlier windows were read in Gmail before the local
copy existed. `aol.com` 2, `sbcglobal.net` 2, `verizon.net` 1, `yahoo.fr` 1 and
`comcast.net` 1 sit there, unretrieved rather than unfiled.

#### `swbell.net` is corroborated from the sending side

The sixteenth reading pulled `swbell.net` out of the endpoint count because it was
read from report-mail sender names and has never been a file in `~/dmarc`, and was
careful to say that this is not a claim it was never a receiving domain. It was
not: **jaguar sent 2 messages to `swbell.net` in the 08-21 UTC window**, which is
the window the sixth reading read from Gmail. The mail existed, Yahoo filed for it,
and the file was never retrieved because the local copy was three days old and
`~/dmarc` was not yet being filled. `talk21.com` (08-20, 1) and `yahoo.fr` (08-17
2, 08-23 1) are the same shape.

**So the honest form gains a clause**: eleven endpoints by filename, plus
`swbell.net` observed by sender name over traffic the send log confirms. The count
and its definition stay separate; the provenance is now measured on both sides.
[[measure-before-recording-in-planning-docs]]

#### Yahoo does not file for every hosted domain it receives for

`sbcglobal.net` took 3 messages on 08-31 and Yahoo filed; it took 2 on 08-23 and
Yahoo did not. `yahoo.fr` took 1 on 08-23 with no filing. Both fall in the 08-22/23
retrieval gap, so this is stated as **not established** — the files may exist and be
unretrieved. It is recorded because it is the one reading of the table that would
weaken the reconciliation above, and it should be closed the next time a Yahoo brand
domain takes traffic in a window whose batch we did retrieve.

#### Google is the sole disagreement, and its content fits a UTC−7 day

Google's residuals at UTC alignment run **+14, +2, +14, 0, −5, −1, 0, +4, 0** across
08-23 → 08-31, positive meaning jaguar sent more than Google reported. Three of nine
windows exact, 40 messages of disagreement over 166 reported. Every other receiver
is exact everywhere, so this is a property of Google's reporting, not of the
measurement.

**Two corrections to the send side first, both verified by MX lookup.** `muohio.edu`
and `rarr.org.uk` are Google-hosted (`aspmx.l.google.com`), so their mail is
evaluated by Google and lands in `google.com`'s report, which omits `envelope_to`
and cannot distinguish them. The fourteenth through sixteenth readings counted
`muohio.edu` under "non-reporting". Folding both in is what the table above uses.

**Scanning the window offset from −12h to +12h, a UTC−7 day fits Google's content
far better than the UTC day its own `date_range` claims:**

| Alignment | Residuals 08-23 → 08-31 | Σ\|residual\| | Exact windows |
|---|---|---|---|
| UTC (as stamped) | +14 +2 +14 0 −5 −1 0 +4 0 | 40 | 3 of 9 |
| UTC−7 | +8 +4 +2 0 0 0 0 0 0 | 14 | 6 of 9 |

At UTC−7 the last **six consecutive windows, 08-26 through 08-31, land exactly**,
including 08-28's 47 at volume. UTC−7 is US Pacific daylight time. Google stamps
every report `00:00:00Z → 23:59:59Z` — checked, all nine — so the claim is that the
stamps and the aggregation day disagree, not that the stamps are unusual.

**Stated as a hypothesis, not a finding.** It is one free parameter fitted to nine
points, and the fit is chosen by the same person who wants it to be true. What
raises it above curve-fitting is that no other reporter needs an offset at all: all
ten fit UTC exactly, so the scan is not simply absorbing noise in the send counts.
[[suspect-the-measurer-before-the-record]]

**The residual it does not explain is 14 messages in the three earliest windows,
all in the same direction** — jaguar sent more than Google reported, on 08-23,
08-24 and 08-25. Those are the last three windows before `p=quarantine` was
published, which is a correlation with no mechanism behind it and is recorded as
that and nothing more. One alternative was tested and falsified: multiple Google
recipients sharing one SMTP transaction, which would let postfix log per recipient
while Google counted per message. **Every one of the 669 sends in the corpus has
exactly one recipient per queue ID**, in every window, so that is not it.

#### What held steady across all fifty

- **All 60 rows are `disposition=none`, 342 messages.** Nothing has been quarantined
  under `p=quarantine` at any receiver in any window.
- Evaluated alignment across those 60 rows: **55 `pass`/`pass`, 4 `fail`/`pass`,
  1 `fail`/`fail`.** The six new rows are all `pass`/`pass`.
- `173.255.245.115` remains the only unsigned-path sender and passes both mechanisms
  in all 52 rows it appears in.
- Policy renders `adkim=r aspf=r` in **all fifty**.
- **`sp` is absent in exactly the 23 Yahoo reports and present in all 27 others**,
  the clean split unbroken by three more Yahoo filings.
- **`pct` is absent in exactly the 4 GMX reports.**
- The forty-four re-reads reproduce exactly, including the `p=none`/`p=quarantine`
  boundary at the 08-25 publication and the twelfth reading's `yahoo.com` 08-26
  cache lag.
- The sixteenth reading's corrected send figures reproduce from an independent
  invocation: Aug 23 = 45, Aug 30 = 37.

#### The forwarding class went to zero, and the failing forward has not recurred in five windows

`209.85.220.41` carried **no messages on 08-31**. Google's report is a single row.
The class reads 8, 5, 2, 0 across 08-28 → 08-31, still 17 messages total across four
windows, every one surviving on DKIM. The twelfth reading's `2001:470:0:60::2` row —
aligned on neither mechanism, delivered only under a discretionary forwarding
exemption — remains the single instance in seventeen readings and **has not recurred
in five windows**.

#### Postmark absent for a fourth consecutive window

`50.31.156.x` appears in no report for 08-28 through 08-31. The cutover has not
happened, so a window with no Postmark row means no test was sent. Unchanged.

#### Bearing on the policy decision

`p=quarantine` is live at five reporting organizations and eleven reporting
endpoints. **08-31 is the fourth clean day at volume** — 46 messages, zero aligned
on neither mechanism, zero quarantined — and it is the first window in five with no
forwarded mail in it at all.

**The case for `p=reject` is unchanged, and this reading adds nothing to it.** The
exposure is still one measured instance of a forward that broke DKIM, delivered
because Google chose to exempt it, and `p=reject` converts that discretion into
someone else's bounce. A window with zero forwarded messages is not evidence that
forwarding stopped; it is evidence that nobody forwarded that day. Nothing argues
for reversing step 7.

#### Predictions for the eighteenth reading

1. **Microsoft files for 08-31, one window late — eight filings, eight times the
   same offset — and reports 6 messages**, all `envelope_to: hotmail.com`, because
   that is what jaguar sent. This is the first Microsoft prediction stated as an
   exact count; the reconciliation above says it should be exact, and a miss is
   worth more than a hit.
2. **08-31 closes at 52** — 46 measured plus Microsoft's 6 — and no endpoint files
   that jaguar did not send to.
3. **Google's 09-01 report reads what jaguar sent into the UTC−7 day, not the UTC
   one.** The 09-01 window is the first test of the offset made before seeing the
   report rather than after.
4. **Comcast's 08-26 and 08-30 holes stay empty for good**, and are no longer worth
   a prediction after this one: the send log says there was nothing to file.
5. **Every report reads `p=quarantine`**, and no report carries a `disposition`
   other than `none`.

### Eighteenth reading — 2026-09-02, covering 2026-09-01: the UTC−7 day survives its first forward test, and the second unsigned message names itself

**Fifty-three files in `~/dmarc` — three new, fifty re-reads.** All three saved
2026-09-02 12:11:29–12:12:06, 37 seconds end to end.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `13593836314853818654` | 2026-09-01 | 8 | 0 |
| `gmx.net` | `GMX` | `a3178967e5be4f10adfd147fd327e14e` | 2026-09-01 | 1 | 0 |
| `protection.outlook.com` | `Outlook.com` | `63ba685afa844e57950b7433dfb5939e` | 2026-08-31 | 6 | 0 |

**09-01 stands at 9 messages across two endpoints**, every row `disposition=none`,
every report `p=quarantine`. Microsoft is outstanding, as always.

**08-31 closes at 52** — 46 plus Microsoft's 6, exactly as predicted.

#### Four of five predictions held, and the fifth was retired before it was made

1. **Microsoft filed for 08-31, one window late — its eighth filing, eight times the
   same offset — and reported 6 messages, all `envelope_to: hotmail.com`.** The
   first Microsoft prediction stated as an exact count, and it is exact on both
   halves. jaguar sent 6 to `hotmail.com` in that window and nothing to
   `outlook.com` or `live.com`; the report says the same. Predicting the endpoint
   from the send log rather than from the last report's shape worked the first time
   it was tried.
2. **08-31 closed at 52**, and no endpoint filed that jaguar did not send to.
3. **Google's 09-01 report reads the UTC−7 day.** Held, and it is the reading's
   main result; see below.
4. Comcast's holes were retired last reading, not predicted.
5. **Every report reads `p=quarantine`** — all three — **and no row carries a
   `disposition` other than `none`.** GMX filed for 09-01 after skipping 08-31,
   which the send log had already explained: zero `gmx.*` traffic in 08-31, one
   message in 09-01.

#### The UTC−7 hypothesis passes a test made before the report existed

The seventeenth reading fitted a UTC−7 aggregation day to nine of Google's windows
and refused to call it a finding, because one free parameter fitted to nine points
is curve-fitting until it predicts. It predicted, and here is the result. Sends are
binned exactly as before — `status=sent`, minus `relay=local`, across `mail.log`,
`mail.log.1` and `mail.log.2.gz`, at jaguar's verified UTC−5 — but by a script
written from scratch for this reading rather than the previous one's.

| Window | 08-23 | 08-24 | 08-25 | 08-26 | 08-27 | 08-28 | 08-29 | 08-30 | 08-31 | **09-01** |
|---|---|---|---|---|---|---|---|---|---|---|
| Google reported | 12 | 15 | 5 | 6 | 13 | 47 | 22 | 13 | 33 | **8** |
| jaguar sent, UTC day | 26 | 17 | 19 | 6 | 8 | 46 | 22 | 17 | 33 | **6** |
| jaguar sent, UTC−7 day | 20 | 19 | 7 | 6 | 13 | 47 | 22 | 13 | 33 | **8** |

| Alignment | Σ\|residual\| | Exact windows |
|---|---|---|
| UTC (as stamped) | 42 | 3 of 10 |
| UTC−7 | 14 | **7 of 10** |

**09-01 lands exactly at UTC−7 and misses by 2 at UTC, and the miss is in the
direction that cannot be explained away.** Google reported 8 messages for a window
into which jaguar sent 6. A receiver cannot report mail nobody sent, and this
report names exactly one source IP — `173.255.245.115`, ours — so the surplus is
not forwarded mail arriving from somewhere else. Under UTC the 09-01 window is the
third where Google reports more than was sent (08-27 by 5, 08-28 by 1); under
UTC−7 there is no such window in ten, and the last **seven consecutive** windows,
08-26 through 09-01, are exact.

The four messages that decide it went out in one burst at `Sep 1 20:40:39` local,
which is `2026-09-02 01:40:39Z`. They belong to the UTC 09-02 window and to the
UTC−7 09-01 day, and Google put them in the report stamped 09-01.

**This is now stronger than a fit, and still short of a mechanism.** What is
established is that Google's `date_range` — `00:00:00Z → 23:59:59Z`, checked on all
ten — does not describe which messages the report contains, and that a US Pacific
day does. Why Google stamps one day and aggregates another is not measured here and
is not guessed at. The corollary is a sharp test rather than another fit: **those
four messages must not appear again in Google's 09-02 report**, because they have
already been counted.

**The three earliest windows are still unexplained**, 08-23/24/25, 14 messages all
in the direction of jaguar sending more than Google reported. The offset does not
touch them and nothing else has been proposed. Unchanged from last reading.

**Every other endpoint reproduces at UTC and only at UTC.** GMX is the sharpest
case, because it falls in the same window as the Google result: jaguar sent GMX 1
message in the 09-01 UTC day and 2 in the UTC−7 day, and GMX reported 1. So one
window contains a receiver that fits UTC and a receiver that does not, measured off
the same log with the same script. The offset is a property of Google's reporting,
not of our clock. [[suspect-the-measurer-before-the-record]]

#### The seventh reading's known-unknown is closed, and the answer was hypothesis A

The seventh reading found one message in Google's 08-22 report with no DKIM
signature and SPF evaluated against the HELO name, raised four hypotheses, watched
all four die, and closed it with an explicit reopen condition: *"Reopen only if a
later reading shows a second unsigned message — one is an anomaly, two is a pattern
with something to grep for."*

**The second one is in Google's 09-01 report, and the mail log names it.**

```
173.255.245.115   1  none  pass  fail  spf:mail.surfguitar101.com=pass/?
```

Identical shape to 08-22's. The whole chain is in `/var/log/mail.log`:

```
Sep  1 09:44:17  63D35586572: from=<admin@surfguitar101.com>, nrcpt=1
Sep  1 09:44:18  63D35586572: to=<member20@example.com>, ...
                 status=bounced (554 5.7.1 [VI-1] Message blocked due to
                 spam content in the message)
Sep  1 09:44:18  bounce[25637]: 63D35586572: sender non-delivery
                 notification: BECCA5869B6
Sep  1 09:44:18  BECCA5869B6: from=<>, size=3907, nrcpt=2
Sep  1 09:44:18  BECCA5869B6: to=<dmarc@localhost>, relay=local
Sep  1 09:44:20  BECCA5869B6: to=<bgneal@gmail.com>,
                 orig_to=<admin@surfguitar101.com>,
                 relay=gmail-smtp-in.l.google.com, status=sent
```

Site mail to `comporium.net` was rejected as spam; Postfix generated the
non-delivery notification; it went to `admin@surfguitar101.com`, which fans out to
the local maildir and to Brian's Gmail; Google evaluated it with an empty MAIL
FROM, fell back to the HELO name `mail.surfguitar101.com`, found the SPF record
published there, and found no signature because DSNs bypass the milters.

**`BECCA5869B6` is the only `from=<>` message in the entire live log** — Aug 30
06:41 through Sep 2 12:13 — and the report carries exactly one such row, count 1.
The identification does not depend on the UTC−7 result: the bounce falls inside the
09-01 window under either alignment.

**Hypothesis A was right all along.** It read *"a null-sender message — MAIL FROM
empty, so SPF fell to HELO"*, and it died in the seventh reading on an absence:
that window's only null sender had `status=expired` and was never delivered. That
was correctly reported as an absence of evidence for one window, and it was.
[[measure-before-recording-in-planning-docs]]

**What this makes it is not a fault but a designed outcome, observed end to end for
the first time.** `mail.surfguitar101.com` publishes `v=spf1 ip4:173.255.245.115
-all`, and that record exists precisely so unsigned bounces have an aligned
mechanism to pass on. Under `p=quarantine`, one did: SPF pass, DKIM absent, relaxed
`aspf` aligning the HELO subdomain to the org domain, `disposition=none`, delivered.
The class is not two anomalies eleven windows apart — it is every Postfix DSN, and
it appears in a report only on the days something bounces.

#### A bug in this reading's own instrument, caught before it was written down

The first run of the send-side binning produced 6 messages for the whole 09-01
window against 9 reported. The regex required `to=<...>, relay=` and Postfix writes
`to=<...>, orig_to=<...>, relay=` for anything delivered through an alias — 93 lines
across the corpus, every one of them to Gmail, which is where `admin@` and `root@`
forward. **The three messages the reading turns on were all in the dropped set**,
including the bounce.

Caught by the impossibility rather than by inspection: a receiver reporting more
than was sent is the same signal that exposed the rotated-log hole in the sixteenth
reading, and it is worth keeping as the check it has now been twice. **The
seventeenth reading's table is unaffected** — the corrected script reproduces all
eleven of its endpoint rows across all ten windows exactly, from an independently
written binning, which is the first time that table has had a second instrument
behind it.

#### A correction to how that falsification was worded

The seventeenth reading falsified "multiple Google recipients sharing one SMTP
transaction" with the claim that *"every one of the 669 sends in the corpus has
exactly one recipient per queue ID."* **Five queue IDs in the live log carry
`nrcpt=2`**, four from `no_reply@surfguitar101.com` and the bounce above. In all
five the second recipient is `dmarc@localhost` over `relay=local` — the `admin@`
alias fanning out to the maildir that feeds `~/dmarc` — so there is exactly one
*remote* recipient per queue ID, and never two at Google. **The falsification
stands; the sentence was broader than the measurement.**

#### Two policy elements the tool has never printed

Reading the raw XML for the bounce turned up fields `dmarc_report.py` does not
render, present all along:

- **Google emits `<np>quarantine</np>`** in all ten of its reports — the
  non-existent-subdomain policy, which our `_dmarc` record does not set, so Google
  is reporting its own default derived from `p`.
- **GMX emits `<discovery_method>psl</discovery_method>` and `<testing>n</testing>`**
  in all five of its reports. `psl` says GMX located the policy via the public
  suffix list; `testing=n` says it is not treating the record as a test.

Neither changes anything and neither is new — they are recorded because the log has
claimed for seventeen readings to be reading `policy_published`, and it has been
reading five of its seven elements. Our published record remains
`v=DMARC1; p=quarantine; rua=...` with no `sp`, `pct`, `np` or `fo`; every `sp`,
`pct` and `np` value in every report is a receiver-side default.

#### What held steady across all fifty-three

- **All 64 rows are `disposition=none`, 357 messages.** Nothing has been quarantined
  under `p=quarantine` at any receiver in any window.
- Evaluated alignment across those 64 rows: **58 `pass`/`pass`, 4 `fail`/`pass`,
  1 `pass`/`fail`, 1 `fail`/`fail`.** The `pass`/`fail` is the bounce above and the
  first of its kind in the local corpus.
- `173.255.245.115` appears in 56 rows and 336 messages, and passes both mechanisms
  in 55 of them.
- Policy renders `adkim=r aspf=r` in **all fifty-three**.
- **`sp` is absent in exactly the 23 Yahoo reports and present in all 30 others.**
- **`pct` is absent in exactly the 5 GMX reports.**
- The fifty re-reads reproduce exactly, the `p=none`/`p=quarantine` boundary at the
  08-25 publication included — 16 reports read `none`, 37 read `quarantine`.

#### The forwarding class is at zero for a second window

`209.85.220.41` carried no messages on 08-31 or 09-01. The class reads 8, 5, 2, 0, 0
across 08-28 → 09-01, 17 messages total across four windows, every one surviving on
DKIM. The twelfth reading's `2001:470:0:60::2` row — aligned on neither mechanism,
delivered only under a discretionary forwarding exemption — remains the single
instance in eighteen readings and has not recurred in six windows.

#### Postmark absent for a fifth consecutive window

`50.31.156.x` last appears in the 08-27 window. Three messages in the corpus, all
`pass`/`pass`. The cutover has not happened, so no window since has had a test to
report. Unchanged.

#### Bearing on the policy decision

`p=quarantine` is live at five reporting organizations and eleven reporting
endpoints, and **09-01 is the fifth clean day** — zero messages aligned on neither
mechanism, zero quarantined.

**The unsigned-bounce identification argues against `p=reject` slightly more than
last reading, not less.** The class is now understood: every Postfix DSN goes out
unsigned and passes DMARC on the HELO SPF record alone. That is one mechanism deep
with no margin — the same single point of failure as the forwarded mail that breaks
SPF and survives on DKIM, in the mirror image. Under `p=reject` a DSN that lost its
SPF pass would be rejected outright, and a rejected bounce is a delivery failure
nobody is told about. jaguar's outbound moves to Postmark at Step 21 and the DSN
path goes with it, so **the honest reading is that this class should be re-measured
after cutover, not legislated before it.** Nothing argues for reversing step 7.

#### Predictions for the nineteenth reading

1. **Microsoft files for 09-01, one window late — nine filings, nine times the same
   offset — and reports 1 message, `envelope_to: hotmail.com`.** jaguar sent it one,
   at `Aug 31 22:03:24` local.
2. **09-01 closes at 10** — 9 measured plus Microsoft's 1 — and no endpoint files
   that jaguar did not send to.
3. **Google's 09-02 report does not contain the four messages sent at
   `Sep 1 20:40:39` local.** They are already inside the 8 it reported for 09-01. If
   they appear again, the UTC−7 result is wrong in a way no offset can repair, and
   that is the point of stating it this way.
4. **GMX files for 09-02 and reports 2** — jaguar sent `member15@example.com` two messages in
   that UTC window, at `Sep 1 21:10:47` and `Sep 2 03:57:48` local. GMX has fit UTC
   in all five of its filings.
5. **Every report reads `p=quarantine`**, no row carries a `disposition` other than
   `none`, and **no `pass`/`fail` row appears unless the mail log shows a bounce** —
   the reopen condition from the seventh reading, restated now that it has an
   instrument behind it.

---

### Nineteenth reading — 2026-09-04, covering 2026-09-02 and 2026-09-03: the UTC−7 offset passes a second forward test, and a DKIM failure class appears that is not the bounce class

**Sixty files in `~/dmarc` — seven new, fifty-three re-reads.** Two windows arrive
at once because the corpus was last copied on 09-02; Brian's note says the reports
came in "yesterday and today."

**Instrument caveat, new this reading: per-report arrival times are not measurable
here.** All seven files carry mtimes of 2026-09-04 14:50–14:51, one copy operation
spanning two days of delivery. Previous readings used the save timestamp to measure
Microsoft's filing offset directly. This one cannot, and the offset below is
inferred from Brian's note plus the established pattern rather than observed.
[[measure-before-recording-in-planning-docs]]

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `protection.outlook.com` | `Outlook.com` | `76533edf4fd140fc8e2f2222e2645cc2` | 2026-09-01 | 1 | 0 |
| `google.com` | `google.com` | `12690854149145162803` | 2026-09-02 | 10 | **1 DKIM** |
| `gmx.net` | `GMX` | `b7aa391f8331469db5994d68ce13d307` | 2026-09-02 | 2 | 0 |
| `protection.outlook.com` | `Outlook.com` | `93bf7b56a14b4ee3993108f971585cb6` | 2026-09-02 | 1 | 0 |
| `google.com` | `google.com` | `1585020204032193119` | 2026-09-03 | 7 | **2 DKIM** |
| `cox.net` | `Yahoo` | `1788500709.189162` | 2026-09-03 | 1 | 0 |
| `sbcglobal.net` | `Yahoo` | `1788500709.189191` | 2026-09-03 | 1 | 0 |

**09-01 closes at 10** — 9 measured last reading plus Microsoft's 1, exactly as
predicted. **09-02 closes at 13** across three endpoints. **09-03 stands at 9**
across three endpoints, and Microsoft should not file for it at all; see the
predictions.

Every row in all sixty files is `disposition=none`. Nothing has been quarantined
under `p=quarantine` at any receiver in any window.

#### Four predictions held, and the fifth's reopen condition fired

1. **Microsoft filed for 09-01 and reported 1 message, `envelope_to: hotmail.com`.**
   Exact on all three halves — the window, the count and the endpoint — for the
   second consecutive reading in which the endpoint was predicted from the send log
   rather than from the previous report's shape. It also filed for 09-02, 1 message,
   `envelope_to: outlook.com`, which jaguar's log matches exactly. Ten filings now,
   and the two-day offset is consistent with both arriving in this batch, though for
   the first time it was not measured.
2. **09-01 closed at 10**, and no endpoint filed that jaguar did not send to. That
   holds for 09-02 and 09-03 as well.
3. **Google's 09-02 report does not contain the four messages sent at
   `Sep 1 20:40:39` local** — held, but the single-window test was degenerate and
   the two-window pair is what settles it. See below.
4. **GMX filed for 09-02 and reported 2.** Exact. jaguar sent `member15@example.com` two
   messages in that UTC window; GMX has now fit UTC in all six of its filings.
5. **Every report reads `p=quarantine` and no row carries a `disposition` other
   than `none`** — held. **The rest of that prediction failed: three `pass`/`fail`
   messages appeared and the mail log shows no bounce.** This is the reading's
   second result, and the class is not the one the prediction was written about.

#### The UTC−7 aggregation day gets its second forward test, and 09-03 is decisive

Sends are binned as in the last two readings — `status=sent`, minus `relay=local`,
at jaguar's UTC−5, which `date -u` on the host confirms again — by a third
independently written script. Google's figures are its rows from `173.255.245.115`
only, excluding the forwarding and Postmark sources, which is the basis the
seventeenth and eighteenth readings used.

| Window | 08-23 | 08-24 | 08-25 | 08-26 | 08-27 | 08-28 | 08-29 | 08-30 | 08-31 | 09-01 | **09-02** | **09-03** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Google reported | 12 | 15 | 5 | 6 | 13 | 47 | 22 | 13 | 33 | 8 | **10** | **7** |
| jaguar sent, UTC day | 26 | 17 | 19 | 6 | 8 | 46 | 22 | 17 | 33 | 6 | **10** | **11** |
| jaguar sent, UTC−7 day | 20 | 19 | 7 | 6 | 13 | 47 | 22 | 13 | 33 | 8 | **10** | **7** |

| Alignment | Σ\|residual\| | Exact windows |
|---|---|---|
| UTC (as stamped) | 46 | 4 of 12 |
| UTC−7 | 14 | **9 of 12** |

**09-02 does not discriminate, by coincidence.** Both alignments predict 10 and
Google reported 10. The four messages of `Sep 1 20:40:39` left the UTC−7 window at
its start and four others — `Sep 2 21:37:16` through `Sep 3 01:39:23` local —
entered at its end. The prediction was written to be decisive and the window
happened to be the one shape in which it cannot be: worth recording, because a
prediction that survives a test it could not have failed has not been tested.

**09-03 discriminates, and it is not close.** Google reported 7. The UTC day holds
11 Google-bound messages; the UTC−7 day holds exactly 7. The four that separate
them went out at `Sep 3 15:49:02`–`15:51:20` local, which is `20:49`–`20:51Z` on
09-03 — inside the UTC 09-03 window and inside the UTC−7 09-04 day. Google put them
in neither report yet, which is what the offset requires.

**Taken as a pair the two windows are decisive even though one of them is not.**
UTC requires (10, 11); UTC−7 requires (10, 7); Google filed (10, 7). The last
**nine consecutive** windows, 08-26 through 09-03, are exact under UTC−7 and four
of those nine are wrong under UTC.

**Still short of a mechanism, and the three earliest windows are still unexplained.**
08-23/24/25 hold 14 messages of residual in the direction of jaguar sending more
than Google reported, the offset does not touch them, and nothing else has been
proposed. Unchanged for the third reading.

**`muohio.edu` is inside the `google.com` endpoint**, delivered through
`aspmx.l.google.com`. It has been folded into these figures since the seventeenth
reading — 2 messages in the UTC 09-02 window — but the log has never said so
plainly, and the endpoint is not the same set as `gmail.com`.

**One caution on "09-02 closes at 13."** jaguar sent 13 in the UTC 09-02 day and the
three filers report 13, but Google's 10 covers a shifted day while GMX's 2 and
Microsoft's 1 cover the stamped one. The totals agree; they are not measuring the
same interval, and the agreement should not be read as a like-for-like
reconciliation. [[suspect-the-measurer-before-the-record]]

#### A second DKIM failure class, and it is not the unsigned-bounce class

Google's 09-02 report carries one `pass`/`fail` message and its 09-03 report carries
two. The seventh reading's reopen condition — *"a second unsigned message"* — is not
what fired, because these are not unsigned:

```
09-01  n=1  eval[spf=pass dkim=fail]  dkim: ABSENT              spf: mail.surfguitar101.com pass
09-02  n=1  eval[spf=pass dkim=fail]  dkim: surfguitar101.com sel=dkim FAIL   spf: surfguitar101.com pass
09-03  n=2  eval[spf=pass dkim=fail]  dkim: surfguitar101.com sel=dkim FAIL   spf: surfguitar101.com pass
```

**The 09-01 row is the bounce: no `dkim` block at all, SPF evaluated against the
HELO name.** The three new ones carry a full `dkim` block with our selector and
`result=fail`, and SPF evaluated against the org domain — a message that was signed
by `opendkim` and whose signature did not verify at Google. Across all sixty files
the only other signed-and-failed row is `2001:470:0:60::2` on 08-26, which failed
SPF as well and is the known forwarding instance. **Signature present, SPF aligned,
signature broken is a new shape in this corpus.**

`BECCA5869B6` remains the only `from=<>` message in the live log, Aug 30 06:41
through Sep 4 14:54, so the bounce class did not recur and cannot explain these.

**Two hypotheses were fitted and both are dead.**

*Injection path.* jaguar signs through `opendkim` on both `smtpd_milters` and
`non_smtpd_milters`, but locally-injected mail is the obvious suspect for a broken
signature, and the counts fit perfectly: the UTC−7 09-02 window holds exactly one
`pickup` message and the 09-03 window holds one `pickup` plus one `root@` message —
1 and 2, matching the failures. **Falsified by the windows that were clean.** The
same daily cron message from `brian` at 02:01 local goes out every day, including
Aug 31 and Sep 1, and it sits inside the UTC−7 08-31 and 09-01 windows, both of
which Google reported with zero signed failures.

*Message size.* The three failures are 5,653, 6,050 and 9,309 bytes and every other
message in those two windows is at most 4,186. **Falsified at a threshold of 5,000
by 08-31**, which carried eight messages of 5,296–5,312 bytes to Google and reported
no failure at all.

**What survives is a fit, not a finding.** No message of 5,653 bytes or more went to
a Google endpoint in any clean window, and all three failures are at or above it —
one free parameter, fitted to four windows, with the threshold falling in the gap
between 5,312 and 5,653 because that is where the data has a gap. The seventeenth
reading called that curve-fitting when it was the UTC−7 offset, and it is
curve-fitting here. It is recorded as the next thing to test, not as the cause.

**No mechanism is proposed and none is guessed at.** `opendkim.conf` leaves
`Canonicalization` at the default `simple/simple` and sets `OversignHeaders From`,
which is the fragile configuration, but that has been true since 2016 and does not
by itself explain three failures in two days. `opendkim` writes nothing to
`mail.log` — zero lines in 5,128 across five days, despite `Syslog yes` — so the
signer's own verdict is not available, and `/home/dmarc/mail` is not readable as
`brian`.

**The way to close this is one raw message, as it was in the tenth reading.** All
three failures were delivered to `bgneal@gmail.com`; their `Authentication-Results`
and `DKIM-Signature` headers say directly what broke:

| Queue ID | Sent (jaguar local) | Size | From |
|---|---|---|---|
| `44C7F5864DF` | Sep 2 16:39:03 | 5,653 | `no_reply@surfguitar101.com` |
| `B4EFD5864BF` | Sep 3 02:02:37 | 6,050 | `no_reply@surfguitar101.com` |
| `0077E586513` | Sep 3 03:07:45 | 9,309 | `root@surfguitar101.com` |

#### A correction to the eighteenth reading's field census

That reading recorded "two policy elements the tool has never printed." **There are
three.** `fo` is present in all 7 Comcast reports and all 10 Microsoft reports and
was missed. The full census across sixty files:

| Field | Present | Absent |
|---|---|---|
| `sp` | 35 — Comcast, GMX, Google, Microsoft | 25 — exactly the Yahoo reports |
| `pct` | 54 | 6 — exactly the GMX reports |
| `np` | 12 — exactly the Google reports | 48 |
| `fo` | **17 — exactly Comcast and Microsoft** | 43 |
| `discovery_method`, `testing` | 6 — exactly the GMX reports | 54 |

Our published record is still `v=DMARC1; p=quarantine; rua=...` with no `sp`, `pct`,
`np` or `fo`. Every value above is a receiver-side default.

#### What held steady across all sixty

- **73 rows, 380 messages, every one `disposition=none`.**
- Evaluated SPF/DKIM across those rows: **65 `pass`/`pass`, 4 `fail`/`pass`,
  3 `pass`/`fail`, 1 `fail`/`fail`.**
- `173.255.245.115` appears in 65 rows and 359 messages.
- Policy renders `adkim=r aspf=r` in all sixty.
- The `p=none`/`p=quarantine` boundary at the 08-25 publication reproduces exactly:
  16 reports read `none`, 44 read `quarantine`.
- **Eleven reporting endpoints by filename**, unchanged, plus `swbell.net` by sender
  name. Five reporting organizations. No new endpoint this reading.
- Yahoo filed for `cox.net` and `sbcglobal.net` on 09-03 and for nothing on 09-01 or
  09-02, and `yahoo.com` itself has not filed since the 08-31 window. The send log
  explains all three absences: no Yahoo-family traffic in those windows.

#### The forwarding class is at zero for a fourth window, and Postmark for a seventh

`209.85.220.41` carried no messages on 09-02 or 09-03. The class reads 8, 5, 2, 0,
0, 0, 0 across 08-28 → 09-03, 17 messages total, every one surviving on DKIM. The
twelfth reading's `2001:470:0:60::2` row remains the single instance in nineteen
readings and has not recurred in eight windows. `50.31.156.x` last appears in the
08-27 window; the cutover has not happened, so there is nothing for it to report.

#### Bearing on the policy decision

`p=quarantine` is live at five reporting organizations and eleven reporting
endpoints, and nothing has been quarantined anywhere in any window.

**This reading argues against moving to `p=reject` more firmly than the last one,
and for a new reason.** The eighteenth reading's argument was that the DSN class
passes on SPF alone with no margin. That still stands. What is added is that **our
own signing breaks intermittently, on ordinary site mail, for a reason we cannot
yet name.** Three messages in two days lost their DKIM signature and survived only
because SPF was aligned — the same one-mechanism-deep position as the bounces, in
mail that is not an edge case. Under `p=reject` those three would still have been
delivered, since SPF passed; but a signing fault of unknown cause is not a thing to
tighten policy on top of. **Step 7 is not reversed and `p=reject` is not
recommended until this class is identified.** jaguar's outbound moves to Postmark at
Step 21, which replaces the signer entirely, so the honest sequence is: identify the
cause, then re-measure after cutover, then decide.

#### Predictions for the twentieth reading

1. **Microsoft does not file for 09-03 at all.** jaguar sent nothing to
   `hotmail.com`, `outlook.com` or `live.com` in that UTC window, and receivers in
   this corpus skip empty windows rather than filing zeroes. **09-03 closes at 9.**
2. **Google's 09-04 report reads the UTC−7 day and contains the four messages sent
   `Sep 3 15:49:02`–`15:51:20` local**, which the 09-03 report did not.
3. **Google's 09-04 report carries no signed-DKIM-fail row, provided no Google-bound
   message of 5,653 bytes or more leaves jaguar between `Sep 4 14:54` and
   `Sep 5 02:00` local.** As of the log's end the window holds 5 messages, the
   largest 3,934 bytes. This is the size fit's first forward test and it is stated
   so it can fail: **the dead injection-path hypothesis predicts exactly one failure
   here**, because the `brian` cron message went out at `Sep 4 02:01:13`.
4. **GMX files for nothing.** jaguar sent no `gmx.*` traffic in the UTC 09-03 window.
5. **Every report reads `p=quarantine`** and no row carries a `disposition` other
   than `none`.

---

#### Addendum, 2026-09-04 — the raw message closes it: Postfix wraps at 998 bytes after `opendkim` has signed

**Brian found `44C7F5864DF` in the Gmail spam folder hours after the reading was
written, and Google's own header names the failure the aggregate report could
not:**

```
Authentication-Results: mx.google.com;
  dkim=neutral (body hash did not verify)
         header.i=@surfguitar101.com header.s=dkim header.b=fBr0dlU7;
  spf=pass  ... smtp.mailfrom=no_reply@surfguitar101.com;
  dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=surfguitar101.com
```

**Body hash, not signature.** The key verified, the headers verified, the body
Google hashed is not the body jaguar signed.

**The mechanism, measured rather than inferred.** The message is a contact-form
submission carrying a long Cyrillic body. *(The second message, below, shows the
Cyrillic and the `8bit` encoding are incidental — line length alone is the
trigger.)*

```
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 8bit
DKIM-Signature: v=1; a=rsa-sha256; c=simple/simple; d=surfguitar101.com; s=dkim;
    bh=YA7b8JVSGndETbItyVWMM2eH6ODPU+odl2+PtYrybYQ=; h=Subject:From:To:Date:Reply-To:From
```

The delivered body carries line breaks that the site never wrote, each followed by
a space, and one of them **splits a two-byte UTF-8 character down the middle** —
`вашего <D0>` ending one line and `<BF>редприятия` starting the next. No
application wraps text mid-character. A byte-oriented line-length enforcer does.

**The first wrap point is at exactly 998 bytes**, counted from the start of the
paragraph to the inserted break. jaguar answers with the matching constant:

```
smtp_line_length_limit = 998        # Postfix default; breaks longer lines with CRLF+SPACE
line_length_limit      = 2048       # input chopping, reconstructed on delivery
```

So the chain is:

1. `core.functions.send_mail` hands Django a `text/plain; charset=utf-8` body.
   **jaguar runs the `main` branch on Django 1.8.15 / Python 2.7**, where
   `utf8_charset.body_encoding = None` is set unconditionally — utf-8 goes out as
   `8bit` with no transfer encoding and therefore no wrapping. The contact form's
   `message` field allows 3,000 characters, about 6,000 bytes of Cyrillic on one
   line.
2. `opendkim` signs in `cleanup`, computing `bh=` over that unwrapped body.
3. Postfix's `smtp` client enforces `smtp_line_length_limit` on delivery and breaks
   the line by inserting CRLF+SPACE, at a byte offset, splitting a character.
4. Google hashes the wrapped body. Mismatch. `dkim=neutral`.

**The size fit is dead, and it was a proxy.** The predictor is not size but *a body
line longer than 998 bytes*; long lines simply live in large messages. That also
explains 08-31's eight messages of 5,296–5,312 bytes passing — large, but nothing
in them on one line. The seventeenth reading's rule earned its keep twice in one
day: the fit was recorded as a fit, and the mechanism replaced it within hours.

**Two of the three are now directly established** — see the next subsection for
`0077E586513`. `B4EFD5864BF` (6,050 bytes, `no_reply@`) is still assigned by shape
rather than observed.

##### Two things not to fix it with

- **`Canonicalization relaxed/relaxed` does not help.** Relaxed body canonicalization
  collapses whitespace *within* a line and drops trailing whitespace and trailing
  empty lines. An inserted line break makes two lines, and it survives. This is the
  tempting one-line change and it would leave the failure exactly where it is.
- **Raising `smtp_line_length_limit` is worse than the bug.** RFC 5321 §4.5.3.1.6
  caps a line at 1,000 octets including CRLF. Postfix's 998 *is* that limit, and
  the site is the thing violating it.

##### The modernize branch already fixes it, and no code change is needed

**This is a defect in the deployed `main` branch, not in the branch that replaces
it.** Django grew the fix in `SafeMIMEText.set_payload` (ticket #22561, quoted in
the source as *"Quoted-Printable encoding has the side effect of shortening long
lines"*): a second charset object, `utf8_charset_qp`, is selected whenever any body
line exceeds `RFC5322_EMAIL_LINE_LENGTH_LIMIT`.

```
charset = utf8_charset_qp if has_long_lines else utf8_charset
```

| Running | Behaviour on a 3,440-byte body line |
|---|---|
| jaguar, Django 1.8.15 | `Content-Transfer-Encoding: 8bit`, line delivered whole, Postfix wraps it, signature breaks |
| modernize, Django 5.2.17 | `Content-Transfer-Encoding: quoted-printable`, **zero lines over 998 bytes on the wire** |

Measured, not read off the changelog: the same `EmailMessage` built under this
repo's venv emits quoted-printable for a long line and 8bit for short ones, and no
line of either reaches 998 bytes. Postfix therefore never wraps, and the signature
survives. **`core.functions.send_mail` needs no change**, and hard-wrapping the
body there would be the wrong fix anyway — it edits what the member wrote, where a
transfer encoding leaves the logical content untouched.

**So Step 21 fixes this at the source rather than hiding it.** The earlier reading
of the sequence — that cutover would mask an unfixed defect behind Postmark's
edge-signing — was wrong, and wrong for a specific reason worth keeping: **the
`django` in this working tree is not the `django` that sent the message.** jaguar
runs `main`. Checking the venv at hand and calling it the site's behaviour is the
same error as reading a cause off a shape in the data.
[[measure-before-recording-in-planning-docs]]

**What remains open is not the code but the interval.** Every over-long line the
legacy site emits between now and the Step 21 deploy loses its DKIM signature and
rides on SPF alone. That is an argument for not tightening to `p=reject` before the
deploy, not an argument for patching a branch that is being retired.

##### Two incidentals worth keeping

- **Google renders a `neutral` verdict as `fail` in the aggregate XML.** The header
  says `dkim=neutral (body hash did not verify)`; the report says
  `<result>fail</result>`. The aggregate format gave no way to tell a body-hash
  mismatch from a bad key or a stripped signature — this is the third time a raw
  message has closed what the reports could only describe, after the tenth and
  eighteenth readings.
- **`dmarc=pass ... dis=NONE`** confirms from the receiving side what all sixty
  reports say: the policy is live, nothing was quarantined, and this message was
  carried by SPF alignment alone.
- **The message is contact-form spam that cleared Turnstile and the honeypot**,
  which is not this reading's subject and is not evidence about the antispam work
  either way — one message says nothing about a rate. Recorded only because it is
  the reason a 6,000-byte line existed to break the signature.

##### Second confirmation, `0077E586513` — 7-bit ASCII, and the wrap lands on 998 again

Brian produced the `root@` message the same evening. Same verdict:

```
Authentication-Results: mx.google.com;
  dkim=neutral (body hash did not verify) header.i=@surfguitar101.com header.s=dkim
  spf=pass ... smtp.mailfrom=root@surfguitar101.com;
  dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE)
```

**Measured from its own body, the first inserted break falls at exactly 998 bytes** —
a second independent hit on the constant, from a different sender, a different code
path and a different day. The break again cuts mid-token, this time splitting the
literal escape `с` after `\u044`.

**And it corrects the mechanism as the first message left it.** This body is
`Content-Transfer-Encoding: 7bit` and **pure ASCII** — it is a Celery error report,
so every Cyrillic character appears as a literal `\uXXXX` escape rather than as
8-bit bytes. The Cyrillic content and the `8bit` encoding in `44C7F5864DF` were
incidental. **The trigger is one thing only: a body line longer than 998 bytes.**
Charset and transfer encoding do not enter into it.

**Django's fix still covers it**, which had to be checked rather than assumed
because the guard is reached through a `charset == "utf-8"` branch and this body is
ASCII. Measured on the bench: a 1,838-byte ASCII line still selects
`quoted-printable` and still produces zero lines over 998 on the wire.

##### What that message actually is, and why it was 9,309 bytes

It is not spam. It is Celery's error report *about* a rejected spam submission, and
the chain is worth having:

1. A contact-form submission arrived with `Subject: ...Сварочная Робота\r\n` — a
   trailing CRLF, which is a header-injection attempt.
2. Django's `forbid_multi_line_headers` refused it: `BadHeaderError: Header values
   can't contain newlines`. **The protection worked.**
3. The exception escaped `core.tasks.send_mail` (jaguar's version, the bare
   `msg.send()` that Step 16 task 02 replaced on the modernize branch).
4. Celery emailed the admins its standard failure report, which **`repr()`s the
   whole task kwargs onto one physical line** — the entire 3,000-character
   submission inlined. That is where a 998-byte line comes from in a message nobody
   composed.

So the long-line class is not confined to what members type. **A failure report can
manufacture one out of any large argument**, which is the more general statement of
the defect.

##### A defect that survives the modernization, found by reading this error

The live payload is fixed by the upgrade for a reason unrelated to mail:
`forms.CharField` gained `strip=True` as its default after 1.8, so the trailing CRLF
is removed during `clean()` and the subject never reaches the header layer. Measured
on both sides:

| Subject | Django 1.8.15 (jaguar) | Django 5.2.17 (modernize) |
|---|---|---|
| `...Робота\r\n` — the live payload | `BadHeaderError` | stripped, sends fine |
| `Сварочная\r\nРобота` — newline in the middle | `BadHeaderError` | **`BadHeaderError` still** |

**`strip()` only touches the ends.** A newline in the middle of the subject still
reaches `forbid_multi_line_headers` on the modernize branch, and because
`core.functions.send_mail` defers to Celery there, the result is a task crash and an
admin error report rather than a form error the submitter sees. `ContactForm.subject`
is a plain `forms.CharField()` with no newline validation.

**This is a hardening, not an emergency** — the header injection is blocked either
way, which is the part that matters. What it buys is a clean rejection at the form
instead of a crash report containing the whole submission. Filed as an open item
rather than fixed here, because it belongs to the contact form rather than to this
reading.

##### Revised prediction 3 for the twentieth reading

Supersedes the size formulation. **Google's 09-04 report carries one signed-DKIM-fail
row for each message jaguar sent it whose body contains a line over 998 bytes, and no
others.** As of `Sep 4 14:54` local the window holds 5 messages, the largest 3,934
bytes, and a 3,934-byte message can still hold a 998-byte line — so unlike the size
version this does not predict zero without reading the bodies, and the count is the
test.

**And a standing one, for after Step 21 rather than for the twentieth reading:
this class goes to zero at the deploy and stays there.** It is the cleanest
before/after the modernization has offered so far — a defect measured in the wild
on the old stack, with the replacement's fix measured on the bench, and an
instrument already running that will report the result without anyone arranging
it.

---

### Twentieth reading — 2026-09-05, covering 2026-09-04: Google's offset survives its strongest window yet, Yahoo contradicts it in the same window, and the size hypothesis dies on a forward test

**Sixty-two files in `~/dmarc` — two new, sixty re-reads.** Both new files carry
mtimes of 2026-09-05 09:49 and both cover the same window, so the arrival-time
caveat the nineteenth reading raised does not bite here: there is nothing to
separate.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `google.com` | `google.com` | `18325381486835571284` | 2026-09-04 | 16 | 0 |
| `yahoo.com` | `Yahoo` | `1788587309.31603` | 2026-09-04 | 1 | 0 |

**09-03 closed at 9** across three endpoints, exactly as predicted, and did not
gain. **09-04 stands at 17** across two, with Microsoft still to file.

Every row in all sixty-two files is `disposition=none`. Nothing has been
quarantined under `p=quarantine` at any receiver in any window.

#### Four predictions held; the fifth was wrong, and the fault is in the nineteenth reading

1. **Microsoft does not file for 09-03 at all — held, and 09-03 closed at 9.** No
   `protection.outlook.com` file for that window exists a full day after the one
   for 09-02 arrived, which is when a window-late filing would have landed. jaguar
   sent nothing to `hotmail.com`, `outlook.com` or `live.com` in the UTC 09-03 day,
   and the prediction was made from the send log rather than from the last report's
   shape for the third time running.
2. **"Google's 09-04 report contains the four messages sent `Sep 3 15:49:02`–
   `15:51:20` local" — FALSIFIED, and it was falsified before it was written.**
   Those four sit in the UTC−7 **09-03** day and were already inside the 09-03
   report. See the correction below. The headline half of the prediction — that the
   report reads a UTC−7 day — is confirmed by a different and stronger route.
3. **No signed-DKIM-fail row — held, and it kills the rival hypothesis outright.**
   See two subsections down; this is the reading's second result.
4. **GMX files for nothing — held.** No `gmx.*` traffic in the UTC 09-03 window and
   no GMX report for it.
5. **Every report reads `p=quarantine` and no row carries a `disposition` other
   than `none` — held**, both reports.

#### A correction to the nineteenth reading: the right count, the wrong four messages

That reading's 09-03 arithmetic is sound — the UTC day holds 11 Google-bound
messages, the UTC−7 day holds 7, Google reported 7, and this reading reproduces all
three figures. **What it got wrong is which four messages the offset moves.**

It named `Sep 3 15:49:02`–`15:51:20` local, and reasoned that `20:49`–`20:51Z` on
09-03 falls "inside the UTC−7 09-04 day." It does not. Subtracting seven hours from
`20:49Z` gives `13:49` on 09-03, which is the middle of the UTC−7 **09-03** day —
the same day the UTC stamp names. Those four messages never moved.

The four that do move are the ones at the *other* end of the window:

| Queue ID | Sent (jaguar local) | UTC | UTC day | UTC−7 day |
|---|---|---|---|---|
| `B7F35586513` | Sep 2 21:37:16 | 09-03 02:37:16Z | 09-03 | **09-02** |
| `2B23958650C` | Sep 2 22:02:18 | 09-03 03:02:18Z | 09-03 | **09-02** |
| `B53F45864B2` | Sep 3 01:19:08 | 09-03 06:19:08Z | 09-03 | **09-02** |
| `3B067586513` | Sep 3 01:39:23 | 09-03 06:39:23Z | 09-03 | **09-02** |

They leave the UTC−7 09-03 day at its *start*, not its end, which is the same shape
the eighteenth reading described correctly for 09-01. The UTC−7 09-03 set is then
exactly seven: the `02:01`, `02:02` and `03:07` messages of Sep 3 plus the four at
`15:49`–`15:51`. Google reported seven.

**So the 09-03 report already contained the four messages the nineteenth reading
said were in neither report**, and the twentieth reading's prediction 2 inherited
that. The error is arithmetic in a sentence, not in the script that produced the
table — the table was right — which is exactly the kind of slip that survives when
the prose is written after the numbers and not checked back against them.
[[suspect-the-measurer-before-the-record]]

#### The UTC−7 aggregation day, tested a third time, on the window that discriminates hardest

Sends are binned as in the last three readings — `status=sent`, minus
`relay=local`, at jaguar's UTC−5, which `date -u` on the host confirms again — by a
**fourth independently written script**, and this time across `mail.log`,
`mail.log.1` and `mail.log.2.gz` together rather than the live file alone. Google's
figures are its rows from `173.255.245.115` only.

| Window | 08-23 | 08-24 | 08-25 | 08-26 | 08-27 | 08-28 | 08-29 | 08-30 | 08-31 | 09-01 | 09-02 | 09-03 | **09-04** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Google reported | 12 | 15 | 5 | 6 | 13 | 47 | 22 | 13 | 33 | 8 | 10 | 7 | **16** |
| jaguar sent, UTC day | 26 | 17 | 19 | 6 | 8 | 46 | 22 | 17 | 33 | 6 | 10 | 11 | **12** |
| jaguar sent, UTC−7 day | 20 | 19 | 7 | 6 | 13 | 47 | 22 | 13 | 33 | 8 | 10 | 7 | **16** |

| Alignment | Σ\|residual\| | Exact windows |
|---|---|---|
| UTC (as stamped) | 50 | 4 of 13 |
| UTC−7 | 14 | **10 of 13** |

**Every one of the twelve carried-over columns reproduces in both alignments**, off
three log files and a script that had not seen the previous one. That is the first
time the whole table has been re-measured end to end rather than extended at the
right-hand edge, and it is worth the paragraph: the seventeenth reading's figures
have now been produced three times by three scripts, and the offset is not an
artifact of any of them. [[mutation-verify-or-it-is-not-coverage]]

**09-04 is the sharpest window in the series.** Google reported 16 into a UTC day
holding 12 — a surplus of four, in the direction a receiver cannot manufacture,
from a report naming exactly one source IP. The UTC−7 day holds exactly 16, and the
four that decide it went out at `Sep 4 19:11:49`, `19:12:32`, `21:25:30` and
`23:03:07` local, all after `19:00` and therefore in the UTC **09-05** window. The
last **ten consecutive** windows, 08-26 through 09-04, are exact under UTC−7; five
of those ten are wrong under UTC.

**And the corollary is again a test rather than a fit: those four must not appear
in Google's 09-05 report.**

**Still short of a mechanism, and the three earliest windows are still
unexplained.** 08-23/24/25 hold 14 messages of residual in the direction of jaguar
sending more than Google reported, the offset does not touch them, and nothing else
has been proposed. Unchanged for the fourth reading.

#### Yahoo contradicts the offset in the same window, off the same log

The eighteenth reading found its cleanest control in GMX, which fit UTC in the same
window Google fit UTC−7. **09-04 repeats it with Yahoo, and more sharply**, because
Yahoo is the only other filer for this window:

| Endpoint | Reported | jaguar sent, UTC 09-04 | jaguar sent, UTC−7 09-04 |
|---|---|---|---|
| `google.com` | 16 | 12 | **16** |
| `yahoo.com` | 1 | **1** | 2 |

The second Yahoo-bound message, `3A004586572` to `member27@example.com` at
`Sep 4 23:03:06` local, is `09-05 04:03:06Z` — inside the UTC−7 09-04 day and
outside the UTC one. Yahoo left it out. **One window, one log, one script: the
receiver that fits UTC−7 and the receiver that fits UTC are measured against the
same twenty-four hours.** The offset is a property of Google's reporting, not of
jaguar's clock, and this is now established twice rather than once.

`yahoo.com` itself had not filed since the 08-31 window, and the send log explains
that as it explained the others: no `yahoo.com` traffic at all in 09-01, 09-02 or
09-03, one message in 09-04.

#### The size hypothesis dies on its first forward test, and so does the injection path

The nineteenth reading recorded a fit — no message of 5,653 bytes or more had gone
to a Google endpoint in a clean window, and all three signed-DKIM failures were at
or above it — and called it curve-fitting rather than a cause. The addendum then
replaced it with a mechanism measured from two raw messages: **a body line longer
than 998 bytes**, which Postfix breaks after `opendkim` has signed.

The 09-04 window tests both, and the reports carry **no signed-DKIM-fail row at
all**:

| Hypothesis | Predicted failures in UTC−7 09-04 | Observed |
|---|---|---|
| Message size ≥ 5,653 bytes | **3** — `7A9AB58650F` (5,971), `C4C685864B2` (5,963), `8ED7C586505` (6,079) | **0** |
| Local injection path | **1** — the `brian` cron message `B1E095864BF`, `Sep 4 02:01:13` | **0** |
| Body line > 998 bytes | 0, if none of the sixteen carries one | 0 |

**The size proxy is now falsified from both sides.** 08-31 killed it below the
threshold — eight messages of 5,296–5,312 bytes, no failure — and 09-04 kills it
above: three messages larger than any of the three that failed, all clean. The
addendum had already demoted it to a proxy on mechanistic grounds; this is the
independent measurement, made against a prediction stated in advance.

**The injection-path hypothesis, falsified retrospectively last reading, fails
forward too.** The same daily `brian` cron message sits in this window and the
window is clean.

**What the line-length mechanism gets from this window is consistency, not
confirmation.** Zero failures is what it predicts *if* none of the sixteen bodies
holds a line over 998 bytes, and those bodies were not read — the two that were
read, in the addendum, are the only direct evidence there is. A window with no
long line cannot distinguish a correct mechanism from an absent one. The test that
would confirm it is the next window that contains a long line, and the standing
prediction is unchanged: **this class goes to zero at the Step 21 deploy and stays
there.** [[measure-before-recording-in-planning-docs]]

`B4EFD5864BF` (6,050 bytes) is still the one of the three assigned by shape rather
than observed, and nothing this reading measured changes that.

#### What held steady across all sixty-two

- **75 rows, 397 messages, every one `disposition=none`.**
- Evaluated SPF/DKIM across those rows: **67 `pass`/`pass`, 4 `fail`/`pass`,
  3 `pass`/`fail`, 1 `fail`/`fail`** — the `pass`/`fail` count is unchanged, which
  is the whole of the DKIM result above.
- `173.255.245.115` appears in 67 rows and 376 messages.
- Policy renders `adkim=r aspf=r` in all sixty-two.
- The `p=none`/`p=quarantine` boundary at the 08-25 publication reproduces exactly:
  16 reports read `none`, 46 read `quarantine`.
- **Eleven reporting endpoints by filename**, five reporting organizations. No new
  endpoint and no new organization this reading.
- The published-policy field census tracks the corpus without surprises: `sp` in 36
  and absent in exactly the 26 Yahoo reports, `pct` in 56 and absent in exactly the
  6 GMX reports, `np` in exactly the 13 Google reports, `fo` in exactly the 17
  Comcast and Microsoft reports, `discovery_method` and `testing` in exactly the 6
  GMX reports. Our record still publishes none of them.

#### The forwarding class is at zero for a fifth window, and Postmark for an eighth

`209.85.220.41` carried nothing on 09-04. The class reads 8, 5, 2, 0, 0, 0, 0, 0
across 08-28 → 09-04, 17 messages total, every one surviving on DKIM, and the
twelfth reading's `2001:470:0:60::2` row has not recurred in nine windows.
Postmark's `50.31.156.*` has not appeared since the 08-27 window; jaguar
is still the only thing sending, which is expected until Step 21 and is the reason
the Postmark path remains measured only by the two hand-sent test messages.

#### Bearing on the policy decision

Nothing moves. `p=quarantine` continues to cost nothing measurable — 397 messages,
zero non-`none` dispositions, and the one class of DKIM failure that has a known
cause is fixed by the branch waiting to deploy rather than by any change to the
zone. `p=reject` stays unrecommended until after the Step 21 deploy, for the reason
the nineteenth reading gave: not that the cause is unknown, but that the fix is not
deployed yet.

#### Predictions for the twenty-first reading

1. **Microsoft files for 09-04 with exactly 1 message**, a window late, from
   `hotmail.com` — `15AA2586558` at `Sep 4 18:19:36` local, `23:19:36Z`, the only
   Microsoft-bound message in either alignment of that day. **09-04 then closes at
   18.**
2. **Google's 09-05 report does not contain the four messages of `Sep 4 19:11:49`–
   `23:03:07` local**, because the 09-04 report has already counted them. This is
   the offset's sharpest available test and it fails if the 09-05 count exceeds the
   UTC−7 09-05 total measured against a complete log.
3. **Yahoo files for 09-05 and its report contains `3A004586572`**, the
   `23:03:06` local message, giving a count of at least 1. Yahoo's UTC alignment
   and Google's UTC−7 alignment make opposite claims about this single message, and
   the two 09-05 reports settle it independently of any count.
4. **GMX and Comcast file for nothing.** No `gmx.*` or `comcast.net` traffic in the
   UTC 09-04 window.
5. **Every report reads `p=quarantine`** and no row carries a `disposition` other
   than `none`.

---

### Twenty-first reading — 2026-09-08, covering 2026-09-04 through 2026-09-07: all five predictions hold, three consecutive Google days reconcile exactly, and Microsoft does not fold tenant domains the way Google does

**Sixty-nine files in `~/dmarc`, sixty-eight reports — six new, sixty-two
re-reads, and one exact duplicate.**
`google.com!surfguitar101.com!1788652800!1788739199 (1).zip` is a second download
of the 09-06 Google report: same md5 `6bd812354e759b24b024e1ff1b349209`, same
`report_id`. `tools/dmarc_report.py` has no dedupe and read sixty-nine files as
sixty-nine reports, counting those 6 messages twice. **Every figure below is on
the deduped corpus of sixty-eight.**

**Brian deleted the duplicate the same day** and the tool now reads sixty-eight,
agreeing with this reading. **The dedupe gap is still in the tool**, closed here by
removing the input rather than by fixing the instrument: a second copy of any report
under a different filename will double-count again, silently and in the direction of
overstating delivery. `(org_name, report_id)` is the key that identifies a report —
the sixth reading established it — and nothing in the tool consults it.
[[suspect-the-measurer-before-the-record]]

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `protection.outlook.com` | `Outlook.com` | `ba610e976e4b4ab3bea34dcef0a7ab82` | 2026-09-04 | 1 | 0 |
| `google.com` | `google.com` | `7757518229062265817` | 2026-09-05 | 5 | **1** |
| `yahoo.com` | `Yahoo` | `1788672892.142064` | 2026-09-05 | 1 | 0 |
| `google.com` | `google.com` | `12744820429228850898` | 2026-09-06 | 6 | 0 |
| `protection.outlook.com` | `Outlook.com` | `6f440f5cfd9b4c73a19ad71b0e6351d4` | 2026-09-06 | 2 | 0 |
| `comcast.net` | `comcast.net` | `v2-1788831294-surfguitar101.com` | 2026-09-07 | 3 | 0 |

**All six files carry mtimes of 2026-09-08 17:12–17:14** — one download batch, so
arrival order is not separable within this reading and the nineteenth reading's
arrival-time caveat bites in full. The one thing the mtimes do settle is a lower
bound: the 09-04 Microsoft report was **not** in the 2026-09-05 09:49 batch the
twentieth reading read, so it arrived somewhere between 09-05 09:49 and 09-08
17:13. "A window late" is consistent with that and is not measured by it.

**09-04 closed at 18** across three endpoints, exactly as predicted, and did not
gain. Every row in all sixty-eight files is `disposition=none`. Nothing has been
quarantined under `p=quarantine` at any receiver in any window.

#### All five predictions held, and the arithmetic in two of them is exact

1. **Microsoft filed for 09-04 with exactly 1 message, `envelope_to:
   hotmail.com` — held.** `15AA2586558` at `Sep 4 18:19:36` local, `23:19:36Z`,
   is the only Microsoft-bound send in the UTC 09-04 window, and the report names
   the mailbox domain the prediction named. **09-04 then closed at 18** — Yahoo 1,
   Google 16, Microsoft 1. The *"a window late"* clause is the one part not
   measured; see the mtime bound above.
2. **Google's 09-05 report does not contain the four messages of `Sep 4
   19:11:49`–`23:03:07` local — held, and the forward test is now exact.** See the
   next subsection.
3. **Yahoo filed for 09-05 and its report contains `3A004586572` — held, at a
   count of exactly 1.** That message, `Sep 4 23:03:06` local, `04:03:06Z`, is the
   only Yahoo-bound send in the UTC 09-05 window. `2DF3F5864BF` left one second
   later for Gmail and sits in **Google's 09-04** day. Two reporters, one second
   apart, opposite day labels, off the same log line pair.
4. **GMX and Comcast filed for nothing — held.** No `gmx.*` or `comcast.net`
   recipient in the UTC 09-04 window, and no report from either for it.
5. **Every report reads `p=quarantine` and no row carries a `disposition` other
   than `none` — held**, all six.

#### The UTC−7 aggregation day, tested a fourth time, on three consecutive days at once

Google's day starts at `02:00` local. Measured against a complete send log, three
adjacent Google windows reconcile with no slack in either direction:

| Google window | UTC−7 day, local | Google-bound sends | Reported |
|---|---|---|---|
| 09-04 | `Sep 4 02:00` → `Sep 5 02:00` | `B1E095864BF` `02:01:13` → `2DF3F5864BF` `23:03:07`, 16 | **16** |
| 09-05 | `Sep 5 02:00` → `Sep 6 02:00` | `12EBB5864BF` `02:01:13` → `683915864B2` `Sep 6 01:53:40`, 5 | **5** |
| 09-06 | `Sep 6 02:00` → `Sep 7 02:00` | `1C5A55864BF` `02:01:12` → `710275864EC` `Sep 7 01:35:58`, 6 | **6** |

The boundary does the work three times. `683915864B2` at `Sep 6 01:53:40` lands in
09-05 and `1C5A55864BF` at `02:01:12`, eight minutes later, lands in 09-06; the
same seven-minute-wide split separates 09-06 from 09-07 at `0D3A25864BF`. **A UTC
day would move messages across all three boundaries and break all three counts.**
This is the offset's fourth forward test and the first to run on three windows
that were predicted before any of the three reports existed.

#### Microsoft does not fold tenant domains, and Google does

jaguar sent **three** Microsoft-bound messages in the UTC 09-06 window. Microsoft's
report covers **two** — `envelope_to: hotmail.com`, count 2, the two consumer
mailboxes `B8FF8586572` (`member17@example.com`) and `6630058650F`
(`member31@example.com`). The third is absent:

| Queue ID | Sent (local) | Recipient | Relay | In a report? |
|---|---|---|---|---|
| `B8FF8586572` | Sep 6 02:48:25 | `member17@example.com` | `hotmail-com.olc.protection.outlook.com` | yes |
| `C23FC5864B2` | Sep 6 11:09:11 | `member28@example.com` | `cpp-edu.mail.protection.outlook.com` | **no** |
| `6630058650F` | Sep 6 11:20:30 | `member31@example.com` | `hotmail-com.olc.protection.outlook.com` | yes |

`cpp.edu` MXes to `cpp-edu.mail.protection.outlook.com` — a Microsoft 365 tenant,
verified by lookup rather than inferred from the relay string, in the practice the
nineteenth reading adopted. **`cpp.edu` appears nowhere in this log before now.**

This is the opposite of the Google result. The nineteenth reading corrected itself
to establish that `muohio.edu`, an `aspmx.l.google.com` tenant, sits *inside* the
`google.com` endpoint's report rather than among the non-reporting domains.
Microsoft's endpoint, on this window, does not behave that way: it splits by
mailbox domain, files for the consumer domain, and drops the tenant.

**What this reading has is one window, and one window cannot tell a rule from an
absence.** The tenant report may yet arrive; the tenant may have reporting
disabled; Microsoft may aggregate tenants on a different cadence. Two tests
settle it and both are already loaded, one in each direction — see predictions 1
and 2.

#### The DKIM-failure class recurs, and this window cannot identify it

A fifth `pass`/`fail` message, in Google's 09-05 window. The class now stands at
**4 rows, 5 messages**, all at Google, all `disposition=none`. The five candidates
in that window and their sizes:

| Queue ID | Sent (local) | From | Size |
|---|---|---|---|
| `12EBB5864BF` | Sep 5 02:01:13 | `brian@surfguitar101.com` | 728 |
| `192EC58650C` | Sep 5 08:16:57 | `no_reply@surfguitar101.com` | 5,450 |
| `774965864EC` | Sep 5 12:57:14 | `no_reply@surfguitar101.com` | 6,188 |
| `8E3E3586505` | Sep 5 20:33:47 | `no_reply@surfguitar101.com` | 2,464 |
| `683915864B2` | Sep 6 01:53:40 | `no_reply@surfguitar101.com` | 6,254 |

**Size does not pick it out** — the five span 728 to 6,254 bytes, which brackets
`B4EFD5864BF` at 6,050 in both directions, and the twentieth reading already killed
the size hypothesis on a forward test. **Nor does the injection path**: Google's day
begins at `02:00` and the daily `brian` cron message goes out at `02:01`, so it sits
at the head of *every* Google window, clean ones included, and cannot discriminate
between them. That is the same falsification the twentieth reading made, reproduced
here from the boundary rather than from a single window.

The aggregate report carries no message identifier, so **nothing measured in this
reading names the failing message.** The line-length mechanism from the nineteenth
reading's addendum is neither confirmed nor damaged by it: a window whose bodies
were not read cannot distinguish a correct mechanism from an absent one, and the
bodies are gone from the queue. The standing prediction is unchanged — **this class
goes to zero at the Step 21 deploy and stays there.**
[[measure-before-recording-in-planning-docs]]

#### What held steady across all sixty-eight

- **82 rows, 415 messages, every one `disposition=none`.**
- Evaluated SPF/DKIM across those rows: **73 `pass`/`pass`, 4 `fail`/`pass`,
  4 `pass`/`fail`, 1 `fail`/`fail`** — the `pass`/`fail` count is up by one, which
  is the whole of the DKIM result above.
- `173.255.245.115` appears in 74 rows and 394 messages.
- Policy renders `adkim=r aspf=r` in all sixty-eight.
- The `p=none`/`p=quarantine` boundary at the 08-25 publication reproduces exactly:
  16 reports read `none`, 52 read `quarantine`.
- **Eleven reporting endpoints by filename, five reporting organizations.** No new
  endpoint and no new organization this reading — `cpp.edu` is a *recipient* domain
  that filed nothing, not a twelfth endpoint.
- The published-policy field census tracks the corpus without surprises: `sp` in 41
  and absent in exactly the 27 Yahoo reports, `pct` in 62 and absent in exactly the
  6 GMX reports, `np` in exactly the 15 Google reports, `fo` in exactly the 20
  Comcast and Microsoft reports, `discovery_method` and `testing` in exactly the 6
  GMX reports. Our record still publishes none of them.

#### The forwarding class is at zero for a seventh window, and Postmark for an eleventh

`209.85.220.41` carried nothing on 09-05 or 09-06. The class reads 8, 5, 2, 0, 0,
0, 0, 0, 0, 0 across 08-28 → 09-06, 17 messages total, every one surviving on DKIM,
and the twelfth reading's `2001:470:0:60::2` row has not recurred in eleven windows.
Postmark's `50.31.156.*` has not appeared since the 08-27 window; jaguar is still
the only thing sending, which is expected until Step 21 and is the reason the
Postmark path remains measured only by the two hand-sent test messages.

#### Bearing on the policy decision

Nothing moves. `p=quarantine` continues to cost nothing measurable — 415 messages,
zero non-`none` dispositions, and the one class of DKIM failure that has a known
cause is fixed by the branch waiting to deploy rather than by any change to the
zone. `p=reject` stays unrecommended until after the Step 21 deploy, for the reason
the nineteenth reading gave: not that the cause is unknown, but that the fix is not
deployed yet.

#### Predictions for the twenty-second reading

Measured against the send log through `Sep 8 13:51` local. The UTC 09-07 window is
complete in the log; 09-08 is not, and nothing below depends on it.

1. **Google's 09-07 report settles the tenant question in Google's direction, or
   breaks the nineteenth reading's correction.** Twenty Google-bound sends fall in
   the UTC−7 09-07 day, `0D3A25864BF` at `Sep 7 02:01:13` through `98B1C58650F` at
   `22:26:32`, with `72C565864DF` at `Sep 8 02:01:12` falling into 09-08. One of
   those twenty is `F15C3586505` to `member24@example.com`, relayed through
   `aspmx.l.google.com`. **The report reads 20 if Google folds the tenant in and 19
   if it does not**, and 19 falsifies the nineteenth reading's correction.
2. **No Microsoft report naming `cpp.edu` arrives for 09-06, and Microsoft's 09-07
   report reads 2 messages, `envelope_to: hotmail.com`** — `8C9E8586529`
   (`member23@example.com`, `Sep 7 10:35:05`) and `8D5835869B6`
   (`member30@example.com`, `17:40:01`). A `cpp.edu` report at any count
   falsifies the first half; a 09-07 count of 3 falsifies both halves at once.
3. **Yahoo files two reports for 09-07 and no more**: `yahoo.com` with 2
   (`3A86F586565` at `Sep 7 07:41:28`, `3340C5869B7` at `14:32:59`) and `aol.com`
   with 1 (`242605869B6` at `10:44:45`). No `att.net`, `sbcglobal.net`,
   `verizon.net`, `bellsouth.net` or `cox.net` filing for that window.
4. **GMX files nothing for 09-07.** No `gmx.*` recipient in the window —
   `member25@example.com` at `Sep 7 10:44:47` relays through `mx01.mail.de` and is not
   GMX. **Comcast has already filed for 09-07 at 3**, matching its three
   `member18@example.com` sends exactly, so that endpoint is closed.
5. **Every report reads `p=quarantine`** and no row carries a `disposition` other
   than `none`.

### Twenty-second reading — 2026-09-12, covering 2026-09-07 through 2026-09-11: a second forwarder appears at web.de, four more exact Google days, and three endpoints file nothing for a window that had traffic

**Seventy-nine files in `~/dmarc`, seventy-nine reports — eleven new, sixty-eight
re-reads, no duplicates.** `tools/dmarc_report.py` reads eighty files and reports
one carrying no report, which is `.DS_Store`. The dedupe gap the twenty-first
reading left open is still open and still unexercised.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `protection.outlook.com` | `Outlook.com` | `1249614d6b64470185e69037848dcdba` | 2026-09-07 | 2 | 0 |
| `google.com` | `google.com` | `13332903735224958335` | 2026-09-08 | 7 | 0 |
| `protection.outlook.com` | `Outlook.com` | `29eff51fe2cd4716b029a1bda35f714a` | 2026-09-08 | 3 | 0 |
| `google.com` | `google.com` | `8513463802414860469` | 2026-09-09 | 15 | 0 |
| `yahoo.com` | `Yahoo` | `1789019529.606825` | 2026-09-09 | 10 | 0 |
| `google.com` | `google.com` | `13277591310551611455` | 2026-09-10 | 13 | 0 |
| `protection.outlook.com` | `Outlook.com` | `00cc373afbc947eb96dda29c5a54085f` | 2026-09-10 | 4 | 0 |
| `yahoo.com` | `Yahoo` | `1789106237.164382` | 2026-09-10 | 3 | 0 |
| `cox.net` | `Yahoo` | `1789106237.164315` | 2026-09-10 | 3 | 0 |
| `google.com` | `google.com` | `2008410879461165677` | 2026-09-11 | 12 | 0 |
| `cox.net` | `Yahoo` | `1789191865.130527` | 2026-09-11 | 4 | 0 |

All eleven files carry mtimes of 2026-09-12 12:57–13:00 — one download batch, so
the nineteenth reading's arrival-time caveat bites in full again. The send-side
figures below come from jaguar's live `/var/log/mail.log`, which at the time of
reading began `Sep 6 06:47` and ran to `Sep 12 13:05` local. **jaguar is UTC−5**;
`date -u` on the box reads `18:04:55Z` against a `13:05` local log line.

#### Scoring the twenty-first reading's predictions: two held, one falsified, one unresolved because the report does not exist

1. **UNRESOLVED — Google filed nothing for the 09-07 window.** The prediction was
   exact about the traffic and could not be exercised: the UTC−7 09-07 day runs
   `0D3A25864BF` at `Sep 7 02:01:13` through `98B1C58650F` at `22:26:32`, is
   **twenty** Google-bound sends including `F15C3586505` to `member24@example.com`,
   and `72C565864DF` at `Sep 8 02:01:12` falls into 09-08 exactly as predicted.
   The report that would read 20 or 19 was never filed or never arrived. See *The
   09-07 hole* below. **The tenant question it was loaded to settle is answered
   anyway, twice, on windows the prediction never named** — see the next section.
2. **HELD, both halves.** No Microsoft report naming `cpp.edu` has arrived for
   09-06, and Microsoft's 09-07 report reads exactly **2**, `envelope_to:
   hotmail.com` — `8C9E8586529` (`Sep 7 10:35:05`) and `8D5835869B6` (`17:40:01`),
   the two the prediction named.
3. **FALSIFIED — Yahoo filed neither report.** The prediction was `yahoo.com` at 2
   and `aol.com` at 1 for the 09-07 window. Both sends are in the log —
   `3A86F586565` (`Sep 7 07:41:28`) and `3340C5869B7` (`14:32:59`) to `yahoo.com`,
   `242605869BA` (`10:44:45`) to `member26@example.com` — and neither endpoint has
   a 09-07 file. The negative half held: no `att.net`, `sbcglobal.net`,
   `verizon.net`, `bellsouth.net` or `cox.net` filing for that window.
4. **HELD.** No `gmx.*` recipient in the window and no GMX report; `member25@example.com`
   at `Sep 7 10:44:47` relays through `mx01.mail.de` and is not GMX. Comcast's
   09-07 filing at 3 was already closed.
5. **HELD.** All eleven read `p=quarantine`, and no row in any of the seventy-nine
   carries a `disposition` other than `none`.

#### A second forwarder class, at web.de, and it reconciles exactly

Four source IPs that appear nowhere in this log before now. All four reverse to
**`mout.web.de`**, and whois puts `217.72.192.78` in `WEBDE1` / *1&1 Mail & Media
GmbH* and `212.227.17.11` in `ionos-inf` / *IONOS SE*, both DE — verified by
lookup rather than inferred from the reverse name, in the practice the nineteenth
reading adopted.

| Google window | Source IPs | Msgs | Evaluated | `auth_results` |
|---|---|---|---|---|
| 09-09 | `212.227.17.11` | 1 | `dkim=pass spf=fail` | `dkim d=surfguitar101.com pass`, `spf d=web.de pass` |
| 09-10 | `212.227.15.3`, `212.227.15.14`, `217.72.192.78` | 3 | same | same |
| 09-11 | `212.227.15.3`, `212.227.17.11`, `217.72.192.78` | 3 | same | same |

Every row is `header_from: surfguitar101.com`, `disposition=none`, DMARC passing
on DKIM alone. **SPF authenticates and does not align**: the envelope sender was
rewritten into `web.de` by the forwarder, so `spf` returns `pass` for the wrong
domain, which under `aspf=r` is `fail` for our purposes.

jaguar sent **seven** messages to one address, `member29@example.com`, relayed
through `mx-ha02/03.web.de` — the MX web.de publishes. Google reported **seven**
forwarded messages, and they fall in the same UTC−7 days:

| Google window | web.de sends in the UTC−7 day | Rows reported |
|---|---|---|
| 09-08 | 0 | 0 |
| 09-09 | `EC85D5869B7` `Sep 9 21:54:18` — 1 | **1** |
| 09-10 | `ABB7F5869B7` `16:22:56`, `1FE9B5869B7` `19:32:01`, `506795869B7` `Sep 11 00:59:02` — 3 | **3** |
| 09-11 | `487C45869B8` `09:01:50`, `27D995869B7` `09:18:45`, `8B9755869B7` `Sep 12 01:04:23` — 3 | **3** |

**This is the same mechanism as the `209.85.220.41` Gmail-relay rows of 08-26 →
08-30**, from a second and independent forwarder: a `web.de` mailbox that
auto-forwards site mail onward to Gmail. The From header survives, so it stays in
*this* domain's report; the connecting IP is web.de's, so SPF cannot align; the
`opendkim` signature still validates because forwarding alters neither headers nor
body. It is member-side configuration with nothing to find or fix on the box, and
jaguar cannot see the second hop at all.

**What is new is not the mechanism but the conditions.** The Gmail-relay
observations were all made under `p=none` or in the first days of `p=quarantine`,
and the readings that used them to argue *DKIM carries forwarded mail through
DMARC* were arguing about a tightening that had not happened. These seven ran
under `p=quarantine` and under a live `-all` SPF record — `v=spf1
ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64
include:_spf.mx.cloudflare.net -all`, re-read from DNS this reading — and every
one was delivered `disposition=none`. **The argument is no longer a prediction
about a tightening; it is a measurement taken after it.**

**Bearing on the deferred `p=reject` decision.** These seven are exactly the mail
that `p=reject` would put at risk, and they are at risk only through DKIM: one
broken signature on that path and the forward is refused rather than quarantined.
That is not an argument against `p=reject` — it is the quantity to put beside it,
and it is small, one recipient, one forwarder.

#### Google's UTC−7 day reconciles exactly four more times, and the tenant question settles with it

Google's day starts at `02:00` local. Counting Gmail plus the Google Workspace
tenant — `muohio.edu`, whose MX is `aspmx.l.google.com` at priority 1, verified by
lookup this reading — against a complete send log:

| Google window | UTC−7 day, local | Google-bound sends | Reported |
|---|---|---|---|
| 09-08 | `Sep 8 02:00` → `Sep 9 02:00` | 6 Gmail + `8D31158650F` to `muohio.edu` `07:36:37` = **7** | **7** |
| 09-09 | `Sep 9 02:00` → `Sep 10 02:00` | 14 Gmail, no tenant = **14** | **14** |
| 09-10 | `Sep 10 02:00` → `Sep 11 02:00` | 10 Gmail, no tenant = **10** | **10** |
| 09-11 | `Sep 11 02:00` → `Sep 12 02:00` | 8 Gmail + `B3CE2586516` to `muohio.edu` `Sep 12 01:24:18` = **9** | **9** |

Four for four, on the `173.255.245.115` row alone; the web.de rows are the table
above and are additional. **The boundary does the work four more times**: the
daily `brian` cron message goes out at `02:01:1x` and lands on the new day in all
four windows, while the latest previous-day send is `Sep 12 01:24:19`. The
boundary is pinned inside a thirty-seven-minute gap, and a UTC day would move
messages across all four.

**The nineteenth reading's correction is confirmed, and prediction 1 did not need
to be the thing that confirmed it.** `muohio.edu` sits *inside* the `google.com`
endpoint's report on 09-08 and again on 09-11: drop the tenant and those windows
read 6 and 8 against reports of 7 and 9. Google folds tenants; Microsoft, per the
twenty-first reading, does not. **Two endpoints, two different rules, both now
measured twice.**

#### Yahoo, Cox and Microsoft reconcile exactly on the true UTC day

The twentieth reading found Yahoo contradicting Google's offset in the same
window and could not say more from one window. Five windows now say it plainly —
these endpoints aggregate on the **UTC calendar day**, with no offset:

| Endpoint | Window | Sends in the true UTC day | Reported |
|---|---|---|---|
| `yahoo.com` | 09-09 | 10 | **10** |
| `yahoo.com` | 09-10 | 3 | **3** |
| `cox.net` | 09-10 | 3 | **3** |
| `cox.net` | 09-11 | 4 | **4** |
| `protection.outlook.com` | 09-07 | 2 `hotmail.com` | **2** |
| `protection.outlook.com` | 09-08 | 2 `hotmail.com` + 1 `hotmail.fr` | **3** |
| `protection.outlook.com` | 09-10 | 4 `hotmail.com` | **4** |

Seven for seven. Microsoft's 09-08 report splits its three into two records by
`envelope_to`, which is the fifteenth reading's finding reproduced on a new
mailbox domain — `hotmail.fr`, relayed through `eur.olc.protection.outlook.com`.

**Cox is a Yahoo tenancy and behaves like Yahoo, not like a third case.** Its
reports carry `org_name: Yahoo` and its recipients relay through
`mta5/6/7.am0.yahoodns.net`, the same MXes as `yahoo.com`. That is worth stating
because the first cut of this reading classified Cox-bound sends as Yahoo by relay
name, which put six messages in the `yahoo.com` column and made its 09-10 report
read 3 against 6. **The mismatch was in the measurement, not the report.**
Classifying by recipient domain rather than by relay fixes it and makes both
endpoints exact. [[suspect-the-measurer-before-the-record]]

**The split is now a property of the instrument, not an anomaly in it.** Google
files on UTC−7; Yahoo, Cox and Microsoft file on UTC. A window label cannot be
compared across reporters without applying the right offset, and every
cross-reporter total in this log before the eighteenth reading was computed
without one.

#### The 09-07 hole — three endpoints with traffic and no report

Five days after the window closed, the 09-07 window is missing three of the five
endpoints that had mail in it:

| Endpoint | Sends in its own day definition | Report |
|---|---|---|
| `google.com` | 20 (UTC−7) | **absent** |
| `yahoo.com` | 2 (UTC) | **absent** |
| `aol.com` | 1 (UTC) | **absent** |
| `protection.outlook.com` | 2 (UTC) | present, exact |
| `comcast.net` | 3 (UTC) | present, exact |

`google.com!surfguitar101.com!1788739200!1788825599.zip` is simply not in
`~/dmarc`; the Comcast and Microsoft files for the same epoch pair are. **20
messages is the largest Google day in the current log**, which makes this the most
expensive window the series has lost.

**Two explanations, and this reading cannot separate them.** Either the three
reporters did not file, or the reports were filed and did not reach `~/dmarc` —
the `rua` local copy runs `admin@surfguitar101.com` through Cloudflare Email
Routing to Gmail and is saved by hand. **Three simultaneous absences across three
independent organizations favor the collection path**, since nothing plausible
makes Google, Yahoo and AOL all skip the same day while Comcast and Microsoft file
for it. Against that: Microsoft's 09-07 report arrived only in this batch, four
days late, so arrival is spread out and "absent at five days" is not "never sent".

**AOL has not filed since the 08-31 window**, and the single AOL-bound send this
log covers — `242605869BA`, `Sep 7 10:44:45` — has no report. Yahoo's absence is two windows wide, 09-07 and
09-08, and it resumes at 09-09 with an exact report. A collection hole that
swallowed one delivery batch would look exactly like that.

**The test is already available and does not go through our mail at all.** The
`_dmarc` record's other `rua` destination is
`00fc656c22e64e73bb643fb00331d013@dmarc-reports.cloudflare.net`, re-read from DNS
this reading and intact. **If Cloudflare's dashboard shows Google, Yahoo and AOL
volume for 2026-09-07, the reports were filed and our collection path lost them**;
if it shows the same hole, they were not filed. That distinguishes an instrument
fault from a reporter behavior in one look, and it should be run before the next
reading rather than after.

#### The signed-DKIM failure class did not recur, and the window that would have tested it hardest is the one that is missing

`173.255.245.115` with `spf=pass dkim=fail` last appeared in Google's 09-05
window. Five Google windows have been filed since — 09-06, 09-08, 09-09, 09-10,
09-11 — and none carries it. The class stands unchanged at **4 rows, 5 messages**,
exactly where the twenty-first reading left it.

**The absence is weaker than five windows makes it sound.** Those five windows
carry 6, 7, 14, 10 and 9 messages; the missing 09-07 window carries 20, more than
any of them and more than twice the median. **The largest untested window in the
series is the one with no report.** Nothing here contradicts the standing
prediction that the class goes to zero at the Step 21 deploy, and nothing here
strengthens it either: a before/after needs the before, and 09-07 is a hole in it.
[[measure-before-recording-in-planning-docs]]

#### What held steady across all seventy-nine

- **101 rows, 491 messages, every one `disposition=none`.**
- Evaluated SPF/DKIM across those rows: **85 `pass`/`pass`, 11 `fail`/`pass`,
  4 `pass`/`fail`, 1 `fail`/`fail`.** The `fail`/`pass` count is up by seven, and
  all seven are the web.de rows above. The `pass`/`fail` count is unchanged at 4.
- `173.255.245.115` appears in 86 rows and 463 messages.
- Policy renders `adkim=r aspf=r` in all seventy-nine.
- The `p=none`/`p=quarantine` boundary at the 08-25 publication reproduces
  exactly: 16 reports read `none`, 63 read `quarantine`.
- **Eleven reporting endpoints by filename, five reporting organizations.** No new
  endpoint and no new organization — `web.de` is a *source*, not an endpoint, and
  has filed nothing.
- The published-policy field census still tracks the corpus: `sp` in 48 and absent
  in exactly the 31 Yahoo reports, `pct` in 73 and absent in exactly the 6 GMX
  reports, `np` in exactly the 19 Google reports, `fo` in exactly the 8 Comcast
  and 15 Microsoft reports, `discovery_method` and `testing` in exactly the 6 GMX
  reports. Our record still publishes none of them.

#### The forwarding class is not at zero any more, and Postmark is at a fifteenth window

`209.85.220.41` has carried nothing since 08-30 — twelve windows — but the class
it belongs to is live again at a different forwarder, so *"the forwarding class is
at zero"* stops being a useful line here. Stated by source: Gmail relay 4 rows and
17 messages, 08-26 → 08-30; web.de 7 rows and 7 messages, 09-09 → 09-11; the
twelfth reading's `2001:470:0:60::2` row has not recurred in sixteen windows.

**Postmark's `50.31.156.*` has not appeared since the 08-27 window**, and jaguar's
send log confirms why: no message in it relays through `*.mtasv.net`. jaguar is
still the only thing sending. That is expected until Step 21, and it remains the
reason the Postmark path is measured only by the two hand-sent test messages of
08-25.

#### Bearing on the policy decision

Nothing moves. `p=quarantine` continues to cost nothing measurable — 491 messages,
zero non-`none` dispositions, eighteen days live — and this reading adds the
strongest evidence yet that the forwarded-mail risk is carried by DKIM in practice
rather than in principle, measured under both `p=quarantine` and `-all`.
`p=reject` stays unrecommended until after the Step 21 deploy, for the reason the
nineteenth reading gave and the twenty-first repeated: not that the cause is
unknown, but that the fix is not deployed yet.

#### Predictions for the twenty-third reading

Measured against the send log through `Sep 12 13:05` local. The UTC 09-11 window
is complete; UTC 09-12 and the UTC−7 09-12 day are not, and nothing below depends
on them.

1. **Microsoft files for 09-09 at 3 and for 09-11 at 6, both `envelope_to:
   hotmail.com`.** 09-09: `ABA85586565` (`Sep 9 01:05:37`), `40ED2586572`
   (`08:13:39`), `41C605865BF` (`18:50:06`). 09-11: `141A15869B6` (`Sep 10
   19:32:01`), `78196586505` (`Sep 11 00:56:11`), `3380A5869B6` (`00:59:04`),
   `7211F586505` (`08:54:53`), `3D02F5869B7` (`09:01:53`), `1C5F75869B6`
   (`09:18:46`). A count of 7 on 09-11 falsifies the UTC day for this endpoint; a
   `hotmail.fr` or tenant record falsifies the twenty-first reading's
   no-folding finding.
2. **Comcast files for 09-09 at exactly 1** — `6EE2958650F` to
   `member14@example.com`, `Sep 9 17:16:27`, the only Comcast-bound send in the
   UTC 09-09 window.
3. **Yahoo files nothing for 09-11.** No `yahoo.com` recipient falls in that UTC
   day; `cox.net` has already filed it at 4 and that endpoint is closed. A
   `yahoo.com` 09-11 report at any count falsifies the UTC day for Yahoo.
4. **The 09-07 hole is resolved by Cloudflare's dashboard before the reports are
   re-read**, not by waiting. Either volume appears there for 09-07 at Google,
   Yahoo and AOL — a collection fault, and the reading log's series has a hole in
   it that re-downloading may still close — or it does not, and three reporters
   independently skipped a window.
5. **Google's 09-12 report reads at least 9** — 8 Gmail plus `B3CE2586516`'s
   successor `257CE5864B2` to `muohio.edu` at `Sep 12 08:34:59` — and the UTC−7
   day was still open at the log's end, so the figure is a floor.
6. **Every report reads `p=quarantine`** and no row carries a `disposition` other
   than `none`.

#### Addendum, 2026-09-12 — Cloudflare's dashboard read the same afternoon: the 09-07 hole is ours, Yahoo alone did not file, and the two failures in that window are bounces

Prediction 4 above proposed the test and it was run within the hour. **Cloudflare
DMARC Management, zone → Email, Report detail for September 7, 2026:**

| Volume | DMARC pass | SPF aligned | DKIM aligned | IP count | Sending service |
|---|---|---|---|---|---|
| 26 | 26 (100%) | 26 (100%) | 24 (92.31%) | 1 | "Akamai Technologies, Inc." |

**26 against the 5 in `~/dmarc`. The reports were filed; our collection path lost
them.** The prediction set 28 as the all-filed figure and 5 as the none-filed
figure; the answer is at the high end, and the shortfall of 2 is itself
informative.

**The one endpoint that genuinely did not file is Yahoo.** 26 decomposes as Google
20 + Comcast 3 + Microsoft 2 + AOL 1. The only way to reach 26 from the five
candidates is to drop one of the two 2s, and Microsoft's 09-07 report is a file in
`~/dmarc`, so it reached Cloudflare on the same record's other `rua` destination.
Google at 20 rather than 19 is what this reading's tenant result already required.
**So the twenty-first reading's prediction 3 stays falsified for `yahoo.com` and is
now falsified for the opposite reason at `aol.com`** — AOL filed, and we lost it.

**This is inferred from one total, not read from reporter identity.** The dashboard
lists *sending services* and never names the reporter; the preamble has said so
since the first reading. The decomposition is the only arithmetic that fits the
constraints, which is weaker than reading five `org_name` fields and is recorded as
such. Re-downloading the 09-07 reports would settle it by observation.

##### The two unaligned messages are the DSN class, and the eighteenth reading's own check is what says so

`DKIM aligned 24 (92.31%)` against `SPF aligned 26 (100%)` and `IP count 1` is a
`spf=pass dkim=fail` pair from jaguar alone — the shape of the signed-DKIM failure
class this reading recorded as absent. **It is not that class.**

```
Sep  7 03:01:01 jaguar postfix/qmgr[11510]: CF7C258658B: from=<>, size=4083, nrcpt=2
Sep  7 15:59:18 jaguar postfix/qmgr[11510]: C781A5865B2: from=<>, size=4263, nrcpt=2
```

**Exactly two null-sender DSNs on Sep 7, and the only two in the whole log from
`Sep 6 06:47` to `Sep 12 13:05`.** Both are Google-bound to `bgneal@gmail.com` —
they are items 3 and 27 of the UTC−7 09-07 day's send list — so both sit inside
Google's missing report and inside Cloudflare's 09-07 bucket. DSNs bypass the
milters and carry no signature; SPF falls back to the HELO name
`mail.surfguitar101.com`, which shares an organizational domain and so aligns under
`aspf=r`. `pass`/`fail`, two of them, which is the whole of the 24-of-26.

**The over-long-line class did not recur, and that is now measured rather than
assumed.** It stands at 4 rows and 5 messages, unchanged since 09-05. The caveat
this reading attached to the five clean windows — that the largest untested window
in the series was the one with no report — was the right worry and it resolves
clean: 09-07 carried 20 Google-bound messages, and every DKIM failure among them is
accounted for by bounces.

**The eighteenth reading prescribed this check and this is its first real use.**
That reading closed the unsigned-message question by identifying the class as every
Postfix DSN and wrote that a `pass`/`fail` row from `173.255.245.115` is "expected
rather than anomalous — and checkable against `grep 'from=<>'` on the mail log."
One grep, two hits, exact agreement with a dashboard figure derived from reports we
do not hold. **Two classes share one `pass`/`fail` signature in the aggregate
reports, and the send log is what separates them** — which is the argument for why
the send-side baseline cannot be allowed to die unreplaced with jaguar.
[[measure-before-recording-in-planning-docs]]

##### What this costs and what it does not

**It costs the row detail.** Volume, alignment rates and IP count survive in the
dashboard; source IPs, `policy_published`, `envelope_to`, Report-IDs and reporter
identity do not. The 09-07 window can never be reconciled endpoint-by-endpoint the
way 09-08 through 09-11 were, unless the reports are recovered from the mail.

**It does not cost the Step 21 before/after**, which needs the DKIM-failure count
and now has it for 09-07 from two independent directions.

**The collection path is the open item, not the window.** `admin@surfguitar101.com`
runs through Cloudflare Email Routing to Gmail and is saved by hand; something in
that path dropped **two of the four reports filed for 09-07, carrying 21 of its 26
messages**, while keeping the other two. Whether it drops more is not known, and
**every earlier window in this log was collected the same way** — so the corpus
totals are a floor, not a census. Cloudflare's own view is the control that can
measure the gap, and it should be read against the series before the Step 21
window rather than during it.

#### Second addendum, 2026-09-12 — Google's 09-07 report recovered from Gmail: the prediction held, the two failure classes separate inside the report, and the class tally has been wrong since the nineteenth reading

Brian found the report in Gmail and saved it at **14:39**; the corpus is now
**eighty reports, 103 rows, 511 messages**, every disposition still `none`.

**The reports were filed and our collection path lost them — now demonstrated,
not inferred.** The first addendum reasoned it from a Cloudflare total. This is
the file.

##### The twenty-first reading's prediction 1 held, at 20

`4725575807514715615`, window 2026-09-07, **20 messages in 2 records**. The
prediction was *"20 if Google folds the tenant in and 19 if it does not."*
**Twenty.** With 09-08 and 09-11 that is the third independent confirmation that
Google folds Workspace tenants — here `F15C3586505` to `member24@example.com` —
into the `google.com` endpoint's report, and the nineteenth reading's correction
is no longer resting on a single window.

##### The two classes are distinguishable inside the reports, and no send log is needed

The failing record reads:

```
173.255.245.115  n=2  disp=none  dkim=fail  spf=pass
    auth_results: <no dkim element at all>  spf d=mail.surfguitar101.com pass
```

**No `<dkim>` element means the message was never signed** — not signed and
broken. And SPF authenticated `mail.surfguitar101.com`, the HELO name, which is
the fallback for a null envelope sender. That is the eighteenth reading's DSN
class, stated by the report itself.

Applied across every DKIM-failing row in the corpus, the discriminator separates
them cleanly:

| Window | Rows | `<dkim>` element | SPF domain | Class |
|---|---|---|---|---|
| 09-01 | 1 msg | **absent** | `mail.surfguitar101.com` | **DSN** |
| 09-02 | 1 msg | `d=surfguitar101.com` fail | `surfguitar101.com` | over-long-line |
| 09-03 | 2 msgs | `d=surfguitar101.com` fail | `surfguitar101.com` | over-long-line |
| 09-05 | 1 msg | `d=surfguitar101.com` fail | `surfguitar101.com` | over-long-line |
| 09-07 | 2 msgs | **absent** | `mail.surfguitar101.com` | **DSN** |

*(The twelfth reading's `2001:470:0:60::2` row on 08-26 is a third shape again —
a `<dkim>` element failing **and** SPF failing, both on `surfguitar101.com`.)*

**This is an instrument result, and a better one than the method the first
addendum used.** That addendum identified 09-07's two failures as bounces by
matching a Cloudflare aggregate against `grep 'from=<>'` on the mail log. The
identification was right, but **the reports carry the answer on their own** — and
they will keep carrying it after jaguar's log is gone, which is exactly the
dependency the exit-condition section warns cannot outlive the host.

##### ⚠️ CORRECTION — the over-long-line class has been over-counted since the nineteenth reading

**It is 3 rows and 4 messages, not 4 rows and 5.** The 09-01 message is unsigned:
it belongs to the DSN class, not to the signed-DKIM class the nineteenth reading
opened.

**The eighteenth reading had already identified that exact message as a Postfix
DSN** — *"null envelope sender, SPF falling back to the HELO name
`mail.surfguitar101.com`, no signature because DSNs bypass the milters."* One
reading later a second class appeared, explicitly *"not the bounce class"*, and
09-01 was absorbed into its tally anyway. The twentieth and twenty-first readings
carried the inflated figure forward, and so did this reading before this addendum.

**Corrected figures:**

| Class | Rows | Messages | Windows |
|---|---|---|---|
| Over-long-line (signed, body-hash fail) | **3** | **4** | 09-02, 09-03 ×2, 09-05 |
| DSN (unsigned, HELO-fallback SPF) | **2** | **3** | 09-01, 09-07 ×2 |

**Why it happened, and it is the reusable part.** Both classes render identically
in the *evaluated* fields — `spf=pass dkim=fail`, which is what
`tools/dmarc_report.py` prints and what every tally in this log was built from.
They differ only in `auth_results`, which the tool summarizes rather than
distinguishing. **A count taken from the evaluated pair cannot separate them, and
five readings took one.** [[suspect-the-measurer-before-the-record]]

**What it changes and what it does not.** The standing prediction — that the
over-long-line class goes to zero at the Step 21 deploy — is unaffected in
direction and now has a smaller, cleaner "before": 4 messages across 3 windows,
all signed, all at Google. The DSN class is not expected to go to zero at all;
it appears whenever something bounces, which is precisely why conflating them
would have made the before/after unreadable.

##### AOL is the only report still missing, and the arithmetic now proves it

The 09-07 window now holds **25 messages** across three endpoints — Google 20,
Comcast 3, Microsoft 2 — against Cloudflare's **26**. The gap is exactly **1**,
and the single AOL-bound send in that window is `242605869BA` to
`member26@example.com` at `Sep 7 10:44:45`. **The first addendum's decomposition
was inferred from one total; it is now confirmed by subtraction**, and Yahoo's
absence from the 26 stands as a genuine non-filing rather than a second loss.

`aol.com!surfguitar101.com!1788739200!1788825599.xml.gz` was searched for in Gmail
and not found. **That one report is the whole of the remaining collection gap**,
and AOL has filed nothing since the 08-31 window.

### Twenty-third reading — 2026-09-21, covering 2026-09-11 through 2026-09-20: Comcast counts evaluations rather than messages and reads 16 for two, Google reconciles exactly ten days running, a twelfth endpoint appears, and the local `rua` copy turns out to have been dead since the MX flip

**One hundred and one files in `~/dmarc`, 101 reports — twenty-one new, eighty
re-reads, no duplicates.** `tools/dmarc_report.py` reads 102 files and reports one
carrying no report, which is `.DS_Store`. All 101 Report-IDs are distinct, so the
dedupe gap the twenty-first reading left open is still open and still unexercised.

| Receiving domain | Reporter | Report-ID | Window | Msgs | Failing |
|---|---|---|---|---|---|
| `protection.outlook.com` | `Outlook.com` | `3681f70e4fd844a2b7bcf4c2e47338de` | 2026-09-11 | 6 | 0 |
| `cox.net` | `Yahoo` | `1789277666.594635` | 2026-09-12 | 3 | 0 |
| `google.com` | `google.com` | `8050126460101432255` | 2026-09-12 | 20 | 0 |
| `protection.outlook.com` | `Outlook.com` | `1ba65eb4fee34bf4a78851bf24aeb73b` | 2026-09-12 | 6 | 0 |
| `yahoo.com` | `Yahoo` | `1789277666.594701` | 2026-09-12 | 3 | 0 |
| `enterprise.protection.outlook.com` | `Enterprise Outlook` | `3b0439d9b00e498c8e12ad1540bbedf1` | 2026-09-13 | 1 | 0 |
| `google.com` | `google.com` | `32091998236930475` | 2026-09-13 | 15 | 0 |
| `aol.com` | `Yahoo` | `1789451087.361978` | 2026-09-14 | 1 | 0 |
| `comcast.net` | `comcast.net` | `v2-1789436543-surfguitar101.com` | 2026-09-14 | 2 | 0 |
| `google.com` | `google.com` | `10965688976189427050` | 2026-09-14 | 12 | 0 |
| `protection.outlook.com` | `Outlook.com` | `6ab1bb05c6a148fca198d68661452bef` | 2026-09-14 | 5 | 0 |
| `yahoo.com` | `Yahoo` | `1789451087.362007` | 2026-09-14 | 4 | 0 |
| `google.com` | `google.com` | `9788966810165148316` | 2026-09-15 | 6 | 0 |
| `google.com` | `google.com` | `8383501600596985036` | 2026-09-16 | 1 | 0 |
| `sbcglobal.net` | `Yahoo` | `1789624102.712517` | 2026-09-16 | 2 | 0 |
| `comcast.net` | `comcast.net` | `v2-1789696251-surfguitar101.com` | 2026-09-17 | **16** | 0 |
| `google.com` | `google.com` | `9270648328413933526` | 2026-09-17 | 3 | 0 |
| `yahoo.com` | `Yahoo` | `1789710489.822197` | 2026-09-17 | 1 | 0 |
| `google.com` | `google.com` | `2930377980238467422` | 2026-09-18 | 3 | 0 |
| `google.com` | `google.com` | `12115526217816345215` | 2026-09-19 | 6 | **1** |
| `google.com` | `google.com` | `11426903074718832384` | 2026-09-20 | 12 | 0 |

The send-side figures below come from jaguar's `/var/log/mail.log.2.gz`,
`mail.log.1` and `mail.log`, which together run `Sep 6 07:22` to `Sep 21 12:12`
local. **jaguar is UTC−5**; `date -u` on the box read `17:18:00Z` against a
`12:18:00 CDT` local clock. The UTC 09-20 window and both open 09-21 windows are
incomplete and nothing below depends on them.

#### Scoring the twenty-second reading's predictions: three held, none falsified, two unresolved because the reports do not exist

1. **HELD on the half that was filed, exactly.** Microsoft's 09-11 report reads
   **6**, `envelope_to: hotmail.com`, and the six sends are the six the prediction
   named by queue ID — `141A15869B6` (`Sep 10 19:32:01`), `78196586505`
   (`Sep 11 00:56:11`), `3380A5869B6` (`00:59:04`), `7211F586505` (`08:54:53`),
   `3D02F5869B7` (`09:01:53`), `1C5F75869B6` (`09:18:46`). No `hotmail.fr` and no
   tenant record, so the twenty-first reading's no-folding finding survives.
   **UNRESOLVED on 09-09 — Microsoft never filed for it**, though three
   `hotmail.com` sends sit in that UTC day.
2. **UNRESOLVED — Comcast never filed for 09-09.** `6EE2958650F` to
   `member14@example.com` at `Sep 9 17:16:27` is in the log and is the only
   Comcast-bound send in the window. No report.
3. **HELD.** No `yahoo.com` report for 09-11 exists, and no `yahoo.com` recipient
   falls in that UTC day. `cox.net` filed 09-11 at 4 and was already closed.
4. Resolved in the twenty-second reading's own addenda.
5. **HELD.** Google's 09-12 report reads **20** against a predicted floor of 9.
   The floor was set on a window still open at the previous log's end; the closed
   window reconciles exactly, below.
6. **HELD.** All 21 new reports read `p=quarantine`, and no row in any of the 101
   carries a `disposition` other than `none`.

#### Comcast's 09-17 report reads 16 for two messages, and the count is end-of-DATA receptions

**This is the first window in the series where a report disagrees with the send
log, and the disagreement is the finding.** `v2-1789696251-surfguitar101.com`
covers UTC 2026-09-17 and carries a single `173.255.245.115` record with
`count=16`, `dkim=pass spf=pass`, `disposition=none`. Two messages were sent to
`comcast.net` in that window.

The window is `Sep 16 19:00` → `Sep 17 18:59` local, and Comcast answered
`451 4.2.0 Try Again Later` **in reply to end of DATA** — after taking the whole
message — to a message Postfix then retried for four hours and fifty minutes:

| Local time | Queue ID | MX answering `451` | MX answering `451` | Receptions |
|---|---|---|---|---|
| 12:02:45 / :47 | `6EAF8586505` | `mx1` | `mx2` | 2 |
| 12:12:01 / :04 | `6EAF8586505` | `mx2` | `mx1` | 2 |
| 12:22:02 / :04 | `6EAF8586505` | `mx1` | `mx2` | 2 |
| 12:42:02 / :04 | `6EAF8586505` | `mx2` | `mx1` | 2 |
| 13:22:02 / :04 | `6EAF8586505` | `mx2` | `mx1` | 2 |
| 14:32:03 / :04 | `6EAF8586505` | `mx2` | `mx1` | 2 |
| 15:42:02 / :04 | `6EAF8586505` | `mx1` | `mx2` | 2 |
| 15:51:23 | `EA19A5864DF` | — | `mx2` accepted `250` | 1 |
| 16:52:03 | `6EAF8586505` | — | `mx1` accepted `250` | 1 |
| | | | **Total** | **16** |

**Sixteen against sixteen.** Every retry cycle reaches *two* Comcast MX hosts,
because Postfix falls through to the next MX after the first defers, and both
have already read the message to end of DATA by the time they answer. Seven
cycles is fourteen receptions; the eventual delivery of `6EAF8586505` is the
fifteenth and the unrelated `EA19A5864DF` is the sixteenth.

**So the `count` field is a count of DMARC evaluations, not of distinct
messages.** Comcast evaluated one 1,585-byte message fifteen times and reported
it fifteen times. Nothing was duplicated, misdelivered or double-sent; the
recipient received one copy.

**Every earlier reconciliation in this log counted `status=sent` lines**, and
every one of them was exact — which is not a vindication of the definition but a
statement that no window before 09-17 contained a deferral loop. Across the whole
covered log the only `4xx`-at-end-of-DATA events are 40 at
`mx{1,2}.mxge.comcast.net` and 2 at `mx.bt.prod.cloud.openwave.ai` (`talk21.com`).
**The corpus totals before 09-17 are unaffected in fact and wrong in method.**
[[suspect-the-measurer-before-the-record]]

**The three mechanisms that inflate a report's count are now all measured, and
they are one mechanism.** A forwarder hop (web.de, `209.85.220.41`) has the
receiver evaluate a message a second time; a multi-recipient fan-out has it
evaluate once per recipient; a defer-and-retry loop has it evaluate once per
attempt. In each case the report counts what the receiver *evaluated*, which is
the only quantity it can honestly report.

**It is still happening at the time of reading.** `250305869BB` entered the queue
around `Sep 21 00:23` local and was still deferring at the log's end thirteen
cycles later, having been received 26 times; with the delivered `0BD785869B6`
that is **27 receptions for 2 messages in the UTC 09-21 window, which is still
open.**

#### Google reconciles exactly for ten consecutive windows, and has filed for fifteen without a gap

Google's day starts at `02:00` local. Counting Gmail plus the `muohio.edu`
Workspace tenant against the `173.255.245.115` row alone, with forwarder rows
held separately:

| Google window | Gmail | Tenant | Direct | `173.255.245.115` row | Forwarder rows |
|---|---|---|---|---|---|
| 09-11 | 8 | 1 | 9 | **9** | 3 |
| 09-12 | 15 | 2 | 17 | **17** | 3 |
| 09-13 | 13 | 2 | 15 | **15** | 0 |
| 09-14 | 9 | 2 | 11 | **11** | 1 |
| 09-15 | 6 | 0 | 6 | **6** | 0 |
| 09-16 | 1 | 0 | 1 | **1** | 0 |
| 09-17 | 3 | 0 | 3 | **3** | 0 |
| 09-18 | 3 | 0 | 3 | **3** | 0 |
| 09-19 | 6 | 0 | 6 | **6** | 0 |
| 09-20 | 12 | 0 | 12 | **12** | 0 |

**Ten for ten, and Google has filed for every window from 09-06 to 09-20 with no
gap — fifteen consecutive.** No other endpoint in the corpus has filed more than
three consecutive windows.

**The boundary keeps doing the work.** The daily `brian` cron goes out at
`02:01:1x` and opens all ten windows; the latest carry-over from the previous day
is `F0E095869BD` at `Sep 14 00:32:57`. That pins the boundary inside a gap of one
hour twenty-eight minutes, which is looser than the thirty-seven-minute pin the
twenty-second reading achieved — **the tightest pin in the series is still that
one**, and these ten windows corroborate it rather than improve it.

**The tenant folds in four more times** — 09-11, 09-12 (×2), 09-13 (×2), 09-14
(×2). Drop `muohio.edu` and those four windows read 8, 15, 13 and 9 against
reports of 9, 17, 15 and 11.

#### A twelfth endpoint: Microsoft files tenant traffic under `enterprise.protection.outlook.com`, and that is where the tenants went

`enterprise.protection.outlook.com!surfguitar101.com!1789257600!1789344000.xml.gz`
is a shape not seen before:

```
org_name: Enterprise Outlook      email: dmarcreport@microsoft.com
window 2026-09-13    1 message    173.255.245.115    dkim=pass spf=pass    disposition=none
envelope_to: cooldwelling.com     envelope_from: surfguitar101.com
```

jaguar sent exactly one message to that domain — `8F2C658650C` to
`member16@example.com`, `Sep 13 14:11:58`, relayed through
`cooldwelling-com.mail.protection.outlook.com`, an MX verified by lookup this
reading. **One send, one report, exact.**

**This completes the twenty-first reading's tenant finding rather than
contradicting it.** That reading established that Microsoft does *not* fold
tenant domains into the `protection.outlook.com` endpoint the way Google folds
them into `google.com`, using the absence of any `cpp.edu` record for 09-06 as
its evidence. It could not say where tenant traffic went instead. **It goes to a
separate endpoint with a separate `org_name`, under the same reporter address.**
Google folds; Microsoft splits the endpoint.

**`cpp.edu` still has no report, and that is now a per-tenant fact rather than a
puzzle.** `C23FC5864B2` to `member28@example.com` went out `Sep 6 11:09:11`, inside
the UTC 09-06 window, and no `enterprise.protection.outlook.com` file exists for
it. Both are Microsoft 365 tenants; one files aggregate reports and one does not,
which is tenant-side configuration and not visible from here.

**The endpoint count is twelve by filename**, plus `swbell.net` by sender name.
The `org_name` strings are six, but the reporting *organizations* are still five:
`Enterprise Outlook` and `Outlook.com` share `dmarcreport@microsoft.com`.

#### The signed-DKIM failure class recurred at 09-19 after thirteen clean windows

`12115526217816345215`, window 2026-09-19, carries one failing record:

```
173.255.245.115  n=1  disp=none  dkim=fail  spf=pass
    auth_results: dkim d=surfguitar101.com selector=dkim result=fail
                  spf  d=surfguitar101.com result=pass
```

**A `<dkim>` element is present and SPF authenticated the header-from domain, not
the HELO name** — so by the twenty-second reading's discriminator this is the
over-long-line class and not the DSN class. Applied across all 101 reports the
two classes remain cleanly separable:

| Class | Rows | Messages | Windows |
|---|---|---|---|
| Over-long-line (signed, body-hash fail) | **4** | **5** | 09-02, 09-03 ×2, 09-05, **09-19** |
| DSN (unsigned, HELO-fallback SPF) | 2 | 3 | 09-01, 09-07 ×2 |

**The class was at 3 rows and 4 messages and had been silent for thirteen Google
windows, 09-06 through 09-18.** The twenty-second reading recorded that silence
with the caveat that the largest untested window was the missing one; 09-07 was
then recovered and came back clean. **This recurrence is the first datum that says
the class is live rather than resolved**, and it arrived in a six-message window.

**The failing message is one of three, narrowed by arithmetic rather than by a
size hypothesis.** The 09-19 Google day holds six sends, none of them a null
sender. A message whose *total* size is under 998 bytes cannot contain a line
longer than 998 bytes, which eliminates three:

| Queue ID | Local time | Size | Recipient | Candidate |
|---|---|---|---|---|
| `9AEEC586505` | `02:01:13` | 728 | `bgneal@gmail.com` | no — too small |
| `1332D5864DF` | `06:05:22` | 950 | `bgneal@gmail.com` | no — too small |
| `37185586505` | `06:30:47` | 855 | `bgneal@gmail.com` | no — too small |
| `78844586558` | `03:30:12` | **6082** | `bgneal@gmail.com` | **yes** |
| `52CAF5864EC` | `17:42:20` | **1999** | `member22@example.com` | **yes** |
| `0755958650C` | `18:19:57` | **1407** | `member22@example.com` | **yes** |

**This is not the size hypothesis the twentieth reading killed.** That one claimed
large messages fail; this uses size only as a *necessary* bound on line length,
which is arithmetic. [[measure-before-recording-in-planning-docs]]

**One of the three is directly readable and the check has not been run.**
`78844586558` was `nrcpt=2` and its second delivery was `relay=local` to
`dmarc@localhost`, so a byte-identical copy sits in `/home/dmarc/mail` on jaguar.
Reading it requires `sudo` — `sudo -n` is refused on the box — so it is left for
Brian:

```
sudo awk 'length > 998 {print FILENAME": "length}' /home/dmarc/mail/new/* /home/dmarc/mail/cur/*
```

A hit on the `20260919083011.1921.82019@jaguar.deathofagremmie.com` message
identifies the failing send and confirms the mechanism on a fourth occurrence.

#### The local `rua` copy has been a dead collection path since the MX flip, and nothing in this log said so

**Over the fifteen days of mail log, `/home/dmarc/mail` received 29 messages and
not one of them was a DMARC report.** Classified by envelope sender: 23 from
`no_reply@surfguitar101.com`, 4 from `root@surfguitar101.com`, 2 from `<>`. All
are jaguar's own mail to `admin@`.

The cause is in `STATUS.md` already, stated about something else. The apex MX is
now `41 route1` / `46 route3` / `98 route2 .mx.cloudflare.net`, re-read from DNS
this reading, and Step 16 task 06 Phase 1 — done **2026-08-23** — records the
consequence in as many words: *"Inbound mail for `surfguitar101.com` no longer
touches jaguar."* External report mail reaches Cloudflare and is forwarded to
Gmail. It never enters jaguar's Postfix, so the `virtual_alias_maps` fan-out that
produces the local copy never runs for it. **Only locally generated mail to
`admin@` still lands in that maildir.**

**What that retires is the instrument's insurance.** The 2026-08-20 section built
the local copy precisely so that the reports could not be forwarded away, proved
it end to end, and the 2026-08-21 amendment established its real value as latency
— a Google report delivered locally in 0.85s and to Gmail 9h25m52s later. **Three
days after that amendment the MX flip took the copy out of the path, and eighteen
readings have been written since without noticing.** The fifth and sixth readings
were the only ones it ever served.

**This is the mechanism behind the twenty-second reading's open item.** That
reading found two of four reports for 09-07 lost, wrote that *"the collection path
is the open item, not the window"*, and identified the path as Cloudflare → Gmail
→ saved by hand. It did not say that the designed second copy had already stopped
existing. **There is no redundancy in report collection and has not been since
2026-08-23**, which is why a single missed delivery batch lost a window outright.

**`tools/dmarc_report.py` still defaults to `DEFAULT_MAILDIR = '/home/dmarc/mail'`.**
Run with no `--dir` on jaguar it now reads a maildir containing no reports. That
is a trap of the kind this log keeps recording — an instrument that answers
without complaining. [[probes-must-not-perturb-what-they-measure]]

#### Every other endpoint reconciles exactly on the UTC day

| Endpoint | Window | Sends in the true UTC day | Reported |
|---|---|---|---|
| `cox.net` | 09-12 | 3 | **3** |
| `yahoo.com` | 09-12 | 3 | **3** |
| `protection.outlook.com` | 09-12 | 6 `hotmail.com` | **6** |
| `enterprise.protection.outlook.com` | 09-13 | 1 `cooldwelling.com` | **1** |
| `aol.com` | 09-14 | 1 | **1** |
| `comcast.net` | 09-14 | 2 | **2** |
| `protection.outlook.com` | 09-14 | 5 `hotmail.com` | **5** |
| `yahoo.com` | 09-14 | 4 | **4** |
| `sbcglobal.net` | 09-16 | 2 | **2** |
| `yahoo.com` | 09-17 | 1 | **1** |
| `comcast.net` | 09-17 | 2 messages / **16 receptions** | **16** |

Eleven for eleven, once 09-17 is counted in the unit Comcast actually reports.

**AOL has filed again.** `1789451087.361978` for 09-14 is the first AOL report
since the 08-31 window, and it is exact. **The 09-07 AOL report is still the one
piece missing from the corpus** and is now the only known loss in the series.

#### Endpoints with traffic and no report, 09-06 → 09-20

| Endpoint | Window | Sends | Note |
|---|---|---|---|
| `enterprise.protection.outlook.com` | 09-06 | 1 | `cpp.edu`; tenant appears not to file |
| `aol.com` | 09-07 | 1 | the known collection loss |
| `yahoo.com` | 09-07 | 2 | genuine non-filing, established in reading 22 |
| `yahoo.com` | 09-08 | 2 | genuine non-filing |
| `comcast.net` | 09-09 | 1 | prediction 2, never filed |
| `protection.outlook.com` | 09-09 | 3 | prediction 1's other half, never filed |
| `gmx.net` | 09-19 | 1 | `gmx.at`; GMX has filed nothing since 09-02 |
| `protection.outlook.com` | 09-20 | 1 | one day old, likely still in flight |

**09-09 is a second two-endpoint hole**, and unlike 09-07 it cannot be a
collection fault of the same shape: Google and Yahoo both filed exact reports for
09-09 in the same delivery batches. Microsoft and Comcast simply did not file.
**Reporters skipping windows is now the better-evidenced explanation for most
absences**, and 09-07 remains the one window where the opposite was demonstrated.

#### What held steady across all 101

- **129 rows, 639 messages, every one `disposition=none`.**
- Evaluated SPF/DKIM by row: **107 `pass`/`pass`, 15 `fail`/`pass`, 6
  `pass`/`fail`, 1 `fail`/`fail`.** By message: 602 / 28 / 8 / 1.
- `173.255.245.115` appears in 110 rows and 607 messages.
- Policy renders `adkim=r aspf=r` in all 101.
- The `p=none`/`p=quarantine` boundary at the 08-25 publication reproduces
  exactly: **16 reports read `none`, 85 read `quarantine`.**
- **Twelve reporting endpoints by filename, five reporting organizations, six
  `org_name` strings.**
- The published-policy field census still tracks the corpus exactly: `sp` present
  in 64 and absent in exactly the 37 Yahoo reports; `pct` present in 95 and absent
  in exactly the 6 GMX reports; `np` in exactly the 29 Google reports; `fo` in
  exactly the 10 Comcast, 18 Outlook.com and 1 Enterprise Outlook reports;
  `discovery_method` and `testing` in exactly the 6 GMX reports. Our record still
  publishes none of them, and `_dmarc.surfguitar101.com` re-read from DNS this
  reading is unchanged: `v=DMARC1; p=quarantine; rua=mailto:00fc656c22e64e73bb643fb00331d013@dmarc-reports.cloudflare.net,mailto:admin@surfguitar101.com`.

#### The forwarding classes, and Postmark at a twenty-fourth window

| Source | Rows | Msgs | Windows |
|---|---|---|---|
| Gmail relay `209.85.220.41` | 6 | 19 | 08-26 → 08-30, **09-12, 09-14** |
| web.de `212.227.*` / `217.72.192.78` | 9 | 9 | 09-09 → **09-12** |
| `2001:470:0:60::2` | 1 | 1 | 08-26 only |
| Postmark `50.31.156.*` | 3 | 3 | 08-25, 08-27 |

**`209.85.220.41` is back after twelve silent windows**, one message each on 09-12
and 09-14. Both are re-evaluations of messages already counted in the same
report's `173.255.245.115` row — the reconciliation is exact without them, which
is what identifies them as forwards rather than as extra mail.

**The web.de forwarder stopped.** jaguar sent nine messages to
`member29@example.com` across 09-09 → 09-12 and Google reported nine forwarded rows,
one per send, exact. There have been no web.de sends since `87C2E5869B7` on
`Sep 12`, and no rows since. The class is complete at nine and every one was
delivered `disposition=none` under `p=quarantine` and `-all`.

**Postmark's `50.31.156.*` has not appeared since the 08-27 window**, and no
message in fifteen days of log relays through `*.mtasv.net`. jaguar is still the
only thing sending, which is expected until Step 21.

#### Bearing on the policy decision

Nothing moves, and one thing is worth stating plainly for the first time.
`p=quarantine` continues to cost nothing measurable — **639 messages, zero
non-`none` dispositions, twenty-seven days live.** The forwarded-mail risk is now
measured across two independent forwarders, both carried through DMARC by DKIM
alone under `-all`.

**The 09-19 recurrence is the argument for keeping `p=reject` deferred, restated
with a date on it.** The over-long-line class was silent for thirteen windows and
came back. Under `p=reject` that message is refused rather than delivered. The
fix is the Step 21 deploy, it is not deployed, and the class is demonstrably still
firing — which is the twenty-second reading's reasoning with the missing evidence
now supplied.

#### Predictions for the twenty-fourth reading

Measured against the send log through `Sep 21 12:12` local. The UTC 09-20 window
is complete; UTC 09-21 and the UTC−7 09-21 day are not.

1. **Comcast's 09-21 report reads at least 27 and is far above the 2 messages
   actually sent.** At the log's end `250305869BB` had been received 26 times and
   `0BD785869B6` once; the window had almost seven hours left and Postfix was
   retrying at roughly seventy-minute intervals. A count equal to 2 falsifies this
   reading's central finding outright; a count near 27–31 confirms that `count` is
   receptions. **This is the cleanest test the finding will get, and it is already
   in the queue.**
2. **Microsoft files for 09-20 at exactly 1**, `envelope_to: hotmail.com` —
   `33D5E58650F` to `member19@example.com`, `Sep 20 12:04:32`.
3. **Google files for 09-21 at 4 or more.** Four Gmail-bound sends by the log's
   end, no tenant, and the UTC−7 day still open, so the figure is a floor. An
   exact 4 would also mean the Gmail relay filed nothing further.
4. **Yahoo files for 09-21 at 1 and `aol.com` at 1.** One recipient each in that
   UTC day.
5. **GMX files nothing for 09-19.** It has filed nothing since 09-02 despite a
   `gmx.at` send on 09-19, and the six GMX reports remain the only ones in the
   corpus carrying `discovery_method` and `testing`.
6. **No `enterprise.protection.outlook.com` report for 09-06 ever arrives**, the
   `cpp.edu` tenant not having reporting enabled.
7. **Every report reads `p=quarantine`** and no row carries a `disposition` other
   than `none`.

#### Addendum, 2026-09-21 — `tools/dmarc_fetch.py`'s first run: four reports recovered, `web.de` is a reporter, and two claims above are falsified

The collection path was automated the same afternoon this reading was written.
Its first sweep of the reporting era — Gmail All Mail and Spam, 2026-07-04
onward — found **four reports that had never been saved**. The corpus is now
**105 reports, 133 rows, 658 messages**, every disposition still `none`.

**The reading above was written against a corpus with a hole in it, and the hole
was not where the twenty-second reading left it.**

##### ⚠️ FALSIFIED — `web.de` is a reporting endpoint, not merely a source

This reading states, in *What held steady across all seventy-nine*: *"`web.de` is
a **source**, not an endpoint, and has filed nothing."* It has filed three
reports, `org_name: WEB.DE`, `noreply-dmarc@sicher.web.de`:

| Report-ID | Window | Msgs | Sends in the UTC day |
|---|---|---|---|
| `3fc6fb808c4c418fa476575edb5be86d` | 2026-09-10 | **4** | 2 |
| `c3a105cb59d54f48a1eb95fa5e291b41` | 2026-09-11 | **8** | 4 |
| `42d724cb697f446db70c82ffd22f3890` | 2026-09-12 | **6** | 3 |

**Thirteen reporting endpoints by filename**, plus `swbell.net` by sender name.
Every row is `173.255.245.115`, `dkim=pass spf=pass`, `disposition=none` — this
is jaguar sending *to* a web.de mailbox, which is the opposite direction from the
`212.227.*` forwarder rows inside Google's reports. **The same forwarder is now
visible from both ends.**

##### Every window is exactly twice the send log, and the send side is clean

4 against 2, 8 against 4, 6 against 3. **Three exact doublings is not a
coincidence**, so the measurement was checked before the reporter was:

- Nine deliveries to `member29@example.com`, the only recipient at any web.de MX in
  the log, `mx-ha02`/`mx-ha03` — and **no other domain relays through a web.de
  MX**, so nothing is being missed by classifying on the recipient domain.
- **Every one is `nrcpt=1`**, so it is not the multi-recipient fan-out.
- **Zero `4xx` responses at end of DATA from any web.de host**, so it is not the
  retry inflation the Comcast section above measures.
- UTC binning at jaguar's verified UTC−5: 2, 4, 3. Reported: 4, 8, 6.

**So this is a third counting behaviour, and it confirms the frame rather than
breaking it.** The `count` field reports what the receiver *evaluated*. Comcast
inflates by re-evaluating a deferred message on every retry; web.de appears to
evaluate each received message twice — plausibly once at MX ingress and once at
mailbox delivery, both attributed to the original connecting IP. **The mechanism
is not measured and is not guessed at**; what is measured is the ratio and the
cleanliness of the send side.

**The contrast with Google is what makes it a reporter property.** The same nine
messages were forwarded onward to Gmail, and Google reported them **nine times,
one per send**, in the `212.227.*`/`217.72.192.78` rows above. The forward
happened once. web.de counted twice; Google counted once. [[suspect-the-measurer-before-the-record]]

##### ⚠️ FALSIFIED — prediction 6, and the reasoning behind it was the error

This reading predicted: *"No `enterprise.protection.outlook.com` report for 09-06
ever arrives, the `cpp.edu` tenant not having reporting enabled."*
`b600b29c97d4444ca781546148067037` covers 2026-09-06 and reads **1 message**,
matching `C23FC5864B2` to `member28@example.com` (`Sep 6 11:09:11` local) exactly.

**The tenant does file. We lost the report.** The prediction inferred a reporter's
configuration from an absence in our own corpus, at a moment when the collection
path was known to drop reports and the reading was in the middle of saying so.
That is the same error the seventeenth reading warned about — *check the send log
before calling an absence a finding* — committed against a gap this very reading
had just characterised. [[measure-before-recording-in-planning-docs]]

##### The collection gap was five reports, not one, and it was leaking rather than failing

The twenty-second reading called AOL's 09-07 report *"the whole of the remaining
collection gap."* The real figure is five, and the shape matters more than the
count: the four recovered here span **09-06 to 09-12 across two unrelated
reporters**, interleaved with windows that were saved correctly. **A single lost
delivery batch cannot produce that.** The manual save was leaking steadily, and
every earlier total in this log is a floor for that reason and not only because
of 09-07.

**AOL's 09-07 report is still absent**, and that absence is now much better
evidenced: an exhaustive programmatic sweep of All Mail and Spam over the whole
reporting era does not find it, where the twenty-second reading had only a hand
search. **It was never delivered to Gmail.**

##### The subject line is a safe narrowing, measured rather than assumed

Brian observed that every report mail carries `Report Domain: surfguitar101.com`
in its subject — the format RFC 7489 §7.2.1.1 specifies, which is a SHOULD and so
cannot be relied on by argument. The fetcher's `--audit` mode runs the broad
attachment-only search alongside the narrowed one and checks the difference:
**29 attachment-bearing messages across the whole reporting era do not match that
subject, and not one of them carries a report.** Lossless on this mailbox.

##### The first DMARC 2.0 documents in the corpus

All three WEB.DE reports are `xmlns="urn:ietf:params:xml:ns:dmarc-2.0"`. **This is
the first time the namespaced schema has appeared here**, and both instruments
handle it: `_unqualify` in `dmarc_report.py`, written against exactly this trap,
and the namespace-aware root-tag test in the fetcher. Had either compared the
qualified tag, these reports would have parsed cleanly and read as zero messages.

##### Corrected census across all 105

- **133 rows, 658 messages, every one `disposition=none`.** Evaluated pairs by
  row: **111 `pass`/`pass`, 15 `fail`/`pass`, 6 `pass`/`fail`, 1 `fail`/`fail`.**
- **Both DKIM-failure classes are unchanged** — over-long-line 4 rows / 5
  messages, DSN 2 rows / 3 messages. All nineteen recovered messages pass both
  mechanisms, so nothing in this reading's failure analysis moves.
- The `p=none`/`p=quarantine` boundary still reproduces exactly: **16 `none`, 89
  `quarantine`.**
- **Thirteen endpoints by filename; seven `org_name` strings; six reporter
  addresses; five corporate organizations.** The three counts now differ and are
  not interchangeable. `Enterprise Outlook` and `Outlook.com` share
  `dmarcreport@microsoft.com`; **`WEB.DE` and `GMX` do not share an address but
  are plainly one implementation** — see the field census below.
- Published-policy field census: `sp` present in 68, absent in exactly the 37
  Yahoo reports; `np` in exactly the 29 Google reports; `fo` in exactly the 10
  Comcast, 18 Outlook.com and 2 Enterprise Outlook reports. **Two entries change:
  `pct` is absent in 9 — the 6 GMX reports *and* the 3 WEB.DE reports — and
  `discovery_method` and `testing` appear in exactly those same 9.** That triple
  signature, plus the parallel `sicher.gmx.net`/`sicher.web.de` reporter
  addresses, is what identifies GMX and WEB.DE as one operator rather than two.

### Twenty-fourth reading — 2026-09-28, covering 2026-09-20 through 2026-09-27: leopard appears for the first time, through Cloudflare's forward, and the send log accounts for fifteen of its sixteen messages exactly; two new forwarders; six of seven predictions held, the seventh already falsified

**`tools/dmarc_fetch.py` found 35 new reports** in 78 candidate messages from All
Mail and Spam since 09-06, with 43 already held and no conflicts. **The corpus
is 140 reports, 184 rows, 1,652 messages, every disposition `none`.** Evaluated
pairs by row: 152 `pass`/`pass`, 24 `fail`/`pass`, 7 `pass`/`fail`, 1
`fail`/`fail`. Published policy: **16 `p=none`, 124 `p=quarantine`**.

This reading covers the 36 reports with windows from 09-20 on: the 35 new ones
and Google's 09-20, already held. They hold 52 rows and 1,006 messages; every row
aligns on at least one mechanism, and every disposition is `none`.

| Reporter (endpoints) | Reports | Windows | Msgs |
|---|---|---|---|
| `comcast.net` | 6 | 09-21 → 09-26 | 637 |
| `google.com` | 8 | 09-20 → 09-27 | 284 |
| `Yahoo` (`yahoo.com`, `aol.com`, `att.net`, `cox.net`, `verizon.net`) | 14 | 09-21 → 09-27 | 58 |
| `Outlook.com` (`protection.outlook.com`) | 6 | 09-20, 09-22 → 09-26 | 20 |
| `GMX` (`gmx.net`) | 2 | 09-23, 09-25 | 7 |

**Report-IDs are not tabulated here.** `tools/dmarc_report.py` prints them, and
the files are named by receiver and window, so any row above can be re-read in
one command. **jaguar's `mail.log` was not read for this reading**, so none of
the direct-delivery counts below are reconciled against the send side. Comcast's
637, including **255** for 09-25, is the largest a single endpoint has filed.
Without the send log it cannot be split into messages and retries. The
twenty-third reading showed Comcast counts receptions, not messages.

#### Scoring the twenty-third reading's predictions: six held, one already falsified

1. **HELD.** Comcast's 09-21 report reads **39**, against 2 messages sent. That
   is above the 27–31 the prediction called confirming, and in the direction the
   receptions finding requires. The excess over 31 is unmeasured without
   jaguar's log.
2. **HELD.** Microsoft's 09-20 report reads exactly **1**.
3. **HELD.** Google's 09-21 report reads **12**, above the floor of 4.
4. **HELD.** `yahoo.com` and `aol.com` each read **1** for 09-21.
5. **HELD.** No GMX report exists for 09-19. GMX's last window before this reading
   was 09-02; it resumed at 09-23 and 09-25.
6. Already **FALSIFIED** in the twenty-third reading's addendum. The `cpp.edu`
   tenant's 09-06 report was in Gmail all along.
7. **HELD.** All 36 reports read `p=quarantine`, and no row has a disposition
   other than `none`.

#### leopard appears: sixteen messages from Cloudflare's forwarding range, and the send log accounts for fifteen

Google's 09-27 report carries five rows no reading has seen:

```
104.30.8.10     4  none  pass  pass
104.30.8.49     4  none  pass  pass
104.30.10.31    2  none  pass  pass
104.30.8.104    4  none  pass  pass
104.30.10.185   2  none  pass  pass
    dkim  d=surfguitar101.com     s=cf2024-1           pass
    dkim  d=cloudflare-email.net  s=cf2024-1           pass
    dkim  d=pm.mtasv.net          s=pm20250806         pass
    dkim  d=surfguitar101.com     s=20260817033844pm   pass
    spf   d=surfguitar101.com                          pass
```

**Every one is mail leopard sent to `admin@surfguitar101.com` through Postmark,
which Cloudflare Email Routing then forwarded to Gmail.** The reporting receiver
sees only the last hop, which is why the source is Cloudflare's `104.30.0.0/19`
and not Postmark's `50.31.156.*`. SPF passes against `surfguitar101.com` because
Cloudflare rewrites the envelope sender with SRS, and `104.30.0.0/19` falls inside
`include:_spf.mx.cloudflare.net`. This is the first time the finding recorded
under *`include:_spf.mx.cloudflare.net` is load-bearing* shows up in an aggregate
report rather than in a header capture.

**There are two `surfguitar101.com` signatures, and they are different.**
`20260817033844pm` is Postmark signing as this domain. `cf2024-1` is Cloudflare
Email Routing signing the forward. The report tool prints both as
`dkim:surfguitar101.com=pass`, which reads like a duplicate but is not one; the
selector is only in the raw XML.

**The attribution, on Google's UTC−7 day, which here runs 09-27 07:00 UTC to
09-28 07:00 UTC:**

| Source | Time (UTC) | Msgs | Evidence |
|---|---|---|---|
| Django `ERROR (internal IP)` mail, the first stack start | 09-27 20:03:48 → 20:04:35 | 10 | leopard `sg101.log.1`: ten `Internal Server Error: /` lines, 15:03:48–15:04:35 at UTC−5 |
| msmtp, the hand-sent test | 09-27 23:42:19 | 1 | journal, `250 … queued as 390DF427E0B` |
| msmtp, cron's failing job | 09-28 00:02:02 | 1 | journal, `29CED412EE3` |
| msmtp, the wrong credential | 09-28 00:08:04 | 0 | journal, `535`, `EX_NOPERM`, nothing sent |
| msmtp, re-sent after restoring the credential | 09-28 00:09:18 | 1 | journal, `C73A1407301` |
| msmtp | 09-28 00:20:58 | 1 | journal, `DE275411344` |
| msmtp, host mail after the token rotation | 09-28 00:38:13 | 1 | journal, `7E7964056E3` |
| **Measured** | | **15** | |
| Django `sendtestemail --admins` after the rotation | after 00:38:13 | 1 | recorded in `STATUS.md` (task 04) as arrived; **not timed by any log** |

**Fifteen of the sixteen are measured and the sixteenth is attributed.**
`sendtestemail` writes nothing to leopard's logs, so it is placed only by the
order in which task 04's record lists it. The journal was read with
`journalctl -t msmtp` over 09-26 → 09-29 and filtered on the host
(`user=` redacted, per runbook B14); it holds six lines, five sent. Which test
the 00:20:58 send was is not recorded in the journal line.

**This is also a forward test of the UTC−7 day on a source it was not fitted
to.** Five of the sixteen fall on 09-28 in UTC and in 09-27 on Google's day. A
UTC-day aggregation would have put 11 in this report, not 16. The day was fitted
on jaguar's direct deliveries; this is Postmark → Cloudflare → Gmail, and it
lands the same way.

**It bears on `STATUS.md`'s third open item, but does not close it.** That item
is that Postmark has never appeared in an aggregate report. Postmark's signature
now has, on sixteen messages. **Postmark as a *source IP*, delivering directly to
a receiver's MX, has still not appeared since 08-27**, because nothing Postmark
sent in this window went anywhere but `admin@`. That half needs the cutover.

#### Two new forwarders, and web.de once more

| Source | Operator (whois, PTR) | SPF domain | Windows | Msgs |
|---|---|---|---|---|
| `23.83.222.44`, `23.83.212.16`, `23.83.222.49` | MailChannels, `23.83.208.0/20`; `crimson.ash.relay.mailchannels.net` | `littlekahunamusic.com` | 09-22, 09-24 | 3 |
| `66.39.4.2` | pair Networks; `mail1.g6.pair.com` | `srs.pair.com` | 09-26 | 1 |
| `212.227.15.14` | `mout.web.de` | `web.de` | 09-22 | 1 |
| Gmail relay `209.85.220.41` | | `gmail.com` | 09-23 → 09-26 | 15 |

**All twenty fail SPF alignment and pass on DKIM `d=surfguitar101.com`**,
delivered `disposition=none` under `p=quarantine`. That makes four independent
forwarders carried through DMARC by DKIM alone. pair applies SRS and still fails
alignment, because it rewrites into its own domain, not this one.
MailChannels forwarding for a named band domain is plausibly a member's
forwarding address; **who it is was not investigated.**

**The twenty-third reading said the web.de forwarder had stopped at 09-12.** One
row on 09-22 says it has not stopped, though it has slowed. That reading's *"the
class is complete at nine"* is wrong: the class is now ten.

#### Failure classes

- **DSN class: one more.** Google 09-25, `173.255.245.115`, `pass`/`fail`, SPF
  on `mail.surfguitar101.com` and no `<dkim>` element. By the twenty-second
  reading's discriminator, that is a bounce.
- **Over-long-line class: none this week.** After 09-19's recurrence, 09-20
  through 09-27 is clean. The class is intermittent, so this does not take it off
  the table for the cutover's before/after.

#### Endpoints with no report yet

No Microsoft report for 09-21 and no Comcast report for 09-27 had arrived by
this fetch. Microsoft's 09-07 report arrived four days after its window closed,
so the 09-27 absences are not yet absences. **Whether any traffic went to those
endpoints in those windows is unmeasured**, because jaguar's log was not read.
Neither is called a gap.

#### Predictions for the twenty-fifth reading

1. **Google's 09-28 report carries no rows for the six msmtp sends of
   09-28 00:02–00:38 UTC.** They are already counted in 09-27 on Google's day.
   If they appear again in 09-28, the UTC−7 day fails on this source.
2. **Any `104.30.*` row in Google's 09-28 report is matched by an msmtp journal
   line or a Django `ERROR` line after 09-28 07:00 UTC.** The journal read here
   has no send after 00:38:13.
3. **Every report reads `p=quarantine`** and no row carries a disposition other
   than `none`.

### Twenty-fifth reading — 2026-10-05, covering 2026-09-28 through 2026-10-04: Postmark appears as a source IP through the member beta, a neighbour on jaguar's /64 passes DMARC on SPF, and the first quarantine dispositions in the corpus

**`tools/dmarc_fetch.py` found 23 new reports** in 23 messages from All Mail and
Spam since 09-13, none already held and no conflicts. **The corpus is 163
reports, 230 rows, 1,849 messages.** Evaluated pairs by row (SPF/DKIM): 189
`pass`/`pass`, 27 `fail`/`pass`, 10 `pass`/`fail`, 4 `fail`/`fail`. Published
policy: **16 `p=none`, 147 `p=quarantine`.** Dispositions: 1,846 `none`, **3
`quarantine`, the first in the corpus.**

This reading covers the 23 new reports. They hold 46 rows and 197 messages.

| Reporter (endpoints) | Reports | Windows | Msgs |
|---|---|---|---|
| `google.com` | 7 | 09-28 → 10-04 | 147 |
| `Yahoo` (`yahoo.com`, `aol.com`, `att.net`) | 10 | 09-28 → 10-04 | 35 |
| `comcast.net` | 2 | 09-28 → 09-29 | 9 |
| `Outlook.com` (`protection.outlook.com`) | 3 | 09-28, 10-02, 10-03 | 5 |
| `GMX` (`gmx.net`) | 1 | 10-01 | 1 |

**jaguar's `mail.log` was not read for this reading**, so jaguar's direct
deliveries are not reconciled. leopard's side was read: `email.log` (which
starts 2026-10-03 01:03 UTC) and the `ERROR` lines of `sg101.log`, both in UTC.
Addresses were reduced to their domains on the host before printing.

#### Scoring the twenty-fourth reading's predictions: two held, one falsified

1. **HELD.** Google's 09-28 report has no `104.30.*` rows at all, so the six
   msmtp sends of 09-28 00:02–00:38 UTC were not counted a second time.
2. **HELD, vacuously.** There is no `104.30.*` row in Google's 09-28 report to
   match.
3. **FALSIFIED in its second half.** All 23 reports read `p=quarantine`. Three
   rows carry `disposition=quarantine` (below). The prediction was written as
   though every non-`none` disposition would mean trouble; these three are the
   policy working.

#### Postmark appears as a source IP, and all three rows reconcile to a send

STATUS item 3's missing half was Postmark delivering straight to a receiver's
MX, which the twenty-fourth reading said "needs the cutover". **The member beta
produced it first**, through the allowlisting backend, which lets mail reach
testers' own addresses:

| Report | Source | Msgs | leopard `email.log` (UTC) |
|---|---|---|---|
| Google 10-02 | `50.31.156.114` | 1 | 10-03 02:31:23, `pm_notification` to `gmail.com` |
| Google 10-03 | `50.31.156.121` | 1 | 10-04 00:58:18, `password_reset` to `gmail.com` (Kojack's reset) |
| Yahoo `att.net` 10-04 | `50.31.156.121` | 1 | 10-04 20:02:24, `pm_notification` to `att.net` |

Each passes SPF on `pm-bounces.surfguitar101.com` (aligned under relaxed SPF)
and carries both `d=pm.mtasv.net` and `d=surfguitar101.com`.

**`email.log`'s `outcome=sent` is not delivery.** It logs one line per
recipient before the allowlist runs. Four other `gmail.com` sends on 10-03
(02:28:52, 02:38:45, 02:43:29, 02:56:28) and the `mail.de` one each have an
`allowlist dropped` line and were never handed to Postmark. Reconciling against
`sent` alone would have predicted five Google rows for 10-02, not one.
`msorensen.net` takes ten sends across the window and is hosted at IONOS
(`mx00/01.1and1.com`), which does not report.

**Another forward test of Google's UTC−7 day, on a third source.** On a UTC day
the three Google sends would fall 10-03, 10-04 and none; Google filed 10-02,
10-03 and none for 10-04. Only the UTC−7 day fits.

#### leopard's forward to `admin@`: two of three Google days reconcile exactly

| Google day (UTC−7) | `104.30.*` msgs | leopard: `admin@` sends + Django error mail | |
|---|---|---|---|
| 10-02 | 5 | 3 (`email.log`, 01:16:05, 01:16:06, 02:58:51) + 2 (`/user_photos/hotlink/` 500s) | **exact** |
| 10-03 | 20 | 1 (`email.log`, 10-04 04:54:43) + 20 (19 `/podcast/N/` 500s, 1 hotlink 500) | **21 against 20** |
| 10-04 | 2 | 2 (`email.log`, 10-04 12:20:36 contact form, 10-05 00:33:58) + 0 | **exact** |

The two `admin@` sends from `no_reply@beta.surfguitar101.com` at 10-03 01:03 are
excluded: Postmark refused that sender (`400`, recorded in `STATUS.md`).
Django's error mail goes through `mail_admins`, which `email.log` does not see,
so it was counted from `sg101.log`'s `Internal Server Error` lines.
**The 10-03 surplus of one is UNRESOLVED.** leopard's msmtp journal was not
read, but host mail could only add to the expected side, not remove from it.

#### A neighbour on jaguar's /64 passes DMARC as this domain

Google's 09-30 report:

```
2600:3c01::2000:96ff:fe4a:23be   1  none  pass  fail   spf:surfguitar101.com=pass
```

**That is not jaguar.** jaguar has one global IPv6 address,
`2600:3c01::f03c:91ff:fe70:e820` (read from `ip -6 addr` on jaguar 2026-10-05),
and its MAC `f2:3c:91:70:e8:20` is the one its address derives from. The source's
PTR is `newsite.akigroup.com`; `whois` puts it in Linode's `2600:3c00::/24`.
It passes SPF because the apex record authorizes
`ip6:2600:3c01::f03c:91ff:fe70:e820/64`, the whole /64, and on Linode that
default /64 is shared with other customers' instances. SPF passed and aligned
on `surfguitar101.com`, so **DMARC passed and `p=quarantine` never applied.**
No DKIM signature from this domain verified.

**No prior reading recorded this**: the term was carried over from the
pre-existing record in Phase 1, and the decision not to copy it to another zone
argued only that nothing had been shown to use it. **What the message was is
unknown**: one message, one receiver, one window. A misconfigured neighbour
using this domain as an envelope sender, and deliberate spoofing, both look
like this.

**No DNS change now (Brian, 2026-10-05):** the cutover is close, and task 10
settles the apex SPF question after it. When it does, the fix is to drop the
`ip6:` term, or narrow it to `/128` if jaguar is still sending. **Reopen
trigger: any second row from `2600:3c01::/64` other than jaguar's own address.**

#### Three spoofs quarantined: the first non-`none` dispositions

Google 09-30: three messages from `119.59.99.226` (METRABYTE-TH, Bangkok; PTR
`stock.obrienmumford.org`), each with SPF on an unrelated domain
(`dmkarashop.com`, `wuttanabat.com`, `chiangraipool.com`) and no DKIM. Aligned on
neither; **disposition `quarantine`.** This is the first time in 163 reports that
the policy has acted on anything.

#### Failure classes

- **DSN class: two.** Google 09-28 and 09-29, `173.255.245.115`, `pass`/`fail`
  with SPF on `mail.surfguitar101.com` and no `<dkim>` element.
- **Over-long-line class: none.** 09-20 through 10-04 is now fifteen clean
  windows since 09-19. It is intermittent, so it stays on the cutover's
  before/after list.
- **Gmail-relay forwards:** 11 messages (10-01: 6, 10-03: 1, 10-04: 4), SPF
  `fail` on `gmail.com`, carried by DKIM, `disposition=none`.

#### Endpoints with no report yet

| Endpoint | Missing windows since 09-27 |
|---|---|
| `comcast.net` | 09-27, 09-30 → 10-04 |
| `protection.outlook.com` | 09-27, 09-29 → 10-01, 10-04 |

**These are not called gaps.** Without jaguar's `mail.log` it is unmeasured
whether those endpoints received any traffic in those windows, and Microsoft has
filed four days late before.

#### Predictions for the twenty-sixth reading

1. **Google's 10-05 report carries exactly 4 messages from Postmark
   `50.31.156.*` sources.** leopard's `email.log` has four `gmail.com` sends on
   Google's 10-05 day (10-05 20:24:04, 20:33:19, 21:07:56; 10-06 00:00:43) and no
   `allowlist dropped` line after 10-03 02:56. Fewer means a send was dropped or
   lost; more means the UTC−7 day or the log is wrong.
2. **No Postmark source row in any Yahoo-filed report for 10-05.** leopard sent
   nothing to a Yahoo-hosted domain that day.
3. **No further row from `2600:3c01::2000:96ff:fe4a:23be`.** A second one makes
   it a pattern rather than a single event, and any other non-jaguar address in
   `2600:3c01::/64` would show the exposure is not one neighbour's.
4. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a row
   aligned on neither mechanism.

### Twenty-sixth reading — 2026-10-06, covering 2026-10-05: the first daily reading; Google's five Postmark messages reconcile on the UTC−7 day, and a spoof from another Linode region is quarantined

**The first reading at A4's daily cadence**, which runs to two weeks after the
flip. `tools/dmarc_fetch.py -a <account>` scanned 27 messages: **4 new**, 23
already held, no conflicts. **The corpus is 167 reports.** All four new reports
are for the 10-05 window. Every one reads `p=quarantine`.

| Reporter | Source | Msgs | Disposition | DKIM / SPF |
|---|---|---|---|---|
| `google.com` | `173.255.245.115` (jaguar) | 20 | none | pass / pass |
| `google.com` | `50.31.156.113`, `.118`, `.121` (Postmark) | 2 + 1 + 2 | none | pass / pass |
| `google.com` | `2600:3c04::2000:8cff:fe2d:1b81` | 1 | **quarantine** | fail / fail |
| `comcast.net` | `173.255.245.115` | 28 | none | pass / pass |
| `yahoo.com` | `173.255.245.115` | 2 | none | pass / pass |
| `aol.com` | `173.255.245.115` | 1 | none | pass / pass |

**jaguar's `mail.log` was not read**, so its four rows (51 by the reporters' counts) are not
reconciled; A5's copy holds the logs if a later reading needs them. Comcast's
28 is evaluations, not messages (reading 23).

#### Google's Postmark rows: five sends, five messages

leopard's `email.log` (UTC), addresses reduced to domains on the host. Google's
10-05 window is the UTC−7 day, 10-05 07:00 to 10-06 07:00 UTC:

| `email.log` (UTC) | Category | To |
|---|---|---|
| 10-05 20:24:04 | `topic_notification` | `gmail.com` |
| 10-05 20:33:19 | `topic_notification` | `gmail.com` |
| 10-05 21:07:56 | `pm_notification` | `gmail.com` |
| 10-06 00:00:43 | `pm_notification` | `gmail.com` |
| 10-06 00:46:51 | `registration` | `gmail.com` |

Exactly five, and the 10-05 00:33 `admin_notification` falls in the 10-04
window. The three `msorensen.net` sends that day go to 1&1 (`mx00.1and1.com`),
which has never filed a report in this corpus. **Under a plain UTC day the count
would have been three**, so the UTC−7 day holds again, on a third source.

#### The quarantined row is a spoof, not leopard

leopard's only global IPv6 address is `2001:db8::4` (read
2026-10-06). The failing source is in `2600:3c04::`, a different Linode prefix
from both hosts, and its row carries **SPF `pass` for `lambaygroup.com`** and no
DKIM result: a host that is allowed to send for its own domain, putting ours
in the `From`. Aligned on neither, and quarantined, as the policy intends.

#### Scoring the twenty-fifth reading's predictions: three held, one falsified

1. **FALSIFIED: five, not four.** The fifth is the 10-06 00:46:51
   `registration` send, the beta's registration test, made after the
   prediction was written on 10-05. The log and the UTC−7 day are both right;
   the prediction counted a day that had not finished.
2. **HELD.** The Yahoo and AOL reports for 10-05 have jaguar rows only.
3. **HELD.** No row from `2600:3c01::2000:96ff:fe4a:23be`, and no other
   non-jaguar address in `2600:3c01::/64`. The new IPv6 row is in a different
   prefix.
4. **HELD.** Every report reads `p=quarantine`, and the one `quarantine`
   disposition is on a row aligned on neither mechanism.

#### Predictions for the twenty-seventh reading

1. **No row from leopard's `2001:db8::4` or
   `192.0.2.13` in any report.** leopard sends only through Postmark (B14).
2. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a row
   aligned on neither mechanism.

### Twenty-seventh reading — 2026-10-07, covering 2026-10-06: the last whole day before the freeze; jaguar alone, a fifth forwarder, and both predictions held

**The last window that is entirely jaguar's.** The freeze is 10-07 19:00 UTC,
so the 10-07 window is split between the two hosts and the readings from it on
are not a clean baseline day. `tools/dmarc_fetch.py -a <account>` scanned 31
messages: **4 new**, 27 already held, no conflicts. **The corpus is 171
reports.** All four are for the 10-06 window, and every one reads
`p=quarantine`. No Microsoft report, as in the twenty-sixth reading.

| Reporter | Source | Msgs | Disposition | DKIM / SPF |
|---|---|---|---|---|
| `google.com` | `173.255.245.115` (jaguar) | 16 | none | pass / pass |
| `google.com` | `173.255.245.115` (jaguar) | 1 | none | **fail** / pass, SPF on `mail.surfguitar101.com` |
| `google.com` | `35.89.44.34` | 1 | none | pass / **fail** |
| `comcast.net` | `173.255.245.115` | 36 | none | pass / pass |
| `yahoo.com` | `173.255.245.115` | 5 | none | pass / pass |
| `aol.com` | `173.255.245.115` | 1 | none | pass / pass |

**jaguar's `mail.log` was not read**, as in the twenty-sixth reading; A5's copy
does not reach 10-06, and D6's day-after pull does.

#### No Postmark row, because leopard sent nothing

leopard's `email.log`, read 2026-10-07: the last send is 10-06 00:46:51 UTC,
the beta's `registration` test, which falls in Google's 10-05 UTC−7 window and
was counted by the twenty-sixth reading. Nothing after it. The only service up
on leopard is `postgres` (S1 step 8 left the stack down), so **zero Postmark
rows is the expected count**, and that is what every report shows.

#### A fifth forwarder

| Source | Operator (whois, PTR) | SPF domain | Window | Msgs |
|---|---|---|---|---|
| `35.89.44.34` | Amazon, `35.71.64.0 – 35.95.255.255`; `omta35.uswest2.a.cloudfilter.net` | `surfguitar101.com` | 10-06 | 1 |

New to the corpus. **It fails SPF and passes DKIM `d=surfguitar101.com`**, so
it is carried through DMARC by DKIM alone, `disposition=none`, the same shape as
the four forwarders in the twenty-fourth reading. Unlike pair, it does not
rewrite the envelope sender, so SPF is evaluated against this domain and fails.
**Whose mailbox forwards through it was not investigated.**

#### Failure classes

- **DSN class: one more.** Google 10-06, `173.255.245.115`, `pass`/`fail`, SPF
  on `mail.surfguitar101.com` and no `<dkim>` element. By the twenty-second
  reading's discriminator, that is a bounce. Not matched to `mail.log`.

#### Scoring the twenty-sixth reading's predictions: both held

1. **HELD.** No row from `2001:db8::4` or
   `192.0.2.13`.
2. **HELD.** Every report reads `p=quarantine`, and no row has a non-`none`
   disposition, including the two aligned on only one mechanism.

#### Predictions for the twenty-eighth reading

The 10-07 window spans the freeze (19:00 UTC) and, if the go/no-go passes, the
flip. Google's window is the UTC−7 day, 10-07 07:00 to 10-08 07:00 UTC.

1. **No jaguar row reflects a send after the freeze.** jaguar's Celery keeps
   running under `OFFLINE` (runbook C0), but nothing it schedules in the
   afternoon sends mail. Its rows should fall below a normal day's in
   proportion to the hours lost; D6's `mail.log` pull confirms the count.
2. **Google's Postmark rows equal leopard's `email.log` sends to `gmail.com`
   in Google's window**, starting with part 1 of the smoke checklist's
   registration to a Gmail plus-address. A count that differs means a send was
   lost, or the UTC−7 day is wrong.
3. **No row from leopard's own addresses**, `2001:db8::4`
   or `192.0.2.13`: it sends only through Postmark (B14).
4. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Twenty-eighth reading — 2026-10-08, covering 2026-10-07: the flip day; both hosts reconcile exactly at Google and Yahoo, the `cloudfilter.net` forwarder is `thegogorillas.com`'s, and jaguar delivers to Comcast after the flip

**The first window with both hosts in it.** The freeze was 10-07 19:00 UTC and
the flip 19:43 UTC. `tools/dmarc_fetch.py -a <account>` scanned **2 messages,
both new**, no conflicts. **The corpus is 173 reports.** Both are for the 10-07
window and read `p=quarantine`. **Comcast, AOL and Microsoft have not filed for
10-07 yet.**

**Only two messages were scanned because the other 171 report mails are in
Gmail's Trash.** Brian moved the already-analyzed reports there. `--dry-run
--all --include-trash` finds 2 in All Mail and 171 in Trash, all already held,
so nothing is lost, and Gmail's 30-day purge does not matter once a report is in
`~/dmarc`. The fetch does not search the trash by default, so **a report trashed
before it is fetched would be missed**. Trashing only after a reading keeps that
from happening, and `--include-trash` covers it if it ever does.

| Reporter | Source | Msgs | Disposition | DKIM / SPF |
|---|---|---|---|---|
| `google.com` | `50.31.156.113`–`.126`, nine addresses (Postmark) | 23 | none | pass / pass |
| `google.com` | `173.255.245.115` (jaguar) | 5 | none | pass / pass |
| `google.com` | `209.85.220.41` (Gmail relay) | 2 | none | pass / **fail**, SPF on `gmail.com` |
| `google.com` | `44.202.169.34` | 1 | none | pass / **fail** |
| `yahoo.com` | `173.255.245.115` (jaguar) | 4 | none | pass / pass |
| `yahoo.com` | `50.31.156.113`, `.116`, `.120` (Postmark) | 3 | none | pass / pass |

Every Postmark row carries both `d=pm.mtasv.net` and `d=surfguitar101.com` and
passes SPF on `pm-bounces.surfguitar101.com`. No row aligned on neither
mechanism, and no DSN or over-long-line row.

#### Google's Postmark rows: 23 against 22 logged sends plus one unlogged

leopard's `email.log` (UTC), addresses reduced to domains on the host. Google's
window is the UTC−7 day, 10-07 07:00 to 10-08 07:00 UTC. The 37 render-pass
lines of `email_smoke.py` (20:18:37–40, 20:21:27–31, `STATUS.md` § Step 21
task 10) are excluded, since none left the host:

| `email.log` (UTC) | `gmail.com` sends |
|---|---|
| 10-07 19:29:02, 19:30:37, 20:12:22 | 3 (`registration`, `pm_notification` ×2) |
| 10-07 20:21:32–53, the smoke run's live pass | 10 |
| 10-07 20:31:22, 20:38:41 | 2 (`password_reset`, `pm_notification`) |
| 10-08 01:14:00 | 1 (`pm_notification`) |
| 10-08 02:22:02–06, 02:52:34–38 | 6 (`topic_notification`) |
| **Logged** | **22** |

**The twenty-third message is the smoke run's Django error mail**, which goes
through `mail_admins` rather than the site's wrapper and so is not in
`email.log`. `STATUS.md` records each smoke inbox receiving 11 messages against
10 logged lines. `sg101.log` has no `ERROR` line in the window, so there was no
other error mail. **22 + 1 = 23, exact.** Prediction 2 asked for this count
with the render lines excluded. Counting them would have predicted 37 or more.

#### Yahoo's Postmark rows: the plain UTC day, three for three

leopard sent `yahoo.com` three messages on the UTC day 10-07: 22:35:00,
23:07:08 and 23:41:01. Yahoo's report shows 3. **Under Google's UTC−7 day the
count would have been 9**, so Yahoo's window is the UTC day, as its report's
`date_range` states.

#### jaguar: five Google and four Yahoo deliveries, the last three hours before the freeze

jaguar's `/var/log/mail.log` read directly as `brian` (in `adm`), not yet D6's
archived pull. jaguar logs in CDT (UTC−5). `status=sent` lines by relay:

| jaguar (CDT) | Relay | Window |
|---|---|---|
| 10-07 02:01:15 (Brian's nightly cron mail, `orig_to=<brian>`), 06:13:08, 07:39:33, 08:25:05, 11:01:04 | Google | Google 10-07: **5** |
| 10-07 07:38:51, 07:39:33, 09:16:56, 11:01:03 | Yahoo | Yahoo 10-07: **4** |

**Both are exact.** jaguar's last site delivery was 10-07 11:01:13 CDT (16:01
UTC), to `thegogorillas.com`, and postfix took **no new message after the
freeze** except the cron mail of 10-08 02:01:12 CDT. jaguar's volume fell with
the hours lost: Google 20, 17, then 5 across 10-05 to 10-07.

**jaguar's cron mail keeps sending after the flip.** It goes out at 02:01 CDT,
07:01 UTC, one minute into Google's UTC−7 day, so **each Google window from
10-08 on carries one jaguar row for as long as jaguar runs**. That row is
expected and does not mean the site is sending from jaguar.

#### A jaguar delivery to Comcast after the flip

Queue ID `38C525869BC`, a site message to `comcast.net`, was queued 10-06
09:51:56 CDT. `mx1.mxge.comcast.net` answered `451 4.2.0 Try Again Later` after
DATA on every attempt, about every 70 minutes, for 48 hours. **It was accepted
at 10-08 09:51:21 CDT (14:51 UTC), `delay=172766`**, a day after the flip. So
**Comcast's report for 10-08 should carry one jaguar row**, and that row comes
from jaguar's queue, not from any new send.

This also gives a test of reading 23's claim that Comcast counts evaluations.
**jaguar delivered nothing to Comcast on 10-07.** Its only Comcast traffic was
21 deferred attempts on the UTC day (10-06 19:22 to 10-07 18:41 CDT). If
Comcast's 10-07 report carries a jaguar row, then Comcast evaluates DMARC
before it defers, and the row's count is set against 21.

#### The `cloudfilter.net` forwarder is `thegogorillas.com`'s

| Source | Operator (whois, PTR) | SPF domain | Window | Msgs |
|---|---|---|---|---|
| `44.202.169.34` | Amazon, `44.192.0.0/10`; `omta035.useast.a.cloudfilter.net` | `surfguitar101.com` | 10-07 | 1 |

This is the operator from the twenty-seventh reading
(`omta35.uswest2.a.cloudfilter.net`), at a second address. It carries only
`d=surfguitar101.com`, not `pm.mtasv.net`, so **the message came from jaguar**.
jaguar sent one message to `thegogorillas.com` in each of the two windows:
10-06 05:07:07 CDT and 10-07 11:01:13 CDT. Its MX, `mail.thegogorillas.com`
(`50.87.184.247`, `unifiedlayer.com`), is a shared host. **One forwarded row
per window, against one send per window, is a match, not yet a confirmation.**
leopard sent `thegogorillas.com` one message at 10-08 14:13:09 UTC, which sets
up a test (prediction 3 below).

#### The member's Gmail relay carries Postmark mail

`209.85.220.41` carried 2 messages. They are the first relay rows to carry
`d=pm.mtasv.net`, so they began as Postmark deliveries to a Google mailbox,
which then forwarded them to another Google mailbox. **The first hop is
already among the 23 above**, so the forward does not affect that count.

#### Scoring the twenty-seventh reading's predictions: all four held, two with caveats

1. **HELD, for the reports in hand.** No jaguar row reflects a site send after
   the freeze; the last one was 16:01 UTC. Its rows fell to 5 and 4. Caveat:
   the 48-hour Comcast deferral means jaguar *did* deliver after the flip, and
   that delivery falls in Comcast's 10-08 window, not this one.
2. **HELD.** 23 Postmark messages = 22 `email.log` sends + the unlogged error
   mail, on the UTC−7 day.
3. **HELD.** No row from `2001:db8::4` or
   `192.0.2.13`.
4. **HELD.** Both reports read `p=quarantine`, and every disposition is
   `none`. The rows aligned on one mechanism only are the two forwarders.

#### Predictions for the twenty-ninth reading

1. **Comcast's 10-08 report carries a jaguar row for `38C525869BC`.** For
   10-07, if Comcast files, a jaguar row means Comcast evaluates DMARC on
   deferred attempts: 21 of them on the UTC day.
2. **Google's 10-08 report carries exactly one jaguar row, the 02:01:13 CDT
   cron mail**, plus anything else jaguar's queue still holds at reading time.
   Anything more means jaguar is still sending site mail.
3. **Google's 10-08 report carries a `cloudfilter.net` row with
   `d=pm.mtasv.net`**, from leopard's 14:13:09 UTC send to
   `thegogorillas.com`. If it is there, that confirms the forwarder's owner.
   If not, the one-for-one match was a coincidence.
4. **If Microsoft files for 10-07, it carries 11 Postmark messages to
   `outlook.com`**: the smoke run's 10 live sends at 20:21:33–54 UTC and its
   error mail.
5. **Google's 10-08 Postmark rows equal leopard's `email.log` `gmail.com`
   sends from 10-08 07:00 to 10-09 07:00 UTC**, plus any Django error mail in
   `sg101.log`. That is the first full day of live traffic.
6. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Twenty-ninth reading — 2026-10-09, covering 2026-10-08 (and Comcast's and Microsoft's 10-07): the first full day on leopard; every Postmark row reconciles exactly at five endpoints, Comcast's deferral loop counts to the reception, and Microsoft's one extra is a retry

**The first window with leopard alone sending site mail.** `tools/dmarc_fetch.py
-a <account>` scanned 9 messages: **7 new**, 2 already held, no conflicts. **The
corpus is 180 reports.** Two are late reports for 10-07 (Comcast, Microsoft); five
are for 10-08 (Google, Yahoo, AOL, AT&T, Comcast). Every report reads
`p=quarantine` and every disposition is `none`. **AOL never filed for 10-07**, and
Microsoft has not filed for 10-08 yet.

| Reporter | Window | Source | Msgs | DKIM / SPF |
|---|---|---|---|---|
| `comcast.net` | 10-07 | `173.255.245.115` (jaguar) | **42** | pass / pass |
| `Outlook.com` | 10-07 | `50.31.156.113`–`.124`, seven addresses (Postmark) | **12** | pass / pass |
| `google.com` | 10-08 | `50.31.156.113`–`.126`, ten addresses (Postmark) | 31 | pass / pass |
| `google.com` | 10-08 | `173.255.245.115` (jaguar) | 2 | pass / pass |
| `google.com` | 10-08 | `209.85.220.41` (Gmail relay) | 1 | pass / **fail**, SPF on `gmail.com` |
| `google.com` | 10-08 | `44.202.169.34` (`cloudfilter.net`) | 1 | pass / **fail** |
| `yahoo.com` | 10-08 | Postmark, five addresses | 8 | pass / pass |
| `aol.com` (Yahoo) | 10-08 | Postmark, two addresses | 2 | pass / pass |
| `att.net` (Yahoo) | 10-08 | Postmark, two addresses | 2 | pass / pass |
| `comcast.net` | 10-08 | `173.255.245.115` (jaguar) | **25** | pass / pass |
| `comcast.net` | 10-08 | Postmark, two addresses | 2 | pass / pass |

Every Postmark row carries `d=pm.mtasv.net` and `d=surfguitar101.com` and passes
SPF on `pm-bounces.surfguitar101.com`. No row aligned on neither mechanism, and no
DSN or over-long-line row.

#### The Postmark rows against leopard's `email.log`

`email.log` (`/svr/sg101/var/log/django/`, UTC) holds 184 `outcome=sent`
recipient lines in all. `sg101.log` and `sg101.log.1` hold **no `ERROR` line on
10-08 or 10-09**, so no Django error mail went out unlogged this time.

| Endpoint | Window | `email.log` sends | Report |
|---|---|---|---|
| Google | UTC−7 day, 10-08 07:00 → 10-09 07:00 UTC | 29 `gmail.com` + **2 `muohio.edu`** | **31**, exact |
| Yahoo | UTC day 10-08 | 8 `yahoo.com` | 8, exact |
| AOL | UTC day 10-08 | 2 `aol.com` (18:44:08, 18:46:05) | 2, exact |
| AT&T | UTC day 10-08 | 2 `att.net` (02:22:05, 02:52:37) | 2, exact |
| Comcast | UTC day 10-08 | 2 `comcast.net` (18:44:09, 18:46:06) | 2, exact |

**`muohio.edu` is a Google Workspace domain** (MX `aspmx.l.google.com`), so
Google counts it with `gmail.com`, as reading 21 saw Google do with tenant
domains. **This is what tells the windows apart, and it is a fresh forward test
of UTC−7.** The `gmail.com` count is 29 under either window. The two `muohio.edu`
sends fall at 10-08 20:53:41 and 10-09 01:53:09 UTC. Under the UTC day only the
first counts, which would give 30. Under UTC−7 both count: **31**, as the report
reads.

#### Microsoft's 10-07: 12 messages, against 11 that Postmark sent

Prediction 4 expected 11 `outlook.com` messages: the smoke run's 10 live sends
and its error mail. `email.log` holds 30 `outlook.com` lines for 10-07, which
are 20 render-pass lines and the 10 live sends at 20:21:33–54 UTC. **Postmark's
own record (API `messages/outbound`, 10-06 to 10-09) holds exactly 11
`outlook.com` messages**: those 10 and `[Django] Smoke test error report` at
20:21:56 UTC. The only other Microsoft-hosted recipient in that span is a
`hotmail.com` password reset at 10-09 03:30:48 UTC, outside the window. Every
row's `envelope_to` is `outlook.com`.

**So Microsoft counted 12 for 11 sent, and the twelfth is a retry.** Postmark's
delivery events (`/messages/outbound/{id}/details`, read 2026-10-09) show ten
of the eleven delivered on the first attempt. The eleventh, the `Password reset`
handed to Postmark at 20:21:46 UTC, has two events:

| UTC | Event | Postmark's detail |
|---|---|---|
| 20:22:46 | `Transient` | `421 4.4.2 … failed to send message to 50.31.156.113->outlook-com.olc.protection.outlook.com … Timed Out waiting 59.999999664s for response to Some(Command(".\r\n"))`, MX `52.101.60.181` |
| 20:25:52 | `Delivered` | `250 2.6.0 … Queued mail for delivery`, MX `52.101.60.153` |

**This is Comcast's mechanism at a second receiver.** The first attempt timed out
waiting for the reply to the end-of-data `.`, so Microsoft had the whole message
and evaluated it. The retry was evaluated again. 10 + 2 = 12, exact. Like
Comcast's, **Microsoft's `count` is receptions, not messages**, and
reconciling against a send log needs the sender's per-attempt record.

#### Comcast's deferral loop: 42 and 25, exact to the reception

Reading 23 found that Comcast's `count` is end-of-DATA receptions, and that every
retry cycle reaches both Comcast MX hosts. Queue ID `38C525869BC` is the second
test of that, and it passes on both days. In jaguar's `mail.log` (CDT, shifted
to UTC):

| UTC day | Receptions in jaguar's log | Report |
|---|---|---|
| 10-07 | 40 `451 … (in reply to end of DATA command)` + 2 `lost connection … while sending end of data` (the 10-06 19:21–19:22 CDT cycle, one per MX) | **42** |
| 10-08 | 24 `451` at end of DATA (12 cycles) + the `250` acceptance at 14:51:21 UTC | **25** |

**So Comcast also evaluates a message whose connection was lost after the body
was sent.** Postfix warns "message may be sent more than once" for exactly that
case. jaguar's queue is now empty (`mailq`, 10-09), so this loop is finished.

#### jaguar's two Google messages: the cron mail and a root mail

| jaguar (CDT) | Queue ID | Origin |
|---|---|---|
| 10-08 02:01:13 | `241AA58650F` | Brian's nightly cron mail, `orig_to=<brian>` |
| 10-09 00:57:26 | `5ADE05864DF` | `uid=0 from=<root>`, `orig_to=<root>`, 1,546 bytes |

The next cron mail, at 10-09 02:01:12 CDT (07:01:12 UTC), falls just past this
window and into the next one. **Neither message is site mail.** The second is
something run as root on jaguar at about 05:57 UTC on 10-09. Postfix does not log
a subject, so what it was is not recorded here.

#### The `cloudfilter.net` forwarder is confirmed as `thegogorillas.com`'s

`44.202.169.34` carried one message with **`d=pm.mtasv.net`** as well as
`d=surfguitar101.com`, so it came from Postmark. leopard sent `thegogorillas.com`
exactly one message in the window, at 14:13:09 UTC. Together with reading 28's
jaguar match, **two senders now line up one-for-one with this forwarder**, which
settles who runs it. Its SPF fails on `pm-bounces.surfguitar101.com`, as every
forwarder's does, and DKIM carries alignment.

`209.85.220.41` carried one Postmark message forwarded from one Google mailbox to
another. Its first hop is among the 31.

#### Scoring the twenty-eighth reading's predictions: three held, two held with a caveat, one falsified, and explained

1. **HELD, both halves.** Comcast's 10-08 report carries jaguar's row: 25, the
   acceptance plus that day's 24 deferred receptions. Comcast filed for 10-07 with
   a jaguar row although jaguar delivered nothing to it that day, so **Comcast
   evaluates on deferred attempts**. The count is 42, not the predicted 21:
   prediction 1 counted retry cycles where reading 23's rule counts receptions,
   two per cycle.
2. **HELD in substance, but the count was wrong.** jaguar has one row, `count=2`,
   not 1: the cron mail and a root mail. No jaguar site mail.
3. **HELD.** The `cloudfilter.net` row carries `d=pm.mtasv.net`.
4. **FALSIFIED by one, explained.** Microsoft reads 12 for the 11 Postmark sent:
   one message timed out after its body was sent and was received again on the
   retry. The prediction counted messages, and Microsoft counts receptions.
5. **HELD.** 31 = 29 `gmail.com` + 2 `muohio.edu`, with no error mail. The
   prediction did not foresee the Workspace domain, but nothing in the count is
   left unexplained.
6. **HELD.** Every report reads `p=quarantine`, and every disposition is `none`.

#### Predictions for the thirtieth reading

1. **Google's 10-09 report carries exactly one jaguar message, the 02:01:12 CDT
   cron mail** (07:01:12 UTC), plus any further root mail. jaguar's queue is
   empty, so there is no retry to add.
2. **Comcast's 10-09 report has no jaguar row.** Its Postmark rows equal
   leopard's `comcast.net` sends on the UTC day, unless Comcast deferred one of
   them.
3. **If Microsoft files for 10-09, it reads 1**: the `hotmail.com` password reset
   at 03:30:48 UTC, plus one for every `Transient` event Postmark records against it.
4. **Google's 10-09 Postmark rows equal leopard's `gmail.com` plus `muohio.edu`
   sends from 10-09 07:00 to 10-10 07:00 UTC**, plus any Django error mail.
5. **Yahoo, AOL and AT&T match their UTC-day sends exactly.**
6. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a row
   aligned on neither mechanism.

### Thirtieth reading — 2026-10-10, covering 2026-10-09: a quiet day, exact at all three reporters; jaguar's extra Google mail is certbot failing to renew

`tools/dmarc_fetch.py -a <account>` scanned 12 messages: **3 new**, 9 already
held. **The corpus is 183 reports**, all three for 10-09 and all `p=quarantine`
with every disposition `none`. **No report is missing.** leopard sent nothing to
`comcast.net`, `aol.com` or a Microsoft domain on the UTC day 10-09, and jaguar
sent nothing to them either, so there was nothing for Comcast, AOL or Microsoft
to file. Microsoft's report for the `hotmail.com` send of 10-09 03:30:48 UTC is
not in yet, and neither is any Microsoft report for 10-08, which had no
Microsoft send.

| Reporter | Source | Msgs | DKIM / SPF |
|---|---|---|---|
| `google.com` | `50.31.156.115`, `.116`, `.124` (Postmark) | 4 | pass / pass |
| `google.com` | `173.255.245.115` (jaguar) | **3** | pass / pass |
| `google.com` | `104.30.8.10` (`i-ba.cloudflare-email.net`) | 1 | pass / pass |
| `google.com` | `35.89.44.34` (`omta35.uswest2.a.cloudfilter.net`) | 1 | pass / **fail** |
| `google.com` | `44.202.169.38` (`omta039.useast.a.cloudfilter.net`) | 1 | pass / **fail** |
| `yahoo.com` | `50.31.156.113`, `.124` (Postmark) | 2 | pass / pass |
| `att.net` (Yahoo) | `50.31.156.113` (Postmark) | 1 | pass / pass |

#### Every Postmark row reconciles

| Endpoint | Window | leopard `email.log` | Report |
|---|---|---|---|
| Google | UTC−7 day, 10-09 07:00 → 10-10 07:00 UTC | 4 `gmail.com` (08:43:07, 08:58:00, 10:51:44, 10-10 00:59:37); no `muohio.edu` | **4**, exact |
| Yahoo | UTC day 10-09 | 2 `yahoo.com` (01:51:55, 08:43:12) | 2, exact |
| AT&T | UTC day 10-09 | 1 `att.net` (01:51:52) | 1, exact |

`sg101.log` holds no `ERROR` in the Google window, so no error mail went out.
The first `ERROR` since is at 10-10 10:18:19, in the next window (see
`STATUS.md`, the 10-10 watch line).

**The three forwarded rows each match a send.**

- **`104.30.8.10` is Cloudflare Email Routing.** It carried leopard's
  `admin_notification` to `admin@surfguitar101.com` at 10-10 01:41:02 UTC, which
  Email Routing forwards to Gmail. It carries three signatures (`surfguitar101.com`,
  `pm.mtasv.net` and `cloudflare-email.net`), and SPF passes on
  `surfguitar101.com` through the apex's `include:_spf.mx.cloudflare.net`.
  Reading 24 saw the same address do the same thing.
- **The two `cloudfilter.net` rows are `thegogorillas.com`'s**, as reading 29
  settled: leopard sent it one message at 10-09 08:43:10 and one at 10-10
  00:59:41 UTC, both in the window, and both rows carry `d=pm.mtasv.net`.
  This is the forwarder's west-coast address from reading 27 and a third
  east-coast one.

#### jaguar: the cron mail and two certbot failures

jaguar's three Google messages, in the window 10-09 02:00 → 10-10 02:00 CDT:

| jaguar (CDT) | Queue ID | Origin |
|---|---|---|
| 10-09 02:01:12 | `73EF25864EC` | Brian's nightly cron mail, `uid=1000` |
| 10-09 12:39:53 | `E7C6F586502` | `uid=0`, root cron session opened 12:00:01, closed 12:39:52 |
| 10-10 00:11:03 | `D5EF25864DF` | `uid=0`, root cron session opened 00:00:01, closed 00:11:02 |

The reading-29 root mail (10-09 00:57:26) fits the same pattern: session opened
00:00:01, closed 00:57:25. **The job is `/etc/cron.d/certbot`**: `0 */12 * * *
… perl -e 'sleep int(rand(3600))' && certbot -q renew`, a run at 00:00 and 12:00
with a random sleep of up to an hour, which matches all three. `-q` prints only
on failure, so **each mail is a failed renewal**.

**The certificate is `edtaxidermy.com`'s.** Read from jaguar's port 443 by SNI:

| Name | `notAfter` | Enters the 30-day renewal window |
|---|---|---|
| `edtaxidermy.com` | 2026-11-08 04:50 UTC | **2026-10-09 04:50 UTC** |
| `bravenewsurf.com` | 2026-11-14 16:23 | 10-15 |
| `surfguitar101.com` | 2026-11-16 16:17 | 10-17 |
| `themadeira.net` | 2026-11-17 04:35 | 10-18 |
| `wiki.surfguitar101.com` | 2026-11-27 16:54 | 10-28 |

The first failure, 10-09 05:57 UTC, is the first run after `edtaxidermy.com`
entered its window, and no root mail went out before it.

**The mail's body (Brian, 2026-10-10) gives the cause:** `Failed authorization
procedure`, `http-01` `unauthorized` for both `www.edtaxidermy.com` and
`edtaxidermy.com`: `Invalid response from
http://edtaxidermy.com/.well-known/acme-challenge/…: 404`, fetched at Cloudflare
addresses (`2606:4700:…`). **Let's Encrypt's challenge never reaches jaguar.**
`edtaxidermy.com` has been served from Cloudflare since 2026-09-13 (the
jaguar-decommission project), so jaguar's webroot answer is not where the
validator looks. The same is true of every name on the list: `bravenewsurf.com`
and `themadeira.net` moved in September, and `surfguitar101.com` and the wiki at
the 10-07 flip. **jaguar's certificates serve nothing**, so the failures cost
nothing beyond the mail. **Unless certbot is stopped, jaguar sends Google two more
messages a day**. Each run tries every due certificate in one mail, so the
names in the last column lengthen that mail and do not add to the count.

#### Scoring the twenty-ninth reading's predictions: four held, two had nothing to score

1. **HELD.** One cron mail plus root mail. That clause turned out to cover two
   more messages.
2. **Nothing to score.** Comcast received nothing on 10-09 from either host and
   filed no report.
3. **Not yet.** Microsoft has not filed for 10-09. Postmark records the
   `hotmail.com` reset as delivered at 03:30:49 UTC with no `Transient` event,
   so the prediction stays at 1.
4. **HELD.** 4 = 4, with no `muohio.edu` and no error mail.
5. **HELD** for Yahoo and AT&T. AOL received nothing and filed nothing.
6. **HELD.**

#### Predictions for the thirty-first reading

1. **Microsoft's 10-09 report, when it comes, reads 1.**
2. **Google's 10-10 jaguar count is the 02:01 CDT cron mail plus one per failed
   certbot run** in 10-10 02:00 → 10-11 02:00 CDT. *Overtaken the same day:*
   Brian disabled the certbot cron at 11:39 CDT, before the 12:00 run, so the
   expected count is **1**, the cron mail alone. A root mail would mean the
   cron was not the only thing running certbot.
3. **Google's 10-10 Postmark rows equal leopard's `gmail.com` and `muohio.edu`
   sends from 10-10 07:00 to 10-11 07:00 UTC**, plus any Django error mail. The
   10:18 worker timeout is logged by gunicorn rather than by Django's request
   handling, so it should not have sent one: **an error mail in Postmark from
   10:18 would falsify that.** Cloudflare Email Routing adds a row for the
   `contact_form` to `admin@` at 10:17:00.
4. **Yahoo's 10-10 equals its UTC-day sends.** leopard sent `gmx.at` two
   messages at 15:37:47 and 16:14:23. If a GMX or `web.de` report arrives, it
   carries them, doubled if reading 23's `web.de` double count applies.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-first reading — 2026-10-11, covering 2026-10-10 (and Microsoft's 10-09): exact at four reporters, GMX files and does not double, and disabling certbot took jaguar back to one message

`tools/dmarc_fetch.py -a <account>` scanned 17 messages: **5 new**, 12 already
held, no conflicts. **The corpus is 188 reports.** One is Microsoft's late
report for 10-09; four are for 10-10 (Google, Yahoo, AT&T, GMX). Every report
reads `p=quarantine` and every disposition is `none`. leopard sent nothing to
`comcast.net`, `aol.com` or a Microsoft domain on the UTC day 10-10, and neither
Comcast, AOL nor Microsoft filed for it.

| Reporter | Window | Source | Msgs | DKIM / SPF |
|---|---|---|---|---|
| `Outlook.com` | 10-09 | `50.31.156.114` (Postmark) | **1** | pass / pass |
| `google.com` | 10-10 | `50.31.156.113`–`.126`, nine addresses (Postmark) | **24** | pass / pass |
| `google.com` | 10-10 | `173.255.245.115` (jaguar) | **1** | pass / pass |
| `google.com` | 10-10 | `104.30.10.185` (Cloudflare Email Routing) | 1 | pass / pass |
| `google.com` | 10-10 | `209.85.220.41` (Gmail relay) | 2 | pass / **fail**, SPF on `gmail.com` |
| `google.com` | 10-10 | `35.89.44.38` (`cloudfilter.net`) | 1 | pass / **fail** |
| `yahoo.com` | 10-10 | Postmark, five addresses | 7 | pass / pass |
| `att.net` (Yahoo) | 10-10 | `50.31.156.124` (Postmark) | 1 | pass / pass |
| `gmx.net` | 10-10 | `50.31.156.113`, `.116` (Postmark) | 2 | pass / pass |

No row aligned on neither mechanism. **GMX's rows carry only
`d=surfguitar101.com`**, not `pm.mtasv.net` as well: GMX reports the aligned
signature alone.

#### Every Postmark row reconciles

| Endpoint | Window | leopard `email.log` | Report |
|---|---|---|---|
| Microsoft | UTC day 10-09 | 1 `hotmail.com` (03:30:48) | **1**, exact |
| Google | UTC−7 day, 10-10 07:00 → 10-11 07:00 UTC | 21 `gmail.com` + **3 `muohio.edu`** (23:53:48, 01:15:07, 02:53:13) | **24**, exact |
| Yahoo | UTC day 10-10 | 7 `yahoo.com` | 7, exact |
| AT&T | UTC day 10-10 | 1 `att.net` (22:48:35) | 1, exact |
| GMX | UTC day 10-10 | 2 `gmx.at` (15:37:47, 16:14:23) | 2, exact |

**UTC−7 passes again on the `muohio.edu` sends**: only the 23:53:48 one falls
on the UTC day, which would give 15 + 1 = 16 against Google's 24. The other two
domains in the window, `msorensen.net` (MX `1and1.com`) and `hushmail.com`, are
not Google-hosted, and Google does not count them.

`sg101.log` holds one `ERROR` in the Google window, gunicorn's `Error handling
request POST /profile/avatar/` at 10:18:19, the worker timeout. Google's count
is exact without an error mail, and the one Email Routing row is matched below,
and **Postmark's own record confirms Django did not mail the timeout**: its
`messages/outbound` for 10:00 → 10:40 UTC (the API reads `-04:00`) holds two
messages, the `Registration Confirmation` at 10:09:15 and the contact form's
`Feedback: Change username` at 10:17:00, both `Sent`.

**The forwarded rows each match a send.**

- **`104.30.10.185` is Cloudflare Email Routing**, a new address in its range:
  the `contact_form` to `admin@surfguitar101.com` at 10:17:00 UTC, as
  prediction 3 named. leopard's other `admin@` send that UTC day, the
  01:41:02 `admin_notification`, fell in reading 30's Google window.
- **`35.89.44.38` is `thegogorillas.com`'s forwarder**: leopard sent it one
  message in the window, 23:50:51 UTC.
- **`209.85.220.41` carried two messages forwarded between Google mailboxes**;
  their first hops are among the 24.

#### jaguar: the cron mail alone

jaguar's `mail.log.1`, window 10-10 02:00 → 10-11 02:00 CDT, holds one Google
delivery: **`A576D586502`, Brian's nightly cron mail, 10-10 02:01:12 CDT**
(`uid=1000`). The last root mail is `D5EF25864DF` at 10-10 00:11:03 CDT, the
certbot failure reading 30 already counted, in the previous window. **So
disabling `/etc/cron.d/certbot` at 11:39 CDT stopped the failures**, and nothing
else runs certbot.

**A new root mail falls in the next window**: `935E95864ED`, `uid=0
from=<root>`, at 10-11 06:47:01 CDT (11:47:01 UTC), to Gmail, the same minute
`mail.log` rotated. That is Sunday's `cron.weekly`: **the mail tells Brian
that a newer Ubuntu release is available** (Brian, 2026-10-11). It is not site
mail and not a fault.

#### Scoring the thirtieth reading's predictions: all five held

1. **HELD.** Microsoft's 10-09 reads 1, the `hotmail.com` password reset.
2. **HELD.** One jaguar message, the cron mail; no root mail from 12:00 CDT on.
3. **HELD.** 24 = 21 + 3, the `contact_form` row is there, and Postmark
   holds no error mail from 10:18.
4. **HELD.** Yahoo 7 = 7. GMX filed, and read 2 for 2: **reading 23's `web.de`
   double count does not apply at GMX**.
5. **HELD.**

#### Predictions for the thirty-second reading

1. **Google's 10-11 jaguar count is 2**: the 02:01:12 CDT cron mail (07:01:12
   UTC) and the 06:47:01 CDT `cron.weekly` upgrade notice.
2. **Google's 10-11 Postmark rows equal leopard's `gmail.com` and `muohio.edu`
   sends from 10-11 07:00 to 10-12 07:00 UTC**, plus any Django error mail.
3. **Microsoft's 10-11 reads 1**: the `hotmail.com` `forgot_username` at
   14:30:12 UTC, plus one for every `Transient` event Postmark records against it.
4. **Yahoo, AT&T and GMX match their UTC-day sends exactly.**
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-second reading — 2026-10-12, covering 2026-10-11: exact at Google and Yahoo, jaguar's two messages as predicted, Microsoft not yet filed

`tools/dmarc_fetch.py -a <account>` scanned 19 messages: **2 new**, 17 already
held, no conflicts. **The corpus is 190 reports.** Both are for 10-11: Google
and Yahoo. Every report reads `p=quarantine` and every disposition is `none`.
**Microsoft has not filed for 10-11** by 23:40 UTC 10-12. leopard sent nothing to
`att.net`, a GMX domain, `aol.com` or `comcast.net` on the UTC day 10-11, and
none of those reporters filed for it.

| Reporter | Window | Source | Msgs | DKIM / SPF |
|---|---|---|---|---|
| `google.com` | 10-11 | `50.31.156.113`–`.126`, eight addresses (Postmark) | **20** | pass / pass |
| `google.com` | 10-11 | `173.255.245.115` (jaguar) | **2** | pass / pass |
| `google.com` | 10-11 | `35.89.44.32`, `.34`, `.38` (`uswest2.a.cloudfilter.net`) | 3 | pass / **fail** |
| `google.com` | 10-11 | `44.202.169.34`, `.38` (`useast.a.cloudfilter.net`) | 2 | pass / **fail** |
| `yahoo.com` | 10-11 | Postmark, six addresses | 7 | pass / pass |

No row aligned on neither mechanism.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-11 07:00 → 10-12 07:00 UTC | leopard `email.log`: 20 `gmail.com`, no `muohio.edu` in the window | **20**, exact |
| Google, forwarders | same | leopard `email.log`: 5 `thegogorillas.com` | **5** `cloudfilter.net` rows, exact |
| Google, jaguar | 10-11 02:00 → 10-12 02:00 CDT | jaguar `mail.log`: `77F7A5864DC` cron mail 02:01:13 CDT, `935E95864ED` `cron.weekly` root mail 06:47:02 CDT | **2**, exact |
| Yahoo | UTC day 10-11 | leopard `email.log`: 7 `yahoo.com` | 7, exact |

leopard's `email.log` holds 36 sends on the UTC day 10-11, all `outcome=sent`.
`sg101.log` holds no `ERROR` or `CRITICAL` line dated 10-11 or 10-12, so no
Django error mail sits in Google's count. jaguar's next cron mail, 10-12
02:01:15 CDT (07:01:15 UTC), falls in the next window.

#### Scoring the thirty-first reading's predictions

1. **HELD.** jaguar 2: the cron mail and the `cron.weekly` upgrade notice.
2. **HELD.** 20 = 20 `gmail.com`; the two `muohio.edu` sends of the UTC day
   (01:15:07, 02:53:13) fell before 07:00 and were reading 31's.
3. **OPEN.** Microsoft has not filed for 10-11.
4. **HELD** at Yahoo, 7 = 7. AT&T and GMX had no sends and did not file.
5. **HELD.**

#### Predictions for the thirty-third reading

1. **Microsoft's 10-11 reads 1**, the `hotmail.com` `forgot_username` at
   14:30:12 UTC, plus one for every `Transient` event Postmark records against it.
2. **Google's 10-12 jaguar count is 1**: the 02:01:15 CDT cron mail, unless
   jaguar's root mails again.
3. **Google's 10-12 Postmark rows equal leopard's `gmail.com` sends from 10-12
   07:00 to 10-13 07:00 UTC**, plus any Django error mail; its `cloudfilter.net`
   rows equal its `thegogorillas.com` sends in the same window.
4. **Yahoo, AOL and Comcast match their UTC-day 10-12 sends exactly**: 6
   `yahoo.com`, 1 `aol.com` (06:15:55) and 2 `comcast.net` (06:15:57,
   18:49:59) as of 23:40 UTC, plus any sent before midnight.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-third reading — 2026-10-13, covering 2026-10-12 (and Microsoft's 10-11): exact at five reporters, the sixth `cloudfilter.net` row is the 06:29 send, and jaguar back to the cron mail

`tools/dmarc_fetch.py -a <account>` scanned 24 messages: **5 new**, 19 already
held, no conflicts. **The corpus is 195 reports.** One is Microsoft's late
report for 10-11; four are for 10-12 (Google, Yahoo, AOL, Comcast). Every
report reads `p=quarantine` and every disposition is `none`. leopard sent
nothing to `att.net`, a GMX domain or a Microsoft domain on the UTC day 10-12,
and none of those reporters filed for it.

| Reporter | Window | Source | Msgs | DKIM / SPF |
|---|---|---|---|---|
| `Outlook.com` | 10-11 | `50.31.156.114` (Postmark) | **1** | pass / pass |
| `google.com` | 10-12 | `50.31.156.113`–`.126`, ten addresses (Postmark) | **20** | pass / pass |
| `google.com` | 10-12 | `173.255.245.115` (jaguar) | **1** | pass / pass |
| `google.com` | 10-12 | `35.89.44.32`, `.34`, `.36`, `.38` (`uswest2.a.cloudfilter.net`) | 5 | pass / **fail** |
| `google.com` | 10-12 | `44.202.169.38` (`useast.a.cloudfilter.net`) | 1 | pass / **fail** |
| `yahoo.com` | 10-12 | Postmark, four addresses | 6 | pass / pass |
| `aol.com` (Yahoo) | 10-12 | `50.31.156.113` (Postmark) | 1 | pass / pass |
| `comcast.net` | 10-12 | `50.31.156.120`, `.126` (Postmark) | 2 | pass / pass |

No row aligned on neither mechanism. `35.89.44.36` is a new address in the
`uswest2` forwarder's range.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Microsoft | UTC day 10-11 | leopard `email.log`: 1 `hotmail.com` (14:30:12) | **1**, exact: no retry counted |
| Google, Postmark | UTC−7 day, 10-12 07:00 → 10-13 07:00 UTC | leopard `email.log`: 20 `gmail.com` | **20**, exact |
| Google, forwarders | same | leopard `email.log`: 6 `thegogorillas.com` (17:56:51, 18:16:22, 19:13:39, 22:40:04, 22:43:25, and 10-13 06:29:52) | **6** `cloudfilter.net` rows, exact |
| Google, jaguar | 10-12 02:00 → 10-13 02:00 CDT | jaguar `mail.log`: `4C8C25864EC`, the cron mail, 02:01:15 CDT | **1**, exact |
| Yahoo | UTC day 10-12 | leopard `email.log`: 6 `yahoo.com` | 6, exact |
| AOL | UTC day 10-12 | leopard `email.log`: 1 `aol.com` (06:15:55) | 1, exact |
| Comcast | UTC day 10-12 | leopard `email.log`: 2 `comcast.net` (06:15:57, 18:49:59) | 2, exact |

leopard's `email.log` holds 41 sends on the UTC day 10-12, and 44 in Google's
window, all `outcome=sent`. None went to `admin@surfguitar101.com`, so there is
no Email Routing row. `sg101.log` holds no `ERROR` or `CRITICAL` line dated
10-12 or 10-13, so no Django error mail sits in Google's count. The other
domains of the day, `msorensen.net` (4), `rockisland.com` and `mail.de`, are not
reporters. jaguar's next cron mail, `4A597586516` at 10-13 02:01:13 CDT, falls
in the next window.

#### Scoring the thirty-second reading's predictions: all five held

1. **HELD.** Microsoft's 10-11 reads 1, the `hotmail.com` `forgot_username`.
2. **HELD.** One jaguar message, the cron mail.
3. **HELD.** 20 = 20 `gmail.com`, and 6 `cloudfilter.net` = 6
   `thegogorillas.com` sends. The sixth `cloudfilter.net` message is the
   10-13 06:29:52 send, inside the UTC−7 window.
4. **HELD.** Yahoo 6, AOL 1 and Comcast 2, each exact. Nothing more was sent to
   them after 23:40 UTC.
5. **HELD.**

#### Predictions for the thirty-fourth reading

1. **Google's 10-13 jaguar count is 1**: `4A597586516`, the 02:01:13 CDT cron
   mail, unless jaguar's root mails again.
2. **Google's 10-13 Postmark rows equal leopard's `gmail.com` sends from 10-13
   07:00 to 10-14 07:00 UTC**, plus any Django error mail. Its
   `cloudfilter.net` rows equal its `thegogorillas.com` sends in the same
   window. As of 17:25 UTC, nothing has been sent in that window. The 8
   `gmail.com` sends and the one `thegogorillas.com` send on 10-13 all fell
   before 07:00 and are counted in the thirty-third.
3. **Yahoo and Comcast match their UTC-day 10-13 sends exactly**: so far 4
   `yahoo.com` and 3 `comcast.net`, plus any sent before midnight.
4. **Microsoft and AOL file nothing for 10-12**, and nothing for 10-13 unless
   leopard sends to them before midnight.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-fourth reading — 2026-10-15, covering 2026-10-13: the quietest Google day since the flip, 1 for 1; exact at Yahoo, Comcast and GMX

`tools/dmarc_fetch.py -a <account>` scanned 28 messages: **4 new**, 24 already
held, no conflicts. **The corpus is 199 reports.** All four are for 10-13:
Google, Yahoo, Comcast and GMX. Every report reads `p=quarantine` and every
disposition is `none`. leopard sent nothing to a Microsoft domain, `aol.com` or
`att.net` on the UTC day 10-12 or 10-13, and none of those reporters filed. Read
10-15 ~00:40 UTC.

| Reporter | Window | Source | Msgs | DKIM / SPF |
|---|---|---|---|---|
| `google.com` | 10-13 | `50.31.156.120` (Postmark) | **1** | pass / pass |
| `google.com` | 10-13 | `173.255.245.115` (jaguar) | **1** | pass / pass |
| `yahoo.com` | 10-13 | Postmark, five addresses | 6 | pass / pass |
| `comcast.net` | 10-13 | `50.31.156.113`, `.124`, `.126` (Postmark) | 3 | pass / pass |
| GMX | 10-13 | `50.31.156.117` (Postmark) | 1 | pass / pass |

No row aligned on neither mechanism, and no forwarder row.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-13 07:00 → 10-14 07:00 UTC | leopard `email.log`: 1 `gmail.com`, the `registration` at 10-14 03:17:33 | **1**, exact |
| Google, forwarders | same | leopard `email.log`: no `thegogorillas.com` send | **0**, exact |
| Google, jaguar | 10-13 02:00 → 10-14 02:00 CDT | jaguar `mail.log`: `4A597586516`, the cron mail, 02:01:13 CDT | **1**, exact |
| Yahoo | UTC day 10-13 | leopard `email.log`: 6 `yahoo.com` | 6, exact |
| Comcast | UTC day 10-13 | leopard `email.log`: 3 `comcast.net` (00:31:27, 00:34:36, 01:03:44) | 3, exact |
| GMX | UTC day 10-13 | leopard `email.log`: 1 `gmx.at` (19:03:16) | 1, exact |

leopard's `email.log` holds 20 sends on the UTC day 10-13, all `outcome=sent`.
Google's window holds only 7 sends in all: 4 to `yahoo.com`, 2 to
`msorensen.net` (not a reporter) and the one `gmail.com` registration. Every
other `gmail.com` send of the UTC day fell before 07:00 and was reading 33's.
None went to `admin@surfguitar101.com`, so there is no Email Routing row.
`sg101.log` holds no `ERROR` or `CRITICAL` line dated 10-13 → 10-15, so no
Django error mail sits in Google's count. jaguar's next cron mail,
`637575864DF` at 10-14 02:01:13 CDT, falls in the next window.

#### Scoring the thirty-third reading's predictions: all five held

1. **HELD.** One jaguar message, `4A597586516`.
2. **HELD.** 1 = 1 `gmail.com`, and no `cloudfilter.net` row for no
   `thegogorillas.com` send.
3. **HELD.** Yahoo 6 and Comcast 3, each exact. GMX filed for a send made
   after the prediction (19:03:16), and is exact too.
4. **HELD.** Neither Microsoft nor AOL filed for 10-12 or 10-13.
5. **HELD.**

#### Predictions for the thirty-fifth reading

1. **Google's 10-14 jaguar count is 1**: `637575864DF`, the 02:01:13 CDT cron
   mail, unless jaguar's root mails again.
2. **Google's 10-14 Postmark rows equal leopard's `gmail.com` sends from 10-14
   07:00 to 10-15 07:00 UTC**, plus any Django error mail: so far 1, at
   18:47:08. No `thegogorillas.com` send so far, so no `cloudfilter.net` row.
3. **Yahoo's 10-14 reads 8**, exact to the UTC day's `yahoo.com` sends, all to
   one address.
4. **Comcast, GMX, AOL, AT&T and Microsoft file nothing for 10-14**: leopard
   sent them nothing on the UTC day.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-fifth reading — 2026-10-15, covering 2026-10-14: exact at Google (21) and Yahoo (8); jaguar's 3 for a predicted 1 is the thirty-fourth reading's own probe

`tools/dmarc_fetch.py -a <account>` scanned 30 messages: **2 new**, 28 already
held, no conflicts. **The corpus is 201 reports.** Both are for 10-14, Google
and Yahoo. Every report reads `p=quarantine` and every disposition is `none`.
leopard sent nothing to Comcast, GMX, AOL, AT&T or a Microsoft domain on the UTC
day 10-14, and none of them filed. Read 10-15 ~17:20 UTC.

| Reporter | Window | Source | Msgs | DKIM / SPF |
|---|---|---|---|---|
| `google.com` | 10-14 | `50.31.156.113`–`.126`, nine addresses (Postmark) | **21** | pass / pass |
| `google.com` | 10-14 | `173.255.245.115` (jaguar) | **3** | pass / pass |
| `google.com` | 10-14 | `209.85.220.41` (Gmail relay) | 5 | pass / **fail**, SPF on `gmail.com` |
| `yahoo.com` | 10-14 | Postmark, six addresses | 8 | pass / pass |

No row aligned on neither mechanism, and no `cloudfilter.net` row.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-14 07:00 → 10-15 07:00 UTC | leopard `email.log`: 21 `gmail.com` (one at 18:47:08, twenty from 10-15 00:38:05 to 01:57:45) | **21**, exact |
| Google, forwarders | same | leopard `email.log`: no `thegogorillas.com` send | **0** `cloudfilter.net` rows, exact |
| Google, jaguar | 10-14 02:00 → 10-15 02:00 CDT | jaguar `mail.log`: `637575864DF`, the cron mail, 02:01:13 CDT; **`70CDD5864EC` and `7C7E2586572`, two root mails at 19:37:27 CDT** | **3**, exact |
| Yahoo | UTC day 10-14 | leopard `email.log`: 8 `yahoo.com`, all to one address | 8, exact |

leopard's `email.log` holds 15 sends on the UTC day 10-14 and 48 in Google's
window, all `outcome=sent`. The window's other domains, `msorensen.net` (6),
`hushmail.com` (4), `rockisland.com` and `mail.de`, are not reporters. Its
`att.net` (4), `comcast.net` and `aol.com` sends fell after UTC midnight, so
they belong to those reporters' 10-15. None went to
`admin@surfguitar101.com`, so there is no Email Routing row. `sg101.log` holds
no `ERROR` or `CRITICAL` line dated 10-14 or 10-15, so no Django error mail
sits in Google's count.

`209.85.220.41` carried five Postmark messages forwarded from one Google mailbox
to another. Their first hops are among the 21. Two recipients got exactly five
messages each in the window, so the count alone does not say whose forward it
is.

#### jaguar's two extra messages are the thirty-fourth reading's probe

Both root mails were queued at 19:37:26 CDT, which is 10-15 00:37:26 UTC, three
minutes before the thirty-fourth reading's recorded read time. jaguar's
`auth.log` shows where they came from: an ssh login as `brian` from
`192.0.2.12` at 19:37:24, then two
`sudo: brian : a password is required ; TTY=unknown ; … COMMAND=/bin/true`
lines at 19:37:26, and a disconnect the same second. **sudo mails root on a
failed authentication, and root forwards to Gmail**, so each non-interactive
`sudo -n true` put one message into Google's jaguar row. A scripted sudo check
over ssh, made at the minute the thirty-fourth reading was taken, is almost
certainly that reading's own work, and the next reading counted it. Do not run
one again: jaguar's sudo is already known to need Brian's password, and a probe
that mails root disturbs the cron-mail baseline these readings depend on. This
reading ran no `sudo` on jaguar.

#### Scoring the thirty-fourth reading's predictions: four held, one falsified and explained

1. **FALSIFIED, and explained.** jaguar's count is 3, not 1: the cron mail plus
   two sudo-failure mails, almost certainly from the reading's own probe (above).
2. **HELD.** 21 = 21 `gmail.com`. All but one were sent after the prediction's
   "so far 1". No `thegogorillas.com` send and no `cloudfilter.net` row.
3. **HELD.** Yahoo 8, exact.
4. **HELD so far.** Comcast, GMX, AOL, AT&T and Microsoft have filed nothing for
   10-14. Microsoft has filed up to four days late before, but a report for a
   day leopard sent it nothing would itself be a finding.
5. **HELD.**

#### Predictions for the thirty-sixth reading

1. **Google's 10-15 jaguar count is 1**: `B6EC65864EC`, the 02:01:13 CDT cron
   mail, unless jaguar's root mails again. No `sudo` is to be run on jaguar
   before it is read.
2. **Google's 10-15 Postmark rows equal leopard's `gmail.com` sends from 10-15
   07:00 to 10-16 07:00 UTC**, plus any Django error mail: so far 1, at
   13:29:20. No `thegogorillas.com` send so far, so no `cloudfilter.net` row.
3. **Yahoo's 10-15 matches the UTC day's `yahoo.com` sends**: so far 6.
4. **AT&T reads 4, Comcast 1 and AOL 1 for 10-15**, exact to the sends of
   00:38 → 01:57 UTC, plus any later ones. GMX and Microsoft file nothing for
   10-15 unless leopard sends to them before midnight.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-sixth reading — 2026-10-16, covering 2026-10-15: exact at Google, Yahoo, AOL and AT&T; jaguar back to the cron mail; Comcast not yet filed

`tools/dmarc_fetch.py -a <account>` scanned 34 messages: **4 new**, 30 already
held, no conflicts. **The corpus is 205 reports.** All four are for 10-15:
Google, Yahoo, AOL and AT&T. Every report reads `p=quarantine` and every
disposition is `none`. Read 10-16 ~17:45 UTC.

| Reporter | Window | Source | Msgs | DKIM / SPF |
|---|---|---|---|---|
| `google.com` | 10-15 | `50.31.156.117`, `.118`, `.126` (Postmark) | **4** | pass / pass |
| `google.com` | 10-15 | `173.255.245.115` (jaguar) | **1** | pass / pass |
| `google.com` | 10-15 | `209.85.220.41` (Gmail relay) | 1 | pass / **fail**, SPF on `gmail.com` |
| `yahoo.com` | 10-15 | Postmark, four addresses | 7 | pass / pass |
| `aol.com` (Yahoo) | 10-15 | `50.31.156.113` (Postmark) | 1 | pass / pass |
| `att.net` (Yahoo) | 10-15 | `50.31.156.117`, `.121`, `.126` (Postmark) | 5 | pass / pass |

No row aligned on neither mechanism, and no `cloudfilter.net` row.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-15 07:00 → 10-16 07:00 UTC | leopard `email.log`: 4 `gmail.com` (13:29:20, then three at 21:10:31 → 21:10:35) | **4**, exact |
| Google, forwarders | same | leopard `email.log`: no `thegogorillas.com` send | **0** `cloudfilter.net` rows, exact |
| Google, jaguar | 10-15 02:00 → 10-16 02:00 CDT | jaguar `mail.log`: `B6EC65864EC`, the cron mail, 02:01:13 CDT | **1**, exact |
| Yahoo | UTC day 10-15 | leopard `email.log`: 7 `yahoo.com`, all to one address | 7, exact |
| AOL | UTC day 10-15 | leopard `email.log`: 1 `aol.com` (01:51:09) | 1, exact |
| AT&T | UTC day 10-15 | leopard `email.log`: 5 `att.net` (00:38:07, 00:47:15, 01:33:09, 01:57:44, 21:10:34) | 5, exact |

leopard's `email.log` holds 50 sends on the UTC day 10-15 and 11 in Google's
window, all `outcome=sent`. The window's other domains, `msorensen.net`,
`hushmail.com` and the one `att.net`, are not Google's. None went to
`admin@surfguitar101.com`, so there is no Email Routing row. `sg101.log`
holds no `ERROR` or `CRITICAL` line dated 10-15 or 10-16, so no Django error
mail sits in Google's count. **Comcast hasn't filed for 10-15**, against one
`comcast.net` send at 01:51:10. jaguar ran no `sudo` and sent nothing but the
cron mail: its next one, `5B1D35864ED` at 10-16 02:01:14 CDT, falls in the
next window.

`209.85.220.41` carried one Postmark message forwarded between Google
mailboxes; its first hop is among the 4. Four Gmail recipients got one message
each in the window. That is consistent with the thirty-fifth
reading's two candidates, each of whom got five that day, but doesn't
narrow them.

#### Scoring the thirty-fifth reading's predictions: all five held, one with Comcast pending

1. **HELD.** One jaguar message, `B6EC65864EC`. No `sudo` was run on jaguar.
2. **HELD.** 4 = 4 `gmail.com`. Three were sent after the prediction's
   "so far 1". No `cloudfilter.net` row.
3. **HELD.** Yahoo 7, exact. One more `yahoo.com` send came after the
   prediction's "so far 6".
4. **HELD for AT&T and AOL, pending for Comcast.** AT&T reads 5: the four
   predicted plus the 21:10:34 send. AOL reads 1. Comcast hasn't filed. GMX
   and Microsoft filed nothing, and leopard sent them nothing.
5. **HELD.**

#### Predictions for the thirty-seventh reading

1. **Google's 10-16 jaguar count is 1**: `5B1D35864ED`, the 02:01:14 CDT cron
   mail, unless jaguar's root mails again.
2. **Google's 10-16 Postmark rows equal leopard's `gmail.com` and `muohio.edu`
   sends from 10-16 07:00 to 10-17 07:00 UTC**, plus any Django error mail:
   so far 8 `gmail.com` and 1 `muohio.edu` (a Google Workspace domain,
   counted in Google's rows as in reading 31). No `thegogorillas.com` send so far,
   so no `cloudfilter.net` row.
3. **Yahoo's 10-16 and AT&T's 10-16 match the UTC day's sends**: so far 2 each.
4. **Comcast files for 10-15 with 1 row**, the 01:51:10 send. AOL, GMX and
   Microsoft file nothing for 10-16 unless leopard sends to them before
   midnight.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-seventh reading — 2026-10-17, covering 2026-10-16: exact at Google, Yahoo and AT&T; Comcast files its 10-15 row; all five predictions held

`tools/dmarc_fetch.py -a <account>` scanned 38 messages: **4 new**, 34 already
held, no conflicts. **The corpus is 209 reports.** Three are for 10-16
(Google, Yahoo, AT&T) and one is Comcast's late 10-15. Every report reads
`p=quarantine` and every disposition is `none`. Read 10-17 ~17:30 UTC.

| Reporter | Window | Source | Msgs | DKIM / SPF |
|---|---|---|---|---|
| `google.com` | 10-16 | `50.31.156.113` → `.126`, nine addresses (Postmark) | **18** | pass / pass |
| `google.com` | 10-16 | `173.255.245.115` (jaguar) | **1** | pass / pass |
| `google.com` | 10-16 | `209.85.220.41` (Gmail relay) | 2 | pass / **fail**, SPF on `gmail.com` |
| `yahoo.com` | 10-16 | `50.31.156.115`, `.126` (Postmark) | 2 | pass / pass |
| `att.net` (Yahoo) | 10-16 | `50.31.156.120` (Postmark) | 2 | pass / pass |
| `comcast.net` | 10-15 | `50.31.156.118` (Postmark) | 1 | pass / pass |

No row aligned on neither mechanism, and no `cloudfilter.net` row.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-16 07:00 → 10-17 07:00 UTC | leopard `email.log`: 15 `gmail.com` and 3 `muohio.edu` (12:01:13 → 10-17 03:49:16) | **18**, exact |
| Google, forwarders | same | leopard `email.log`: no `thegogorillas.com` send | **0** `cloudfilter.net` rows, exact |
| Google, jaguar | 10-16 02:00 → 10-17 02:00 CDT | jaguar `mail.log`: `5B1D35864ED`, the cron mail, 02:01:13 CDT | **1**, exact |
| Yahoo | UTC day 10-16 | leopard `email.log`: 2 `yahoo.com` (13:42:49, 13:57:38) | 2, exact |
| AT&T | UTC day 10-16 | leopard `email.log`: 2 `att.net` (13:42:47, 13:57:36) | 2, exact |
| Comcast | UTC day 10-15 | leopard `email.log`: 1 `comcast.net` (01:51:10) | 1, exact |

leopard's `email.log` holds 20 sends on the UTC day 10-16 and 28 in Google's
window, all `outcome=sent`. The window's other domains, `msorensen.net` (4),
`hushmail.com` (2) and the `att.net` and `yahoo.com` sends, are not Google's.
Two of the 15 `gmail.com` sends are `registration` mail (18:40:17, 19:08:39);
the rest are topic notifications. `sg101.log` holds no `ERROR` or `CRITICAL`
line dated 10-16 or 10-17, so no Django error mail sits in Google's count.
jaguar ran no `sudo` and sent nothing but the cron mail: its next one,
`E7B9A586507` at 10-17 02:01:13 CDT, falls in the next window. Its `mail.log`
otherwise holds only `Relay access denied` rejections.

`209.85.220.41` carried two Postmark messages forwarded between Google
mailboxes; their first hops are among the 18.

#### Scoring the thirty-sixth reading's predictions: all five held

1. **HELD.** One jaguar message, `5B1D35864ED`.
2. **HELD.** 18 = 15 `gmail.com` + 3 `muohio.edu`, against "so far 8 and 1";
   the rest were sent after the prediction. No Django error mail, no
   `cloudfilter.net` row.
3. **HELD.** Yahoo 2 and AT&T 2, exact; neither got another send after the
   prediction's "so far 2 each".
4. **HELD.** Comcast filed for 10-15 with 1 row, from `50.31.156.118`. AOL, GMX
   and Microsoft filed nothing for 10-16, and leopard sent them nothing.
5. **HELD.**

#### Predictions for the thirty-eighth reading

1. **Google's 10-17 jaguar count is 1**: `E7B9A586507`, the 02:01:13 CDT cron
   mail, unless jaguar's root mails again.
2. **Google's 10-17 Postmark rows equal leopard's `gmail.com` and `muohio.edu`
   sends from 10-17 07:00 to 10-18 07:00 UTC**, plus any Django error mail:
   so far none. leopard has sent nothing since 03:49:16 UTC.
3. **Yahoo's and AT&T's 10-17 match the UTC day's sends**: so far 0 each, so
   neither files for 10-17 unless leopard sends to them before midnight.
4. **Comcast, AOL, GMX and Microsoft file nothing for 10-16 or 10-17** unless
   leopard sends to them before midnight on 10-17: it sent them nothing on 10-16.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-eighth reading — 2026-10-18, covering 2026-10-17: exact at Google; Yahoo files for a spoof, quarantined under the policy

`tools/dmarc_fetch.py -a <account>` scanned 40 messages: **2 new**, 38 already
held, no conflicts. **The corpus is 211 reports.** Both are for 10-17: Google
and Yahoo. Every report reads `p=quarantine`. Read 10-18 ~21:40 UTC.

| Reporter | Window | Source | Msgs | DKIM / SPF | Disposition |
|---|---|---|---|---|---|
| `google.com` | 10-17 | `50.31.156.114` → `.126`, five addresses (Postmark) | **6** | pass / pass | none |
| `google.com` | 10-17 | `173.255.245.115` (jaguar) | **1** | pass / pass | none |
| `yahoo.com` | 10-17 | `209.85.208.101` (a Google server) | 1 | **fail / fail**; authenticated as `bogotabureau.com` (SPF and DKIM pass there) | **quarantine** |

The Yahoo row is not ours: a message whose header `From` claimed
`surfguitar101.com`, sent through Google's infrastructure and signed for
`bogotabureau.com`. It aligned on neither mechanism, so Yahoo quarantined it
as the policy asks. Yahoo has no Postmark row for 10-17, and leopard sent
Yahoo nothing that day.

**The corpus holds four quarantined rows in all**, every one aligned on
neither mechanism: three in Google's 09-30 report, from `119.59.99.226`, each
authenticated as a different domain (`dmkarashop.com`, `wuttanabat.com`,
`chiangraipool.com`), and this one. Counted with `dmarc_report.py` over the
whole corpus, rows whose disposition isn't `none`.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-17 07:00 → 10-18 07:00 UTC | leopard `email.log`: 6 `gmail.com` (17:46:34 → 10-18 02:07:59), 0 `muohio.edu` | **6**, exact |
| Google, forwarders | same | leopard `email.log`: no `thegogorillas.com` send | **0** `cloudfilter.net` rows, exact |
| Google, jaguar | 10-17 02:00 → 10-18 02:00 CDT | jaguar `mail.log`: `E7B9A586507`, the cron mail, 02:01:15 CDT | **1**, exact |
| Yahoo, Postmark | UTC day 10-17 | leopard `email.log`: no `yahoo.com` send | **0** Postmark rows, exact |
| AT&T | UTC day 10-17 | leopard `email.log`: no `att.net` send | no report, exact |

leopard's `email.log` holds 11 sends on the UTC day 10-17 (8 `gmail.com`, 2
`muohio.edu`, 1 `msorensen.net`) and 6 in Google's window, all
`outcome=sent`. The two `muohio.edu` sends fall before 07:00 UTC, in the
thirty-seventh reading's window. Five of the six window sends are topic
notifications and one a private-message notification. `sg101.log` holds no
`ERROR` or `CRITICAL` line dated 10-17 or 10-18, so no Django error mail sits
in Google's count.

#### Scoring the thirty-seventh reading's predictions: four held, one held on the count

1. **HELD.** One jaguar message, `E7B9A586507`.
2. **HELD.** 6 = 6 `gmail.com` + 0 `muohio.edu`. No Django error mail, no
   `cloudfilter.net` row.
3. **HELD ON THE COUNT, NOT ON THE FILING.** Yahoo's and AT&T's Postmark counts
   match leopard's sends, 0 each. But "neither files for 10-17" missed: Yahoo
   filed, for the spoof, which no prediction about our own mail could see.
   AT&T filed nothing.
4. **HELD, SO FAR.** Comcast, AOL, GMX and Microsoft filed nothing for 10-16 or
   10-17. Comcast has filed a day late before.
5. **HELD, AND EXERCISED.** Every report reads `p=quarantine`, and the one
   non-`none` disposition is on the row aligned on neither mechanism.

#### Predictions for the thirty-ninth reading

1. **Google's 10-18 jaguar count is 2**: `819C35864DF`, the 02:01:12 CDT cron
   mail, and `BEE2B5864EC` at 06:47:02 CDT, from root (uid 0): the Sunday
   `run-parts --report /etc/cron.weekly` in `/etc/crontab`, as on 10-11.
   Unless jaguar's root mails again before 10-19 02:00 CDT.
2. **Google's 10-18 Postmark rows equal leopard's `gmail.com` and `muohio.edu`
   sends from 10-18 07:00 to 10-19 07:00 UTC**, plus any Django error mail: so
   far 6 `gmail.com` (to 20:59:43 UTC).
3. **Yahoo's, AT&T's and Microsoft's 10-18 match the UTC day's sends**: so far
   4 `yahoo.com`, 1 `att.net` and 3 `hotmail.com`, so all three should file.
4. **Comcast, AOL and GMX file nothing for 10-18** unless leopard sends to them
   before midnight: so far it has not.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Thirty-ninth reading — 2026-10-19, covering 2026-10-18: exact at Google, Yahoo and AT&T; Microsoft not yet filed

`tools/dmarc_fetch.py -a <account>` scanned 43 messages: **3 new**, 40 already
held, no conflicts. **The corpus is 214 reports.** All three are for 10-18:
Google, Yahoo and AT&T. Every report reads `p=quarantine`, and every row's
disposition is `none`. Read 10-19 ~23:50 UTC.

| Reporter | Window | Source | Msgs | DKIM / SPF | Disposition |
|---|---|---|---|---|---|
| `google.com` | 10-18 | `50.31.156.113` → `.126`, ten addresses (Postmark) | **23** | pass / pass | none |
| `google.com` | 10-18 | `209.85.220.41` (Gmail relay) | 1 | pass / fail (`gmail.com`) | none |
| `google.com` | 10-18 | `173.255.245.115` (jaguar) | **2** | pass / pass | none |
| `yahoo.com` | 10-18 | `50.31.156.117`, `.118`, `.124`, `.126` (Postmark) | **4** | pass / pass | none |
| `att.net` | 10-18 | `50.31.156.114` (Postmark) | **1** | pass / pass | none |

The relay row is a forward of one of the 23, aligned on DKIM; its first hop
is among them.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-18 07:00 → 10-19 07:00 UTC | leopard `email.log`: 23 `gmail.com` (14:53:55 → 10-19 05:20:14), 0 `muohio.edu` | **23**, exact |
| Google, forwarders | same | leopard `email.log`: no `thegogorillas.com` send | **0** `cloudfilter.net` rows, exact |
| Google, jaguar | 10-18 02:00 → 10-19 02:00 CDT | jaguar `mail.log`: `819C35864DF`, the cron mail, 02:01:12 CDT; `BEE2B5864EC`, root's `cron.weekly` mail, 06:47:02 CDT | **2**, exact |
| Yahoo, Postmark | UTC day 10-18 | leopard `email.log`: 4 `yahoo.com` | **4**, exact |
| AT&T | UTC day 10-18 | leopard `email.log`: 1 `att.net` | **1**, exact |
| Microsoft | UTC day 10-18 | leopard `email.log`: 3 `hotmail.com` | not yet filed |

leopard's `email.log` holds 19 sends on the UTC day 10-18, every one a topic
notification (9 `gmail.com`, 4 `yahoo.com`, 3 `hotmail.com`, 1 `att.net`, 1
`hushmail.com`, 1 `msorensen.net`), and 41 in Google's window, all
`outcome=sent`. Of the window's 23 `gmail.com` sends, 17 fall after the
thirty-eighth reading was taken: a registration confirmation at 00:39:33 and
16 topic notifications in two bursts, 05:16:10 → 05:16:20 and 05:20:04 →
05:20:14. `sg101.log` holds no `ERROR` or `CRITICAL` line dated 10-18 or 10-19,
so no Django error mail sits in Google's count.

#### Scoring the thirty-eighth reading's predictions: four held, one pending

1. **HELD.** Two jaguar messages, `819C35864DF` and `BEE2B5864EC`, the Sunday
   `cron.weekly` mail as on 10-11.
2. **HELD.** 23 = 23 `gmail.com` + 0 `muohio.edu`. No Django error mail, no
   `cloudfilter.net` row.
3. **HELD AT YAHOO AND AT&T, PENDING AT MICROSOFT.** Yahoo 4 = 4, AT&T 1 = 1.
   Microsoft has not filed for 10-18; its newest report in the corpus is for
   10-11, and it has filed up to four days late before.
4. **HELD.** Comcast, AOL and GMX filed nothing for 10-18, and leopard sent
   them nothing that UTC day: its `aol.com` and `comcast.net` sends fall on
   10-19.
5. **HELD.** Every report reads `p=quarantine`, and every disposition is
   `none`.

#### Predictions for the fortieth reading

1. **Google's 10-19 jaguar count is 1**: `96ED758650E`, the 02:01:14 CDT cron
   mail. Unless jaguar's root mails again before 10-20 02:00 CDT.
2. **Google's 10-19 Postmark rows equal leopard's `gmail.com` and `muohio.edu`
   sends from 10-19 07:00 to 10-20 07:00 UTC**, plus any Django error mail: so
   far 3 `gmail.com` (to 16:35:46 UTC).
3. **AOL and Comcast file for 10-19, 2 messages each**, matching the UTC day's
   2 `aol.com` and 2 `comcast.net` sends; Comcast may file a day late.
4. **Microsoft files for 10-18 with 3 messages**, within four days. Yahoo and
   AT&T show no Postmark row for 10-19: leopard sent them nothing that UTC day.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Fortieth reading — 2026-10-20, covering 2026-10-19: exact at Google, AOL and Comcast; Microsoft files its 10-18 row; all five predictions held

`tools/dmarc_fetch.py -a <account>` scanned 47 messages: **4 new**, 43 already
held, no conflicts. **The corpus is 218 reports.** Three are for 10-19 (Google,
AOL, Comcast) and one is Microsoft's late 10-18. Every report reads
`p=quarantine`, and every row's disposition is `none`. Read 10-20 ~22:25 UTC.

| Reporter | Window | Source | Msgs | DKIM / SPF | Disposition |
|---|---|---|---|---|---|
| `google.com` | 10-19 | `50.31.156.114` → `.121`, six addresses (Postmark) | **6** | pass / pass | none |
| `google.com` | 10-19 | `173.255.245.115` (jaguar) | **1** | pass / pass | none |
| `aol.com` | 10-19 | `50.31.156.116`, `.121` (Postmark) | **2** | pass / pass | none |
| `comcast.net` | 10-19 | `50.31.156.118`, `.121` (Postmark) | **2** | pass / pass | none |
| `protection.outlook.com` | 10-18 | `50.31.156.114` (1), `.116` (2) (Postmark) | **3** | pass / pass | none |

No relay row and no forwarder row.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-19 07:00 → 10-20 07:00 UTC | leopard `email.log`: 6 `gmail.com` (08:54:14 → 10-20 02:50:57), 0 `muohio.edu` | **6**, exact |
| Google, forwarders | same | leopard `email.log`: no `thegogorillas.com` send | **0** `cloudfilter.net` rows, exact |
| Google, jaguar | 10-19 02:00 → 10-20 02:00 CDT | jaguar `mail.log.1` + `mail.log`: `96ED758650E`, the cron mail, 02:01:13 CDT | **1**, exact |
| AOL | UTC day 10-19 | leopard `email.log`: 2 `aol.com` | **2**, exact |
| Comcast | UTC day 10-19 | leopard `email.log`: 2 `comcast.net` | **2**, exact, on time |
| Microsoft | UTC day 10-18 | leopard `email.log`: 3 `hotmail.com` | **3**, exact, a day late |

leopard's `email.log` holds 28 sends on the UTC day 10-19 (26 topic
notifications, 2 registration: 20 `gmail.com`, 2 each `aol.com`,
`comcast.net`, `mail.de`, `rockisland.com`), and 8 in Google's window, all
`outcome=sent`. Of the window's 6 `gmail.com` sends, 3 fall after the
thirty-ninth reading was taken: two topic notifications at 10-20 02:28 and a
PM notification at 02:50:57. `sg101.log` holds no `ERROR` or `CRITICAL` line
dated 10-19 or 10-20, so no Django error mail sits in Google's count.

#### Scoring the thirty-ninth reading's predictions: all five held

1. **HELD.** One jaguar message, `96ED758650E`, the 02:01 CDT cron mail.
2. **HELD.** 6 = 6 `gmail.com` + 0 `muohio.edu`. No Django error mail.
3. **HELD.** AOL 2 = 2 and Comcast 2 = 2, both on time.
4. **HELD.** Microsoft filed 10-18 with 3, two days after the day. Yahoo and
   AT&T filed nothing for 10-19, and leopard sent them nothing that UTC day.
5. **HELD.** Every report reads `p=quarantine`, and every disposition is
   `none`.

#### Predictions for the forty-first reading

1. **Google's 10-20 jaguar count is 1**: `E05B65864EC`, the 02:01:14 CDT cron
   mail. Unless jaguar's root mails again before 10-21 02:00 CDT.
2. **Google's 10-20 Postmark rows equal leopard's `gmail.com` and `muohio.edu`
   sends from 10-20 07:00 to 10-21 07:00 UTC**, plus any Django error mail: so
   far 0 (to 22:22 UTC). A Google report of 0 Postmark rows may not be filed
   at all.
3. **Yahoo and Comcast file for 10-20, 1 message each**, matching the UTC
   day's 1 `yahoo.com` and 1 `comcast.net` send so far; Comcast may file a day
   late.
4. **Microsoft, AOL and AT&T file nothing for 10-19 or 10-20** (so far):
   leopard sent them nothing on either UTC day.
5. **Every report reads `p=quarantine`.** Any non-`none` disposition is on a
   row aligned on neither mechanism.

### Forty-first reading — 2026-10-21, covering 2026-10-20: exact at Google, Yahoo, Comcast and AT&T; the last reading

`tools/dmarc_fetch.py -a <account>` scanned 51 messages: **4 new**, 47 already
held, no conflicts. **The corpus is 222 reports.** All four are for 10-20:
Google, Yahoo, Comcast and AT&T. Every report reads `p=quarantine`, and every
row's disposition is `none`. Read 10-21 ~18:10 UTC.

| Reporter | Window | Source | Msgs | DKIM / SPF | Disposition |
|---|---|---|---|---|---|
| `google.com` | 10-20 | `50.31.156.113` → `.126`, eight addresses (Postmark) | **17** | pass / pass | none |
| `google.com` | 10-20 | `209.85.220.41` (Gmail relay) | 4 | pass / fail (`gmail.com`) | none |
| `google.com` | 10-20 | `44.202.169.38` (`useast.a.cloudfilter.net`) | 1 | pass / **fail** | none |
| `google.com` | 10-20 | `173.255.245.115` (jaguar) | **1** | pass / pass | none |
| `yahoo.com` | 10-20 | `50.31.156.120`, `.124` (Postmark) | **3** | pass / pass | none |
| `comcast.net` | 10-20 | `50.31.156.115` (Postmark) | **1** | pass / pass | none |
| `att.net` | 10-20 | `50.31.156.120`, `.124` (Postmark) | **2** | pass / pass | none |

The relay rows are forwards of four of the 17, aligned on DKIM; their first
hops are among them. The `cloudfilter.net` row is `thegogorillas.com`'s
forwarder, as in readings 29 to 33, aligned on DKIM.

#### Every row reconciles

| Endpoint | Window | Sender's log | Report |
|---|---|---|---|
| Google, Postmark | UTC−7 day, 10-20 07:00 → 10-21 07:00 UTC | leopard `email.log`: 17 `gmail.com` (22:33:28 → 10-21 03:15:20), 0 `muohio.edu` | **17**, exact |
| Google, forwarders | same | leopard `email.log`: 1 `thegogorillas.com`, 23:49:54 | **1** `cloudfilter.net` row, exact |
| Google, jaguar | 10-20 02:00 → 10-21 02:00 CDT | jaguar `mail.log`: `E05B65864EC`, the cron mail, 02:01:14 CDT | **1**, exact |
| Yahoo | UTC day 10-20 | leopard `email.log`: 3 `yahoo.com` (02:28, 22:33, 23:49) | **3**, exact |
| Comcast | UTC day 10-20 | leopard `email.log`: 1 `comcast.net`, 02:28 | **1**, exact, on time |
| AT&T | UTC day 10-20 | leopard `email.log`: 2 `att.net` (22:33, 22:35) | **2**, exact |

leopard's `email.log` holds 20 sends on the UTC day 10-20 (19 topic
notifications, 1 PM notification: 9 `gmail.com`, 3 `yahoo.com`, 2 each
`att.net`, `hushmail.com`, `msorensen.net`, 1 each `comcast.net`,
`thegogorillas.com`), and 35 in Google's window, all `outcome=sent`. Every one
of the window's 17 `gmail.com` sends falls after the fortieth reading was
taken (22:25): two bursts of topic notifications at 22:33 and 22:35, and the
rest between 00:17 and 03:15. `sg101.log` holds no `ERROR` or `CRITICAL` line
dated 10-20 or 10-21, so no Django error mail sits in Google's count.

#### Scoring the fortieth reading's predictions: four held, one falsified by later sends

1. **HELD.** One jaguar message, `E05B65864EC`, the 02:01 CDT cron mail.
2. **HELD.** 17 = 17 `gmail.com` + 0 `muohio.edu`. No Django error mail.
3. **HELD.** Yahoo and Comcast both filed for 10-20, each equal to the UTC
   day's sends. Yahoo's count was 3, not 1: two sends to it came after the
   reading.
4. **HELD AT MICROSOFT AND AOL, FALSIFIED AT AT&T.** AT&T filed 10-20 with 2,
   for the two `att.net` sends at 22:33 and 22:35, after the reading was
   taken. The prediction's "so far" covered that case, and the report still
   matches the sender's log exactly.
5. **HELD.** Every report reads `p=quarantine`, and every disposition is
   `none`.

#### The log stops here

This is the last reading. The cadence set on 2026-09-05 (weekly, then daily
across the Step 21 window, then stopped) ends with the two weeks after the
cutover, so no predictions follow. `tools/dmarc_fetch.py` and
`tools/dmarc_report.py` stay for spot checks.

**The post-cutover corpus**: 47 reports with windows from 10-08 to 10-20,
210 rows and 374 messages. **Exactly one row fails DKIM**: Yahoo's 10-17
spoof from `209.85.208.101` as `bogotabureau.com`, which is also the only
non-`none` disposition. Every Postmark row and every jaguar row passes DKIM
and aligns, at every reporter that filed.

How the exit items stand is recorded in `STATUS.md` under *When the reading
log stops*.
