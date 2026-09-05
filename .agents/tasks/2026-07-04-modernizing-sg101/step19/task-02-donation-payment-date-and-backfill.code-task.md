# Task: Convert PayPal's Payment Date Zone, and Backfill Fifteen Years of Donations

## Description
`donations/views.py` throws away the timezone PayPal sends with every IPN and
records a Pacific wall clock as though it were the site's own zone. Every
donation on file is stored **two hours earlier than the instant PayPal
reported**. Fix the parse so new donations are correct, and backfill the
existing rows in the same change.

Both halves or neither. Correcting new rows alone would leave the column holding
two conventions two hours apart with nothing recording which row is which, and
`monthly_stats()` summing across both.

## Background

### The defect
PayPal sends `payment_date` as a Pacific wall clock with the zone as a trailing
abbreviation: `'04:14:08 Jan 21, 2011 PST'`. The handler does

```python
payment_date = payment_date[:-4]          # "strip off the timezone"
payment_date = datetime.datetime.strptime(payment_date, PP_DATE_FMT)
...
payment_date = timezone.make_aware(payment_date)
```

**The abbreviation is not converted, it is discarded.** `make_aware()` then
attaches `TIME_ZONE` — America/Chicago — to a clock reading that was Pacific.
Pacific is always two hours behind Chicago, so the error is a constant and DST
does not complicate it.

Note that `[:-4]` also silently assumes a three-letter abbreviation.

### How much data, measured 2026-08-09 against the production snapshot
**1,421 donations, 2011-03-01 to 2026-07-06, all affected.** Correcting them by
+2 hours moves **5 rows into a different calendar month** and **none into a
different year**. So the defect is invisible in annual totals and shows up only
as five donations reported in the wrong month across fifteen years of
`monthly_stats()` and `donations_report`.

### The decision, already taken
Phase 0 decided this on 2026-09-03: **fix forward and backfill**, Phase C
builds. The record is in `STATUS.md` under *Step 19 Phase 0 — the six
decisions*, item 5.

**"Fix forward only" was rejected on the record rather than by omission**, for
the reason above. "Do nothing and document it" was a legitimate option and was
also rejected: the amounts and dates are right and only the times are wrong, but
the code keeps recording every *new* donation two hours early, so the error
grows rather than sitting still.

### Why it is a migration and not a script
Step 21 loads a fresh production snapshot onto the new host, converted by
`tools/pgloader/convert.sh` and brought up to date by
`tools/pgloader/post_convert.py`. A one-off script run against today's database
would be undone by that reload. A migration runs as part of the chain, on
whatever snapshot is loaded.

### Constraints carried out of the Phase 0 decision
- **Map `PST`/`PDT` to `America/Los_Angeles` and raise on anything else.** Zone
  abbreviations are not uniquely decodable in general; PayPal only ever sends
  these two here, so mapping exactly those and rejecting the rest is safe and
  fails loudly rather than silently mis-filing.
- **The backfill keys on `payment_date < <cutover>` and must be idempotent.**
  Nothing in the row distinguishes a corrected donation from an uncorrected one,
  so the migration has to be all-or-nothing over a stated boundary and must not
  double-apply.

### Where the boundary actually is
The cutover constant is the moment the corrected parse goes live. Rows written
before it are Pacific-mislabelled; rows after it are correct. Because the
migration and the parse fix ship together, that boundary is *the migration's own
application time* — which is not knowable when the file is written. Settle this
explicitly; the obvious candidates are a hardcoded UTC timestamp chosen at
release, or a marker written by the migration itself. Do not leave it implicit.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — the
  `[Phase 0 DECIDED ... Phase C builds]` block on `payment_date`
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — *Step 19 Phase 0 —
  the six decisions*, item 5, for the argument that was actually made
- `donations/views.py:205-241` — the IPN handler
- `donations/models.py` — `DonationManager.monthly_stats()` and the
  `ExtractYear`/`ExtractMonth` work Step 13 task 09 did on the same column

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Parse the zone instead of discarding it.** Split the abbreviation off
   without assuming its length, map `PST` and `PDT` to `America/Los_Angeles`,
   build an aware datetime in that zone, and store it.

2. **Reject any other abbreviation loudly.** An unknown zone must log and refuse
   the IPN in the same way the handler already refuses an unparseable date — it
   must not fall back to a guess.

