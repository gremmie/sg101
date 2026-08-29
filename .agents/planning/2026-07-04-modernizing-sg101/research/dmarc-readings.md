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

**Reading 13 carries two addenda** — Gmail Postmaster Tools read the same
afternoon, whose compliance panel is a 2026-08-18 snapshot with two of its three
complaints measurably false and no deliverability data at this domain's volume;
and a census of the Gmail spam folder, which holds one filtered message that is
not a report, the one that was filtered having been removed from the folder by
the act of reading it.

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
