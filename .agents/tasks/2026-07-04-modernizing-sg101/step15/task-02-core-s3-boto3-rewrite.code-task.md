# Task: Rewrite `core/s3.py` for boto3

## Description
Replace the boto v2 implementation of `core/s3.py` with boto3, and drop the
import guard that has stood in for it since the Python 3 flip. `S3Bucket` keeps
its public API so its callers do not change; the five tests in
`core/tests/test_s3.py` are retargeted from boto v2's names to boto3's.

This is the core of Step 15 — the "its callers import cleanly and their tests
keep mocking it" bargain that Step 8 struck, coming due.

## Background

### What is there now
`core/s3.py` wraps boto v2 behind a small class:

```python
try:
    from boto.s3 import connect_to_region
    from boto.s3.connection import OrdinaryCallingFormat
    from boto.s3.key import Key
    _BOTO_AVAILABLE = True
except ImportError:
    ...
    _BOTO_AVAILABLE = False
```

`S3Bucket.__init__` raises `NotImplementedError` when `_BOTO_AVAILABLE` is
False. **boto is absent from every requirements file** — the only mention is a
comment at `requirements.txt:5` — so on this branch, today, constructing an
`S3Bucket` always raises.

The public API is five methods: `upload_from_file`, `upload_from_filename`,
`upload_from_string`, `delete_keys`, and the private `_make_key`.

### Its consumers, after task 01
Two, both of which must keep working unchanged:

- `core/images/upload.py:38` — `process_upload()`'s S3 branch, the live photo
  upload path
- `user_photos/s3.py:20` — `delete_photos()`, reached from
  `user_photos/views.py:194`, `user_photos/admin.py:26` and
  `antispam/utils.py:103`

Task 01 removes the third (`ssl_images`). If task 01 has not run, this task's
API contract is wider by that one caller.

### The module docstring is stale in two ways
It says storage "is slated to move to Cloudflare R2 via boto3." **Both halves are
wrong now**: the destination is the existing S3 bucket, not R2, and the move is
this task, not a later step. The `NotImplementedError` message repeats the same
claim. Neither should survive this task.

### The boto3 shape is a real decision — record it
boto3 offers a low-level `client` and a higher-level `resource`. The v2 code is
resource-shaped (`Key` objects with `set_contents_from_*`), so `resource` maps
more directly, but `client` is the better-supported surface and the one AWS
documents first. **Pick one, and record why**, the way Step 13 task 06 recorded
psycopg 3 and Step 13 task 09 recorded `USE_TZ`.

Mappings either way:

| boto v2 | boto3 (client) |
| --- | --- |
| `connect_to_region(region, ...)` | `boto3.client('s3', region_name=..., aws_access_key_id=..., aws_secret_access_key=...)` |
| `conn.get_bucket(name, validate=False)` | no equivalent needed — the bucket is a parameter, not an object |
| `Key(bucket)` + `key.set_metadata(k, v)` | `Metadata={...}` on the write call |
| `key.set_contents_from_file(fp)` | `put_object(Body=fp, ...)` or `upload_fileobj` |
| `key.set_contents_from_filename(f)` | `put_object(Body=open(...))` or `upload_file` |
| `key.set_contents_from_string(s)` | `put_object(Body=s, ...)` |
| `key.make_public()` | `ACL='public-read'` on the write call |
| `bucket.delete_keys([...], quiet=True)` | `delete_objects(Delete={'Objects': [{'Key': k}, ...], 'Quiet': True})` |
| `OrdinaryCallingFormat()` | not needed — addressing style is negotiated, or set via `Config(s3={'addressing_style': 'path'})` |

**`make_public()` deserves a thought rather than a transliteration.** The
existing objects in `sg101.user.photos` are public-read, and the site serves them
as plain URLs, so new objects must match. But buckets created or reconfigured
since 2023 may have Block Public Access or a bucket-owner-enforced ownership
setting that makes a per-object `ACL='public-read'` **fail outright**. This
cannot be settled from the repo — it is a property of the live bucket. Task 05's
tool is what answers it. Write the code so the ACL is one clearly-marked place.