3. **Do not silently change what `make_aware()` meant.** The existing comment at
   `views.py:221` explains that `make_aware()` reproduces what the ORM did
   implicitly before. That reasoning is superseded here, and the comment must be
   replaced rather than left contradicting the code.

4. **One data migration in `donations/` backfilling `payment_date` by +2 hours**
   for every row before the stated boundary.

5. **Idempotent, and provably so.** Running it twice must not shift a row four
   hours.

6. **State the boundary.** A named constant with a comment saying what it means
   and why that value, not an inline literal.

7. **Reversible.** Unlike the email blanking, this one is exactly reversible —
   subtract two hours over the same boundary. Implement the reverse.

8. **Verify against the numbers already measured.** After the backfill, 1,421
   rows have moved, exactly 5 have changed calendar month, and 0 have changed
   year. Those figures were measured on the 2026-08-09 snapshot and a fresh
   snapshot will hold more donations — so the test is the *shape* (all rows
   before the boundary moved by exactly two hours), and the 5-and-0 figures are
   a check against the snapshot they were measured on.

## Dependencies
- `zoneinfo` (stdlib on 3.12) for `America/Los_Angeles`
- `donations/tests.py` — already contains real IPN payloads with `PST` dates,
  which are the natural fixtures
- `tools/pgloader/convert.sh` and `post_convert.py` for snapshot verification

## Implementation Approach

1. Fix the parse first, with tests over the existing IPN fixtures, including a
   `PDT` payload and a bogus-zone payload that must be refused.
2. Add the data migration with the boundary constant and its reverse.
3. Test the migration on constructed rows either side of the boundary.
4. Rehearse on a freshly converted snapshot: convert a pristine dump, run
   `post_convert.py`, and check the row count moved, the five month-crossers, and
   that `monthly_stats()` for those five months changes by exactly the expected
   amount.
5. Confirm `monthly_stats()` and `donations_report` read the corrected column the
   way Step 13 task 09 intended — this is the reporting path the defect was
   invisible in.

## Acceptance Criteria

1. **A PST donation is stored at the instant PayPal reported**
   - Given an IPN with `payment_date=04:14:08 Jan 21, 2011 PST`
   - When the handler processes it
   - Then the stored value equals `2011-01-21 04:14:08` in `America/Los_Angeles`,
     which is `12:14:08Z`

2. **A PDT donation is handled by the same path**
   - Given an IPN with a `PDT` date in summer
   - When the handler processes it
   - Then the stored instant reflects Pacific daylight time, not standard time

3. **An unknown abbreviation is refused, not guessed**
   - Given an IPN whose `payment_date` ends in an abbreviation that is neither
     `PST` nor `PDT`
   - When the handler processes it
   - Then the IPN is rejected and logged, and no `Donation` row is created

4. **The abbreviation's length is not assumed**
   - Given a `payment_date` whose zone token is not three characters
   - When it is parsed
   - Then the parse either succeeds correctly or is refused — it does not
     truncate the seconds

5. **The backfill moves every pre-boundary row by exactly two hours**
   - Given rows on both sides of the boundary
   - When the migration runs
   - Then every row before it has advanced by exactly two hours and no row after
     it has changed

6. **Idempotent**
   - Given the migration has run
   - When it runs again
   - Then no row moves a second time

7. **Reversible**
   - Given the migration has run
   - When it is reversed
   - Then every affected row returns to its original value exactly

8. **The measured figures reproduce on the snapshot they were measured on**
   - Given the 2026-08-09 production snapshot, converted
   - When the migration runs
   - Then 1,421 rows move, 5 change calendar month, and 0 change year

9. **The reports read the corrected data**
   - Given the five donations that change month
   - When `monthly_stats()` is called for the months either side
   - Then each donation is counted in the month it actually belongs to

10. **The suite is green and the tests are mutation-verified**
    - Given the full test suite under the deprecation gate on `docker_test`
    - When it is run in the container
    - Then it passes, and each new assertion has been observed to fail against a
      deliberate mutation — in particular, restoring the `[:-4]` discard must
      break a test

## Metadata
- **Complexity**: Medium
- **Labels**: donations, PayPal IPN, timezone, data migration, backfill, Step 19 Phase C
- **Required Skills**: Django migrations, zoneinfo, datetime correctness, PayPal IPN format
