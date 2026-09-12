# Task: Database and Media Backups to Object Storage

## Description
Build the new VM's backup path — scheduled database and media backups to
S3-compatible object storage, with retention, an alarm that is verified to
deliver, and a restore that has actually been run. **The storage provider is
deliberately not chosen here**; the constraint it must satisfy is.

## Background
The site's backups today are a nightly rsync from `bobcat.gremmielabs.dev` to the
production host, and **that job backs up jaguar**. At cutover it keeps backing up a
machine nobody uses while the new VM has no backup at all, and the failure mode is
silence: the backup appears to be running, because it is — of the wrong host.
Repointing that job belongs to the cutover; **defining what the new VM produces
belongs here.**

**The alarm lesson is the expensive part of the background.** bobcat mails its
output to Brian, and measured on 2026-08-18 that channel carried **54 bounce log
lines against 4 deliveries** — roughly one refused message a night, which is the
job's cadence. A backup that started failing would announce it through a channel
that already fails most of the time. Any alarm this task adds has to be verified as
delivering, not assumed.

**`tools/pg_snapshot.sh` already exists** and is the starting point rather than a
thing to duplicate. It dumps in custom format (`-Fc`), excludes the search index's
data deliberately — 1,104 MB of a 1,681 MB database, and derived — and its measured
timings are recorded in `STATUS.md`: dump 8 s / 128 MB, full restore about a minute
with identical row counts, `reindex_search` 1 m 35 s.

**Two traps that tool already documents and this task must not re-learn:**
`./snapshots` is mounted read-only into the `postgres` container, so dumps stream
out over `exec -T`; and `.env` must not be sourced to read values out of it,
because `SECRET_KEY` contains `$8` and sourcing runs the file as shell.

**And the limitation worth keeping in front of the schedule:** a snapshot only
helps if it is older than the damage.

### Why the provider is deferred, and what is decided instead

**`plan.md` says only *"Backups still go to object storage."*** No provider is
chosen anywhere in the record; the design mentions Linode Object Storage in a
costing example and nothing more.

**Nothing in this task needs the answer.** The dump, the schedule, the retention
shape, the alarm, the media backup and the restore drill are all provider-neutral.
AWS S3 and Linode Object Storage both speak the S3 API, so the difference is an
endpoint URL and a credential — configuration, in the pattern
`sg101/settings/base.py:350-352` already uses for the user-photos bucket and its
endpoint.

**What must be decided now is the constraint, because it is what gets lost
otherwise.** If it is not written down, the bucket is chosen at provisioning time
on price and convenience, and the property that makes off-machine backups worth
having disappears without anyone noticing:

> **The backup target must not share a provider or account with the VM.**

A Linode VM backed up to Linode Object Storage shares a failure domain: one billing
lapse, suspension or account event takes the site and its backups together. This
composes with what already exists — `bobcat` is a second Linode and the plan
repoints its rsync at the new VM, giving a warm same-provider copy — so the object
storage copy is the one that has to be somewhere else. **Against a Linode VM, an
AWS S3 bucket satisfies the constraint, and the credentials and `boto3` are already
in the project from Step 15.**

**A separate bucket, not the media buckets.** `sg101.user.photos` and
`sg101.forum.photos` have their own access patterns and lifecycle; backups sharing
one are a media-cleanup script away from being gone.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C10 — backups to object storage)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — *PostgreSQL
  snapshots — `tools/pg_snapshot.sh`*, for the measured timings and the two traps
- `.agents/planning/2026-07-04-modernizing-sg101/research/hosting.md` — object
  storage options and pricing
- `tools/image_smoke.py` — the mock-by-default / opt-in-`--s3` pattern Step 15
  established for exercising real object storage

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Schedule a database dump to S3-compatible object storage, building on
   `tools/pg_snapshot.sh` rather than duplicating it.
2. Back up `/media` — the categories that live on the VM's disk — on a schedule
   appropriate to how often they change.
3. **Take the endpoint, bucket and credentials entirely from configuration**, in
   the pattern `base.py` already uses, so the provider is a `.env` value and not a
   code change.
4. **Build and exercise the whole path locally** against an S3-compatible endpoint
   in the dev stack, so the restore drill can run without a cloud account. Follow
   Step 15's precedent if an opt-in real-bucket branch is wanted as well.
5. **Record the non-shared-failure-domain constraint** where Step 21's
   provisioning will read it, and add the bucket-and-provider decision to
   `cutover-runbook.md`.
6. Use a **write-scoped credential** for the backup job — able to put objects, not
   to delete them — so a compromise of the VM cannot take the backups with it.
7. Implement retention **at the storage layer** (lifecycle rules) rather than as a
   deletion script that can silently stop running. Deletion is then the one thing
   the job's own credential cannot do.
8. Add failure alarming, and **verify the alarm is delivered** rather than assuming
   it. Use a channel that does not depend on this host's outbound mail.
9. Document the restore procedure where the cutover runbook can reference it.
10. Keep the search index excluded from dump data, and keep the reason recorded.

## Dependencies
- Task 03 — the production stack the backups run against, and where a local
  S3-compatible service would sit
- `tools/pg_snapshot.sh`, present since 2026-08-05
- A bucket, credentials and provider — **deferred to Step 21 provisioning**, which
  is why requirement 4 exists

## Implementation Approach
1. Read `tools/pg_snapshot.sh` and decide what it already does versus what needs
   adding — scheduling, upload, retention, alarming.
2. Stand up a local S3-compatible endpoint so the path is exercisable before any
   bucket exists.
3. Add the upload and lifecycle-based retention, keeping the custom-format dump so
   `pg_restore` can still pull individual tables.
4. Add the alarm, and test it by making the job fail on purpose.
5. **Run a restore into a scratch database and compare row counts**, which is the
   only evidence the backup is usable.

## Acceptance Criteria

1. **A scheduled dump reaches object storage**
   - Given the schedule is active against the local endpoint
   - When a cycle completes
   - Then a custom-format dump of the expected size is present in the bucket

2. **Media is backed up**
   - Given `/media` on the VM's disk
   - When a backup cycle completes
   - Then its contents are recoverable from object storage

3. **The restore has been run, not just written down**
   - Given a dump pulled from object storage
   - When it is restored into a scratch database
   - Then every table's row count matches the source

4. **The provider is configuration, not code**
   - Given the backup job
   - When the endpoint and bucket are changed in `.env`
   - Then the job targets the new destination with no code change

5. **The job cannot delete what it wrote**
   - Given the backup job's credential
   - When a delete is attempted against an existing object
   - Then it is refused, and lifecycle expiry still removes aged objects

6. **Retention removes old backups**
   - Given objects older than the retention window
   - When the lifecycle policy evaluates
   - Then they are removed and newer ones are untouched

7. **A failure is announced through a channel that works**
   - Given a backup job made to fail deliberately
   - When the cycle completes
   - Then an alarm is received, and its delivery is confirmed at the receiving end

8. **The constraint survives into provisioning**
   - Given `cutover-runbook.md`
   - When the backup bucket entry is read
   - Then it states that the target must not share a provider or account with the
     VM, and why

9. **The procedure is documented**
   - Given the restore documentation
   - When it is followed by someone who did not write it
   - Then the database is restored without recourse to the source

## Metadata
- **Complexity**: Medium
- **Labels**: Backups, PostgreSQL, Object Storage, Operations, Production Hardening
- **Required Skills**: pg_dump/pg_restore, S3-compatible APIs, scheduling, alerting
