# Task: Add an Opt-In S3 Branch to `tools/image_smoke.py` and Verify Against the Real Bucket

## Description
Extend the existing image smoke tool with an opt-in branch that uploads to, reads
back from, and deletes from the real `sg101.user.photos` bucket — then run it to
close Step 15. This is the step's demo and the only thing in it that proves the
S3 code actually works.

## Background

### Why a tool and not a test — Brian's question, 2026-08-16
Because what needs verifying is **environmental, not behavioral**. "Do these
credentials still authenticate after three years dormant, does the bucket policy
still permit a public-read write, does the region still resolve" are properties
of AWS and of the account, not of this diff. Four reasons it cannot live in the
suite:

1. **CI has no AWS credentials and should not have them.** The suite runs under
   `docker compose run` in GitHub Actions; a test hitting real S3 is either
   permanently red or needs secrets, network and spend to go green.
2. **It would fail for reasons unrelated to the change under review**, which
   trains people to ignore a red suite — the most expensive habit a test can
   teach.
3. **Step 21 needs to run exactly this on the new host** before the DNS flip. A
   tool takes a settings module and gets pointed at a new deployment; a test
   buried in the suite does not.
4. **Repo precedent.** `tools/` is where this project already puts
   prove-it-on-this-deployment artifacts: `image_smoke.py`, `pgloader/smoke.py`,
   `pg_snapshot.sh`, `deprecation_gate.sh`.

### The tool already exists and already names this hole
`tools/image_smoke.py` drives the avatar, user-photo and photo-of-the-day
uploads through the real views with real image bytes, then removes everything it
created in a `finally` block. Its docstring says:

> The user-photo path is forced down its LOCAL_UPLOAD branch, because the S3
> branch needs live credentials and would put objects in a real bucket. Both
> branches run the same PIL code and differ only in where the bytes land, so
> this exercises the image handling either way -- **but it is not a test of the
> S3 code.**

That comment was written as a limitation. Step 15 is where it gets an answer, so
**extend this tool rather than adding a new one**: it already has the scratch
user, the image makers, the cleanup discipline and the "take a snapshot first"
warning.

### This is the load-bearing verification, by construction
Brian chose `unittest.mock` over `moto` for task 02 (2026-08-16). That was a
deliberate trade — no new dependency — and its consequence is that **neither a
wrong boto3 kwarg nor a wrong `Metadata` shape nor the `delete_keys` miscount
can fail the suite.** A mock accepts anything.

So this task is not a formality on top of a green suite. It is the first moment
anything confirms the S3 code is right. Step 13 task 07 is the cautionary case:
41 tests stayed green while a real upload raised `AttributeError`.

### The round trip covers both blind spots at once
The tool has to delete what it uploads. That means one run exercises
`upload_from_file` **and** `delete_keys` against the real bucket — the two
things the mocks cannot see — and it verifies task 04's routing on a real S3 URL
rather than a fixture.

### What only this tool can answer
- **Do the credentials still work?** Nothing has uploaded to this bucket since
  **2023-05-07**. `AWS_ACCESS_KEY`/`AWS_SECRET_KEY` are presumed live because
  reads still work, but reads are public and prove nothing about the keys.
- **Does `ACL='public-read'` still succeed?** Buckets touched since 2023 may have
  Block Public Access or bucket-owner-enforced object ownership, either of which
  makes a per-object ACL fail. Task 02 flagged this as unanswerable from the
  repo.
- **Is the served URL byte-identical in form to the existing 21,754 rows?**
- **Does the object come back with its metadata** (`user`, `date`) intact?

### Safety — this writes to the live photo bucket
Non-negotiable properties:

- **Opt-in behind an explicit flag.** The default invocation must keep doing
  exactly what it does today, on the local branch. Nobody gets S3 objects by
  running the tool the way the docstring already tells them to.
- **A distinguishable key prefix** so anything ever leaked is identifiable and
  sweepable by hand — the existing tool's `_image_smoke_user` convention is the
  model.
- **Cleanup in `finally`, verified afterwards**, exactly as the existing tool
  does for its database rows.
- **Never point it at production.** The existing docstring's warning applies with
  more force here, because this reaches beyond the database into shared storage.

### It writes to the database too
The tool creates a user and `Photo` rows. `tools/pg_snapshot.sh dump <label>`
first, as the existing docstring already instructs. Step 14 task 04's lesson also
applies: a probe that perturbs what it measures gives a wrong answer, so the
scratch user and its rows must not be left behind to be counted by anything else.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 15's demo; Step 21, which reruns this on the new host)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 13 task 07, for why a green mocked suite is not verification; Step 14
  task 04, for probes that perturb their subject)
- `DOCKER.md` §8 (`tools/pg_snapshot.sh`)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Extend `tools/image_smoke.py`; do not add a second tool.** Its scratch user,
   image makers, `check()` harness and `finally` cleanup are all reusable.
2. **The S3 branch is opt-in behind an explicit flag** (e.g. `--s3`). The default
   invocation keeps driving `USER_PHOTOS_LOCAL_UPLOAD=True` and touches no
   bucket.