### `delete_keys()` has a counting bug — do not preserve it
```python
response = self.bucket.delete_keys(keys, quiet=True)
return len(key_urls) - len(response.errors)
```
`keys` is the subset of `key_urls` whose prefix matched this bucket. The return
subtracts errors from **`key_urls`**, the unfiltered input — so URLs that were
skipped for not being S3 URLs are counted as deleted.

The existing `test_delete_keys` **pins the bug**: it passes three URLs of which
two match, and asserts `3`.

This matters right now because 4,577 of the 26,331 `user_photos.Photo` rows are
local-disk URLs, so the skipped set is not hypothetical. **Task 04 owns the
fix**, including what should happen to those local files. This task should
either leave `delete_keys` counting exactly as it does and let task 04 change it,
or fix the count here and hand task 04 a smaller job — **but it must not
silently carry the bug forward into new code as though it were intended.**
State which you did.

### Testing: mocks, by Brian's decision (2026-08-16)
`moto` was considered and **declined** — no new dependency; the five tests are
retargeted from `core.s3.connect_to_region` / `core.s3.Key` /
`core.s3.OrdinaryCallingFormat` to boto3's names, keeping their present
call-list-assertion shape.

**The consequence has to be designed around, not just noted.** A mock accepts
any kwarg, so a wrong argument name, a wrong method, or a wrong `Metadata`
shape stays green. This project has been bitten by exactly that: Step 13 task 07
reverted `Image.ANTIALIAS` together with its mock assertions and **41 tests
stayed green while a real upload raised `AttributeError`**.

Two things follow, and both are requirements below:

1. **Every new test must be mutation-verified** — reverted deliberately, watched
   to fail, restored. An assertion that cannot fail is not coverage.
2. **The real verification is task 05's tool**, against the live bucket. This
   task's suite proves the wiring is what we intended; only task 05 proves the
   intention was right. Do not describe this task as "verified" on a green suite.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 15: the S3-not-R2 reversal and why the blocker was the interpreter)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 8, which stubbed this module; Step 13 task 07, for the mock-coverage
  failure mode)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Add `boto3` to `requirements.txt`** with a pin and a comment saying what
   uses it. Remove the stale boto comment at `requirements.txt:5`.
2. **Choose `client` or `resource` and record the reason** in the code and the
   write-up. Do not leave the choice implicit in the diff.
3. Rewrite `S3Bucket` on boto3, **keeping the five-method public API and the
   constructor signature** (`access_key`, `secret_key`, `base_url`,
   `bucket_name`, `region_name='us-west-1'`) so both callers are untouched by
   this task.
4. **Delete the `try`/`except ImportError` guard, `_BOTO_AVAILABLE`, and the
   `NotImplementedError`.** The module either works or fails loudly.
5. **Rewrite the module docstring and remove every reference to Cloudflare R2**,
   in this file and anywhere else in the module's comments. Both claims it makes
   are now false.
6. Keep the returned URL format byte-identical: `'{base_url}{bucket}/{key}'`
   with the trailing-slash normalization the constructor does. **26,331 existing
   rows are absolute URLs in this format** and new rows must be
   indistinguishable from the 21,754 already on S3.
7. Put the public-read ACL in **one clearly-marked place**, with a comment noting
   that the bucket's own configuration can override it and that task 05 is what
   verifies it.
8. Retarget the five tests in `core/tests/test_s3.py` to boto3's names and
   **remove the `@unittest.skip`** that has disabled the class since Step 8.
9. **Mutation-verify every test in the file**: revert the behavior each asserts,
   confirm the test fails, restore. Record the five mutations and their results.
