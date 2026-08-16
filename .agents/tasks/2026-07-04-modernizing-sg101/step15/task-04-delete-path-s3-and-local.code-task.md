# Task: Make Photo Deletion Work for Both S3 and Local-Disk Photos

## Description
`delete_photos()` is S3-only, unguarded, and currently raises on every delete
path in the site. Route each photo URL to the right backend — S3 objects to the
bucket, local-disk files to `os.unlink` under `MEDIA_ROOT` — and make the
returned count mean what its callers already assume it means.

**This is its own separately-verified commit.** It introduces a filesystem
delete under `MEDIA_ROOT` driven by database contents, which is the most
destructive path Step 15 adds, and it deserves to be reviewable on its own.

## Background

### Deleting a photo raises today — measured 2026-08-16
This is not a latent risk; it is a live break on this branch. `user_photos/s3.py`
constructs the bucket **before looking at any URL**:

```python
def delete_photos(qs):
    bucket = S3Bucket(settings.USER_PHOTOS_ACCESS_KEY, ...)   # raises here
    key_urls = []
    for photo in qs:
        ...
```

Until task 02 lands, `S3Bucket.__init__` raises `NotImplementedError` because
boto v2 is absent. Three call sites, **none of which guards**:

| Call site | Reached by |
| --- | --- |
| `user_photos/views.py:194` | a member deleting their own photos |
| `user_photos/admin.py:26` | the admin's `custom_delete` action |
| `antispam/utils.py:103` | spam cleanup, deactivating a user |

**The suite is green only because all three are mocked** —
`user_photos/tests/test_upload_views.py:242,252,262` patch
`user_photos.views.delete_photos`. Nothing exercises the real function.

**The plan says "only *uploading* ever broke."** That is true of production on
Python 2.7, where boto works. It is false of this branch, and the difference has
been invisible for six steps because of those three mocks.

### The count is wrong, and it will start mattering
```python
prefix = '{}{}/'.format(self.base_url, self.name)
keys = [url[len(prefix):] for url in key_urls if url.startswith(prefix)]
response = self.bucket.delete_keys(keys, quiet=True)
return len(key_urls) - len(response.errors)      # <- unfiltered input
```

URLs that were skipped for not matching the prefix are counted as deleted.
`core/tests/test_s3.py`'s `test_delete_keys` **pins this**: three URLs in, two
match, asserts `3`.

`user_photos/s3.py:35` then compares that count to the request count and logs
success:

```python
if act_cnt == req_cnt:
    logger.info("Deleted %d user photo(s) from S3", act_cnt)
else:
    logger.warning("Deleted %d user photo(s) out of %d", act_cnt, req_cnt)
```

So once boto3 works, deleting a local-disk photo will **leave the file on disk,
delete the database row, and log complete success.**

### The scale of the skipped set
Measured in the snapshot 2026-08-15 — 26,331 `user_photos.Photo` rows, storing
absolute URLs:

| rows | host | `upload_date` range |
| --- | --- | --- |
| 21,754 | `s3-us-west-1.amazonaws.com/sg101.user.photos` | 2013-09-15 → 2023-05-07 |
| 4,577 | `surfguitar101.com` (local disk) | 2023-05-08 → 2026-07-11 |

The local set **keeps growing until the Step 21 DNS flip**, because production
stays live on the old code the whole time. Whatever this task builds has to
handle a set that is larger on cutover day than it is now.

### Brian's decision, 2026-08-16: unlink the local files
Chosen over "skip but count honestly" and over deferring to Step 19/21.

**This does not breach Step 15's "migrate nothing" rule.** That rule is about not
moving the 4,577 files into the bucket — a rewrite that could not survive Step
21's fresh snapshot. This is the delete path doing what its three callers already
believe it does. Nothing is moved, no row's URL is rewritten, and the 4,577 that
are never deleted still ride the Step 21 media rsync untouched.

The payoff is concrete: the orphans stop accumulating now, and Step 21 rsyncs a
tree without three years of files whose rows are gone.

### How local URLs are built — the mapping this task must invert
`core/images/upload.py:178-188`:

```python
def _user_photo_url(filename):
    url_pattern = '%s://%s%s%s/%s'
    site = Site.objects.get_current()
    return url_pattern % (settings.SITE_SCHEME, site.domain,
                          settings.MEDIA_URL,
                          settings.USER_PHOTOS_LOCAL_UPLOAD_DIR, filename)
```

So a local URL is `{scheme}://{site.domain}/media/user_photos/{name}`, and the
file is at
`os.path.join(settings.MEDIA_ROOT, settings.USER_PHOTOS_LOCAL_UPLOAD_DIR, name)`.

**Three hazards in inverting that:**

1. **`SITE_SCHEME` is `http` in `base.py:55`** but production serves https, and
   rows exist from both eras. Match on **host and path**, never on scheme.
2. **`site.domain` may not equal the stored host.** `USER_IMAGES_SOURCES` carries
   both `surfguitar101.com` and (via `SG101_HOSTS` elsewhere in the tree)
   `www.surfguitar101.com`. Accept both, or match on the path prefix and treat
   any non-S3 URL with the right path shape as local.
3. **The filename comes from the database**, so it is attacker-influenced in
   principle. `..%2F` and absolute paths must not escape.

### The guard is not optional
The final path **must resolve under `MEDIA_ROOT/USER_PHOTOS_LOCAL_UPLOAD_DIR`**,
verified with `os.path.realpath` after joining, not by string inspection before
it. A delete driven by a URL column with no containment check is the kind of
thing that is fine until one row is strange.

Deleting a file that is already gone is **not an error** — the row is being
removed either way, and a missing file must not abort the batch or leave the
member unable to delete. Log it and continue.

### `media/user_photos` does not exist in the dev checkout
Those files live only on production. **Dev cannot rehearse this against real
data**, so the tests must create their own fixture files under a temporary
`MEDIA_ROOT` — `core/tests/images/test_real_images.py:113-114` already
establishes that pattern with `override_settings`, and `tools/image_smoke.py`
creates and tears down the upload dir at line 76.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 15's "MIGRATE NOTHING" section, and Step 21's media rsync)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 14 task 04, on probes that perturb what they measure; Step 13 task 07,
  on mock assertions that cannot fail)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Take a database snapshot before any verification that writes**
   (`tools/pg_snapshot.sh dump <label>`). This task deletes rows and files.
2. Route each URL in `delete_photos()` by destination: S3 URLs to the bucket,
   local URLs to the filesystem, anything unrecognized **skipped and logged, not
   guessed at**.
3. **Do not construct the `S3Bucket` unless there is at least one S3 URL to
   delete.** A member deleting only local photos must not need working AWS
   credentials.
4. **Containment guard:** the resolved local path must be under
   `MEDIA_ROOT/USER_PHOTOS_LOCAL_UPLOAD_DIR`, checked with `os.path.realpath`
   after the join. A path that escapes is skipped and logged as an error.
5. Match local URLs on **host and path**, never on scheme, and accept both
   `surfguitar101.com` and `www.surfguitar101.com`.
6. A missing local file is logged and treated as success — it must not abort the
   batch or block the row deletion.
7. **Fix the count.** The return value must be the number of photos actually
   deleted, across both backends. If task 02 left `delete_keys`' count as it was,
   fix it here, including its test.
8. `user_photos/s3.py`'s success/warning log must remain meaningful once the
   count is honest — a partial delete should log the warning branch, and it
   should be possible to see which backend fell short.
9. **The module is no longer S3-only. Say so.** `user_photos/s3.py`'s name and
   docstring both claim it is "for all S3 related operations"; at minimum the
   docstring must stop being false. Renaming the module is optional and, if
   done, must update its three importers.
10. **Tests must exercise the real function, not a mock**, for: an S3-only
    batch, a local-only batch, a mixed batch, a missing local file, a
    containment-guard violation, and the count in each case.
11. **Mutation-verify each new test** — remove the guard, break the routing,
    revert the count — and record the results. Mock-shaped assertions that
    cannot fail are the specific failure mode this project has already hit twice.
12. Leave the three existing mocked view tests in place; they cover the view's
    contract, not this function's.