3. The S3 branch must **upload, read back, and delete**, verifying at each stage:
   the object exists and is publicly readable; its `user` and `date` metadata
   survived; the returned URL matches the format of the existing 21,754 rows;
   and after deletion the object is gone.
4. **Use a distinguishable key prefix** for everything it creates, and say in the
   docstring how to sweep leftovers by hand if a run is interrupted.
5. **Clean up in `finally` and verify the cleanup**, including the bucket objects
   — mirroring how the tool already verifies its scratch user is gone.
6. **Exercise the delete through `user_photos.s3.delete_photos`**, not by calling
   the bucket directly, so the run also verifies task 04's routing against a real
   S3 URL.
7. **Update the docstring**: the limitation it currently records has been
   answered, and the new safety properties need stating with the same directness
   as the existing warning.
8. Report the result of each check in the existing `check()` style, so a run is
   readable as a pass/fail list.
9. **Run it**, and record what the run proved — specifically whether the
   credentials still authenticate and whether `public-read` still succeeds.
10. If `public-read` fails against the live bucket, **stop and report rather than
    working around it.** How new objects are made publicly readable is a bucket
    configuration decision for Brian, not something to solve in a smoke tool.
11. Record the tool in `DOCKER.md` beside the other smoke tooling, including the
    credentials it needs and the fact that it writes to a real bucket.
12. **Do not run this against production.**

## Dependencies
- Task 02 (boto3 rewrite) — there is nothing to smoke before it
- Task 03 (settings) — the tool reads the bucket, base URL and region from
  settings
- Task 04 (delete path) — the tool deletes through `delete_photos`
- Live AWS credentials in the environment
- A PostgreSQL snapshot (`tools/pg_snapshot.sh dump <label>`)

## Implementation Approach
1. Snapshot the database.
2. Read the existing tool end to end first — particularly its `created` dict and
   `finally` cleanup, which the S3 branch has to extend rather than duplicate.
3. Add the flag and the S3 branch, with cleanup wired in before the upload is
   ever attempted, so an early failure still tidies up.
4. Run it against the real bucket with a single small image first.
5. Verify the leftovers story by interrupting a run deliberately and confirming
   the documented sweep works.
6. Record the results, including anything the run revealed about bucket
   configuration.
7. Update the docstring and `DOCKER.md`.

## Acceptance Criteria

1. **The Default Invocation Is Unchanged**
   - Given `docker compose exec -T web python /app/tools/image_smoke.py` with no
     flags
   - When it runs
   - Then it behaves exactly as before, drives the local upload branch, and
     touches no bucket

2. **The S3 Branch Round-Trips**
   - Given the `--s3` flag and live credentials
   - When the tool runs
   - Then a photo is uploaded to `sg101.user.photos`, fetched back publicly,
     confirmed to carry its `user` and `date` metadata, deleted, and confirmed
     gone

3. **The URL Form Matches the Existing Rows**
   - Given the URL returned by the upload
   - When it is compared to the format of the 21,754 existing S3 rows
   - Then it is identical in scheme, host, bucket segment and key placement

4. **Deletion Goes Through the Application's Own Path**
   - Given an uploaded photo
   - When the tool deletes it
   - Then it does so via `user_photos.s3.delete_photos`, exercising task 04's
     routing against a real S3 URL

5. **Cleanup Is Verified, Not Assumed**
   - Given a completed or failed run
   - When the `finally` block finishes
   - Then the scratch user, its `Photo` rows and every uploaded object are gone,
     and the tool asserts their absence rather than trusting the delete calls

6. **Leftovers Are Identifiable and Documented**
   - Given an interrupted run
   - When the docstring's sweep instructions are followed
   - Then every object the tool created is findable by its prefix and removable

7. **The Docstring's Limitation Is Retired**
   - Given the current "it is not a test of the S3 code" note
   - When the docstring is read after this task
   - Then it describes what the S3 branch verifies, what credentials it needs,
     and that it writes to a real bucket

8. **The Credentials Question Is Answered on the Record**
   - Given that nothing has uploaded to this bucket since 2023-05-07
   - When the tool has been run
   - Then the write-up states plainly whether the existing credentials still
     authenticate and whether `public-read` still succeeds

9. **A Failing ACL Is Reported, Not Worked Around**
   - Given a bucket configuration that rejects `ACL='public-read'`
   - When the tool hits it
   - Then the run stops and reports it as a configuration decision for Brian,
     with no fallback silently substituted

10. **Documented Beside the Other Tooling**
    - Given `DOCKER.md`
    - When the smoke tooling section is read
    - Then this tool's S3 mode appears with its flag, its credential
      requirements, and its warning

11. **Step 15's Demo Is Satisfied**
    - Given the whole step
    - When a member uploads a photo through the site
    - Then it is stored in `sg101.user.photos` and served from the same host the
      21,754 existing photos already use

## Metadata
- **Complexity**: Medium
- **Labels**: Verification, Smoke Tooling, S3, Live Credentials, Demo, Step 15
- **Required Skills**: boto3 against real S3, S3 bucket policy and object
  ownership semantics, writing destructive tooling with verified cleanup
