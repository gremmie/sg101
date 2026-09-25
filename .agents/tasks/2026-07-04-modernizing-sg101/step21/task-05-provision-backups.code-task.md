# Task: Provision the Backups on Real Accounts, and Repoint or Retire bobcat

## Description
Create the two backup buckets on AWS S3, run the backup job for real, **prove
the failure alarm reaches Gmail**, restore once from the real bucket, and
install the timer. Then decide what bobcat — the second Linode that has rsynced
jaguar nightly for years — does after cutover.

## Background
Step 20 task 06 built the whole backup path (a `backup` compose service
dumping to a database bucket and syncing media to a media bucket, versioned,
with a 90-day expiry on the dumps) and drilled it against local MinIO with
`tools/backup_drill.sh`. Runbook **B12** is the step-by-step for real accounts;
this task performs it.

**The bucket rule from B7 is satisfied by the provider decision.** Backups must
not share a provider or account with the VM, since one billing lapse or
account event would take both. The VM is on **Linode** (decided 2026-09-24), so
**AWS S3 satisfies it**, and boto3 plus AWS credentials are already in the
project from Step 15. Use **new** buckets, not `sg101.user.photos` or
`sg101.forum.photos`, and an IAM user whose only policy is
`backup/policy-writer.json` — it writes objects; it cannot read or delete.

**bobcat** (`bobcat.gremmielabs.dev`, 198.58.104.73) rsyncs jaguar nightly at
03:15 — the MySQL dumps, the media tree, the wiki, and Brian's other sites.
After cutover it goes on backing up a machine nobody uses, and **its alarm is
almost deaf**: measured 2026-08-18, roughly one refused report a day (Gmail
`5.7.25`/`5.7.1`, from a PTR that does not forward-confirm and a HELO name with
no A record). Repointing it at the new VM makes it the second, same-provider
copy B7 describes. The alternative is retiring it now that S3 holds offsite
copies. **Brian's decision**; the plan has assumed repointing so far.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C10 — backups to object storage)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — B7, B12
- `DOCKER.md` §10, *Backups, and restoring from them*
- `.agents/tasks/2026-07-04-modernizing-sg101/step20/task-06-backups-to-object-storage.code-task.md`
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step
  21, the bobcat item

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Both buckets created with `backup provision` using an administrative
   credential that is not left on the VM; versioning on; the dump lifecycle
   applied; the media bucket with no lifecycle rules; Block Public Access
   confirmed on both.
2. The job's IAM user has `backup/policy-writer.json` and nothing else. Show that
   it cannot read or delete, rather than trusting the policy text.
3. A healthchecks.io check (period 1 day, grace 2 hours) alerts Gmail. The
   alarm is proven by a run with a wrong database password, **seen arriving in
   Gmail**, not only on the dashboard.
4. `secrets/backup.env` holds the ping URL, buckets and key, root-only.
5. The first full run completes (~4.7 GB of media); its duration and the
   host's memory during `pg_dump` are recorded — task 07 needs both.
6. One restore from the real bucket into a scratch database, compared by row
   counts with the source.
7. The systemd timer installed and listed.
8. bobcat: Brian's decision recorded. If repointed: its exclude file must
   **not** drop the Apache logs this time (task 01's finding), and its report mail
   must reach Gmail. Either fix its reverse DNS and HELO as recorded, or send its
   reports through Postmark the way task 04 does for the VM.
9. A reminder around day 91 to confirm the oldest dumps have actually expired.

## Dependencies
- Task 03 (the VM and stack); task 04 (host mail), for the timer's failure mail
- AWS account access; a healthchecks.io account

## Implementation Approach
1. Follow B12 in order, recording each result in `STATUS.md`.
2. Correct B12 wherever reality differed.
3. Put the bobcat question to Brian with both options and what each costs.

## Acceptance Criteria

1. **The alarm reaches a person**
   - Given a backup run with a wrong database password
   - When it fails
   - Then the healthchecks alert arrives in Gmail

2. **The job's credential is write-only**
   - Given the job's IAM key
   - When it tries to list, read and delete an object
   - Then each is refused

3. **A real restore works**
   - Given the newest dump in the real bucket
   - When it is restored into a scratch database
   - Then table row counts match the source

4. **The timer is live**
   - Given the installed units
   - When `systemctl list-timers` runs
   - Then `sg101-backup.timer` is listed with its next run

5. **bobcat has a recorded fate**
   - Given Brian's decision
   - When this task closes
   - Then bobcat is repointed with logs included and a working alarm, or retired,
     and any cutover-day part is in the runbook

## Metadata
- **Complexity**: Medium
- **Labels**: Backups, AWS S3, IAM, Monitoring, Operations
- **Required Skills**: AWS S3 and IAM, systemd timers, PostgreSQL restore, rsync