13. Suite green, `check` clean, gate green.

## Dependencies
- Task 02 (boto3 rewrite) — `delete_keys` must actually work before its count
  can be verified end to end
- Task 03 should not reach a real deployment before this lands: enabling S3
  uploads while deletion still raises would let members add photos they cannot
  remove
- A PostgreSQL snapshot before any verification against real data

## Implementation Approach
1. Snapshot the database first.
2. Write the URL-routing helper and its containment guard before touching
   `delete_photos`, and test it in isolation — it is the part with the security
   property.
3. Rework `delete_photos` to partition the queryset's URLs, then call each
   backend only if it has work.
4. Fix the count, and follow it into `core/tests/test_s3.py`'s `test_delete_keys`
   if task 02 left it pinning the old behavior.
5. Build the test fixtures with a temporary `MEDIA_ROOT`, following
   `core/tests/images/test_real_images.py`'s pattern.
6. Mutation-verify everything, including the guard — a containment check that
   has never been observed failing is not known to work.
7. Fix the docstring; decide on the module name and say why either way.
8. Run `tools/image_smoke.py`, which drives the local upload path end to end, to
   confirm nothing in the local branch regressed.

## Acceptance Criteria

1. **Deleting a Local Photo Removes Its File**
   - Given a `Photo` row whose URL points at `MEDIA_ROOT/user_photos/`
   - When `delete_photos()` runs over it
   - Then the file and its thumbnail are gone from disk and the returned count
     includes it

2. **Deleting an S3 Photo Still Deletes From the Bucket**
   - Given a `Photo` row whose URL points at `sg101.user.photos`
   - When `delete_photos()` runs over it
   - Then the object is deleted through `S3Bucket.delete_keys` exactly as before

3. **Mixed Batches Are Handled Per Row**
   - Given a queryset containing both S3 and local photos
   - When `delete_photos()` runs
   - Then each row is deleted from its own backend and the count equals the total
     actually removed

4. **No Credentials Needed for a Local-Only Delete**
   - Given a queryset containing only local-disk photos
   - When `delete_photos()` runs with unusable AWS credentials
   - Then it succeeds without constructing an `S3Bucket`

5. **The Containment Guard Holds**
   - Given a `Photo` row whose URL resolves outside
     `MEDIA_ROOT/USER_PHOTOS_LOCAL_UPLOAD_DIR`
   - When `delete_photos()` runs over it
   - Then nothing outside that directory is unlinked, the row is skipped, and the
     violation is logged as an error

6. **A Missing File Is Not a Failure**
   - Given a local `Photo` row whose file is already gone
   - When `delete_photos()` runs
   - Then the batch completes, the row is still deletable, and the absence is
     logged

7. **The Count Means What Callers Assume**
   - Given any mixture of S3 URLs, local URLs and unrecognized URLs
   - When `delete_photos()` returns
   - Then the value is the number of photos actually deleted — and reverting it
     to `len(key_urls)` makes a test fail

8. **The Real Function Is Under Test**
   - Given the new tests
   - When they run
   - Then they exercise `delete_photos` itself rather than a mock of it, covering
     S3-only, local-only, mixed, missing-file and guard-violation cases

9. **Every New Test Is Mutation-Verified**
   - Given the routing, the guard and the count
   - When each is deliberately broken in turn
   - Then a test fails every time, and the write-up records each mutation

10. **The Docstring Stops Lying**
    - Given `user_photos/s3.py`
    - When it is read after this task
    - Then it no longer describes itself as handling only S3 operations, and any
      rename decision is recorded with its reason

11. **The Local Upload Path Is Unregressed**
    - Given `tools/image_smoke.py`
    - When it runs against the stack
    - Then every check passes, confirming the local branch still uploads and
      cleans up as before

## Metadata
- **Complexity**: Medium
- **Labels**: S3, Local Storage, Deletion, Path Traversal, Data Safety, Step 15
- **Required Skills**: Filesystem path containment and `realpath` semantics, URL
  parsing, Django `override_settings` with a temporary `MEDIA_ROOT`, mutation
  testing