10. State explicitly what you did about `delete_keys`' count — preserved for task
    04, or fixed here — and make sure no test asserts the wrong number as though
    it were correct.
11. Suite green, `check` clean, deprecation gate green. **boto3 is a new
    dependency: re-run the gate and report whether it adds any warning.**

## Dependencies
- Task 01 (retire `ssl_images`) — not a hard prerequisite, but it removes one of
  three `S3Bucket` consumers and should land first
- Step 14 complete: Django 5.2.17 / Python 3.12.14
- No live AWS credentials are needed for this task; task 05 is where they matter

## Implementation Approach
1. Add and pin `boto3`; confirm it installs and imports in the container on
   Python 3.12 before writing any code.
2. Decide `client` vs `resource` on the two callers' needs, and write the reason
   down before implementing.
3. Rewrite the module, keeping the API fixed. Take the docstring seriously — it
   is currently a set of false statements about a plan that reversed.
4. Retarget the tests one at a time, running each as you go.
5. Mutation-verify all five. Expect at least one to be untestable as written and
   need strengthening — that is the point of the exercise, not a setback.
6. Re-run the deprecation gate with the new dependency in the image.
7. Write up the shape decision, the ACL question left open for task 05, and the
   `delete_keys` count disposition.

## Acceptance Criteria

1. **boto3 Pinned and Documented**
   - Given `requirements.txt`
   - When it is read after this task
   - Then `boto3` is pinned with a comment naming `core/s3.py` as its consumer,
     and the stale boto/R2 comment is gone

2. **The Guard Is Gone**
   - Given `core/s3.py`
   - When it is read after this task
   - Then there is no `try`/`except ImportError`, no `_BOTO_AVAILABLE`, and no
     `NotImplementedError` — constructing an `S3Bucket` either works or raises a
     real boto3 error

3. **The API Did Not Move**
   - Given `core/images/upload.py` and `user_photos/s3.py`
   - When this task completes
   - Then neither file has been modified, and both still construct and call
     `S3Bucket` exactly as before

4. **URL Format Preserved**
   - Given a key uploaded through any of the three `upload_from_*` methods
   - When the returned URL is compared to the format of the 21,754 existing S3
     rows
   - Then it is identical in scheme, host, bucket segment and key placement

5. **The Shape Decision Is Recorded**
   - Given the choice between boto3's `client` and `resource`
   - When the write-up is read
   - Then it names which was chosen and the reason, rather than leaving it to be
     inferred from the diff

6. **Tests Retargeted and Un-Skipped**
   - Given `core/tests/test_s3.py`
   - When the suite runs
   - Then the `@unittest.skip` is gone and all five tests execute and pass

7. **Every Test Is Mutation-Verified**
   - Given the five retargeted tests
   - When each asserted behavior is deliberately reverted in turn
   - Then the corresponding test fails every time, and the write-up records all
     five mutations and their outcomes

8. **The delete_keys Count Is Handled Deliberately**
   - Given the pre-existing miscount and the 4,577 local-disk rows
   - When this task completes
   - Then the write-up states whether the count was preserved for task 04 or
     fixed here, and no test asserts the wrong count as though it were intended

9. **The Docstring Tells the Truth**
   - Given the module's docstring and comments
   - When they are read after this task
   - Then nothing claims a move to Cloudflare R2 or a temporary disablement, and
     the ACL comment names task 05 as what verifies bucket configuration

10. **Suite, Checks and Gate Clean**
    - Given `boto3` newly in the image
    - When the suite, `check`, `makemigrations --check` and
      `tools/deprecation_gate.sh` run
    - Then all are clean, and the write-up reports whether boto3 introduced any
      deprecation warning and how it was handled

## Metadata
- **Complexity**: Medium
- **Labels**: S3, boto3, Storage, Step 8 Stub, Step 15
- **Required Skills**: boto3 client/resource APIs and S3 semantics, `unittest.mock`
  call-list assertions, mutation testing, Python packaging
