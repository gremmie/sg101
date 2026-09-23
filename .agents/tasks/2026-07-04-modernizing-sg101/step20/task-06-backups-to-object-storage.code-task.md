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

**⚠️ PREMISE GAP found 2026-09-21: the first of those two traps describes the
*dev* stack, and this task runs against the *prod* one.** This file was generated
2026-09-12; task 03 landed the production stack on 2026-09-19. Measured from both
compose files rather than assumed:

| | `docker-compose.yml` (dev) | `docker-compose.prod.yml` |
|---|---|---|
| `./snapshots:/snapshots:ro` | **mounted** | **absent** |
| published `5432` | yes | **none** |
| data | `postgres_data` volume | `postgres_data` volume |

So in production there is **no snapshots mount to stream into and no published
port to connect to** — the dump has nowhere to land by the route the trap
describes, and the backup job's path onto the host is undefined rather than
inherited. The `.env` trap is unaffected and still applies.

**This does not change the task's shape**, only a premise its implementation
approach rests on: step 1 says to read `tools/pg_snapshot.sh` and decide what it
already does, and what it does is dev-shaped. Decide where a prod dump is written
before building on it.

**Also stale: the pointer in *Why the provider is deferred* read
`sg101/settings/base.py:350-352`, which is now the avatar settings.** Corrected
below to 377-387. **The pattern it cites is real and survives** — `USER_PHOTOS_BUCKET`,
`USER_PHOTOS_BASE_URL` and `USER_PHOTOS_REGION` are all `env()`-driven, so
requirement 3 stands as written.

**Same failure as tasks 04 and 07**: a task file written before the task it
depends on. **Re-read a task file's premises against what has landed since it was
written**, not only its requirement list.

**And the limitation worth keeping in front of the schedule:** a snapshot only
helps if it is older than the damage.

### Decided 2026-09-22: what runs the job, and where a dump may exist

**The schedule lives on the host, not in celery beat.** A systemd timer (or cron)
on the VM runs a one-shot compose service — `docker compose -f
docker-compose.prod.yml run --rm backup`, behind a profile so `up` never starts
it. The tooling stays in the repo and runs locally against the S3-compatible
endpoint; only the trigger is host configuration, alongside task 11's
`logrotate` in the cutover runbook. Beat was rejected on four grounds:

- **The app image cannot do it.** The Dockerfile installs `libpq-dev` but no
  PostgreSQL client, so there is no `pg_dump`, and one would have to match the
  16 server. `./media` is mounted into `web` only, not `worker` or `beat`.
- **It would share fate with what it protects.** A beat task needs beat, the
  broker and a worker all healthy; lose any one and backups stop with nothing
  said — the same silent failure this task exists to end.
- **It would occupy the only worker** for the length of a dump and a media
  upload, delaying the site's own tasks, mail among them.
- **The backup credential would sit in the application's environment**, reachable
  from every request, where it has no business being even write-scoped.

**The dump is written inside the backup container, verified, then uploaded — it
never lands on the host.** *(Corrected 2026-09-22, same day; the first version of
this paragraph was wrong twice.)* It first said `pg_dump` runs in the `postgres`
container over `exec -T` and streams to the upload under `set -o pipefail`:

- **`exec` is not available to a one-shot container** without the Docker socket,
  which is root on the host. The backup image is built `FROM postgres:16` instead
  and connects over the compose network — the client still matches the server,
  which was the reason for `exec`.
- **`pipefail` does not stop a truncated upload.** If `pg_dump` dies mid-stream,
  `aws s3 cp -` sees end of input, completes the upload and exits 0; `pipefail`
  fails the *job*, but the partial object is already in the bucket, and the job's
  credential cannot delete it. It sits there for the retention window looking like
  a backup.

So the dump goes to a temporary file in the container's own writable layer — not
a host path, mounted by nothing, and gone when the `--rm` container exits — and is
uploaded only if `pg_dump` exited 0. A bad dump never reaches the bucket. Cost:
~128 MB of transient space. *(A `pg_restore --list` check before upload was
planned and dropped: nothing could make it fail where `pg_dump` had succeeded,
so it could never be seen to catch anything.)*

**A dump must never land under a path the proxy mounts.** The proxy serves
`./media`, `./static`, `./var/public` and `./var/maintenance` to the internet; a
dump in any of them is downloadable by anyone who guesses the name, and it holds
password hashes, email addresses and private messages. Keeping the dump inside the
container makes this hold by construction; if a host copy is ever added, it goes
in a root-owned `0700` directory mounted into no container. **Direction matters in
the requirements below: `/media` is a *source* of the backup, never a
destination.**

**Requirement 8 needs a dead-man's switch, not only a failure alarm.** An alarm
on failure catches a job that runs and breaks; it cannot catch a job that never
starts — a timer not installed, a disabled unit, a VM that is off. The job checks
in with an external heartbeat service on success, and silence is the alarm.
Neither a timer nor beat can report its own absence.

**Two buckets, not one — decided 2026-09-22.** Dumps and media need opposite
retention: a dump's current object expires after **90 days**; a media file's
never does, because an untouched 2012 photo is still the only off-site copy.
**The media bucket keeps everything, current and noncurrent versions, forever**;
its only lifecycle rule aborts incomplete multipart uploads. One bucket with
prefix-filtered rules would work until a filter was dropped, and then expire the
media silently while the site kept serving it from disk. Separate buckets make
each rule whole-bucket. **Both are versioned**: a put-only credential can still
overwrite, and versioning is what keeps the overwritten original. One job
credential, put-and-list on both, nothing that deletes.

**The buckets: new and dedicated** — as already recorded below and in
runbook B7 — **provided the VM is not on AWS.** The VM's provider is still
open between Linode and Lightsail (`research/hosting.md`); on Lightsail an S3
bucket shares the provider and fails the constraint, so the bucket choice is
settled only once the VM is.

### Why the provider is deferred, and what is decided instead

**`plan.md` says only *"Backups still go to object storage."*** No provider is
chosen anywhere in the record; the design mentions Linode Object Storage in a
costing example and nothing more.

**Nothing in this task needs the answer.** The dump, the schedule, the retention
shape, the alarm, the media backup and the restore drill are all provider-neutral.
AWS S3 and Linode Object Storage both speak the S3 API, so the difference is an
endpoint URL and a credential — configuration, in the pattern
`sg101/settings/base.py:377-387` already uses for the user-photos bucket, its
base URL and its region.

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
   adding — scheduling, upload, retention, alarming. Read *Decided 2026-09-22*
   first: the trigger, the streaming route and the no-served-path rule are
   settled, and the tool's `./snapshots` route is dev-only.
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
