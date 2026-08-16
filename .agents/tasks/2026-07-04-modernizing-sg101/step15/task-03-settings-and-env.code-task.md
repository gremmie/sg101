# Task: Env-Configure the Remaining `USER_PHOTOS_*` Settings and Re-Enable S3 Uploads

## Description
Move the S3 destination settings out of hardcoded literals into the environment,
add the region setting the code has never had, and flip
`USER_PHOTOS_LOCAL_UPLOAD` back to `False` so new uploads go to
`sg101.user.photos` again.

This is the switch-flip of Step 15. Tasks 01, 02 and 04 make it safe to throw.

## Background

### The plan overstates this item — measured 2026-08-16
Step 15's guidance says to "env-configure `USER_PHOTOS_*`". **Most of that is
already done.** `sg101/settings/base.py:329-350` reads:

```python
USER_PHOTOS_ENABLED = True
USER_PHOTOS_ACCESS_KEY = env('AWS_ACCESS_KEY', default='')
USER_PHOTOS_SECRET_KEY = env('AWS_SECRET_KEY', default='')
USER_PHOTOS_BUCKET = 'sg101.user.photos'
USER_PHOTOS_BASE_URL = 'https://s3-us-west-1.amazonaws.com'
USER_PHOTOS_MAX_SIZE = (660, 720)
USER_PHOTOS_THUMB_SIZE = (120, 120)
USER_PHOTOS_RATE_LIMIT = (50, 86400)   # number / seconds
...
USER_PHOTOS_LOCAL_UPLOAD = False
USER_PHOTOS_LOCAL_UPLOAD_DIR = 'user_photos'
```

**The credentials have been env-driven since Step 3** — `AWS_ACCESS_KEY` and
`AWS_SECRET_KEY`, already present in `.env.example:27-29`. What is actually left:

- `USER_PHOTOS_BUCKET` — hardcoded
- `USER_PHOTOS_BASE_URL` — hardcoded
- **the region does not exist as a setting at all.** `S3Bucket`'s signature
  carries `region_name='us-west-1'` as a default argument and both call sites
  omit it, so the region is a literal buried in a function signature.

The sizes and the rate limit are deployment-invariant and stay as literals.

### `USER_PHOTOS_LOCAL_UPLOAD = True` is committed, not an uncommitted edit
It is at `sg101/settings/production.py:74`, tracked, from `e53aa1f`
("Turn on user photos local upload in prod", 2025-01-04). Flipping it is a
one-line edit to a tracked file.

**This does not retire the Step 21 audit item.** The plan's finding stands: local
uploads demonstrably began **2023-05-08** and were only committed twenty months
later, which means production ran an *uncommitted* edit to `production.py` for
that whole period, and `fab update`'s `hg pull --update` preserves such edits
silently. The lesson is that a second, still-uncommitted edit could exist and
nothing in the repo would reveal it. Step 21 audits the working copy with
`hg status` / `hg diff` before cutover. **This task settles this one setting; it
does not settle the class of problem.**

### `USER_IMAGES_SOURCES` needs no change
```python
USER_IMAGES_SOURCES = [
    'dl.dropboxusercontent.com',
    's3.amazonaws.com',
    's3-us-west-1.amazonaws.com',
    'scontent-ord1-1.xx.fbcdn.net',
    'lh3.googleusercontent.com',
    'surfguitar101.com',
]
```
`s3-us-west-1.amazonaws.com` is already whitelisted, so as long as
`USER_PHOTOS_BASE_URL` keeps that host, hotlinking and `core/html.py`'s
sanitizer accept the new URLs unchanged. **If this task parameterizes the base
URL, a deployment that points it somewhere else silently breaks image display**
— the whitelist would reject the site's own photos. Guard against it.

`surfguitar101.com` also stays: the 4,577 local-disk rows are served from it and
are not going anywhere (see task 04 and Step 21).

### Do not break `docker_test`
`core/tests/test_settings.py` is the seam that covers settings loading, and Step
14 task 05 found `django-environ` bumps are the ones most likely to disturb it.
Any new `env()` call needs a default that keeps the test settings importable
without a populated `.env`.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 15's guidance paragraph; Step 21's working-copy audit item)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 3, which established the env-var configuration and `.env.example`)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Correct the plan's premise in the write-up**: the credentials were already
   env-driven, and what this task actually moves is the bucket, the base URL and
   a region that did not previously exist as a setting.
2. Add `USER_PHOTOS_BUCKET` and `USER_PHOTOS_BASE_URL` as `env()` reads with
   their **current values as defaults**, so an unset environment reproduces
   today's behavior exactly.
3. **Add `USER_PHOTOS_REGION`** (default `'us-west-1'`) and pass it explicitly
   from both `S3Bucket` call sites, so the region stops living in a function
   signature default.
4. Update `.env.example` with the new keys, their defaults, and a comment saying
   these must match the host the 21,754 existing rows already point at.
5. **Set `USER_PHOTOS_LOCAL_UPLOAD = False`** in `sg101/settings/production.py`.
   Leave `base.py`'s `False` as is. Do not remove the setting — the local branch
   stays in the code and is still what `tools/image_smoke.py` drives by default.
6. **Add a guard or an explicit check that `USER_PHOTOS_BASE_URL`'s host is in
   `USER_IMAGES_SOURCES`.** A base URL pointing at an unwhitelisted host would
   upload successfully and then fail to display, which is the worst shape of
   failure available here.
7. Do not change `USER_PHOTOS_MAX_SIZE`, `USER_PHOTOS_THUMB_SIZE`,
   `USER_PHOTOS_RATE_LIMIT` or `USER_PHOTOS_LOCAL_UPLOAD_DIR`.
8. `core/tests/test_settings.py` passes, and the stack still boots from `.env`
   alone — the Step 3 acceptance condition.
9. Suite green, `check` and `check --deploy` clean, gate green.

## Dependencies
- Task 02 (boto3 rewrite) — the constructor signature must be settled before
  call sites start passing a region explicitly
- Task 04 (delete path) should land before this flip reaches a real deployment:
  turning uploads back on while `delete_photos` still raises would leave members
  able to add photos they cannot remove

## Implementation Approach
1. Read the current settings and confirm for yourself which are already
   env-driven — do not take this task file's word for it.
2. Add the three `env()` reads with current-value defaults; confirm an empty
   environment reproduces today's settings exactly.
3. Thread `USER_PHOTOS_REGION` through both `S3Bucket` call sites.
4. Add the whitelist consistency check, with a test that it fires.
5. Update `.env.example`.
6. Flip `production.py:74` last, once everything else is green.
7. Boot the stack from `.env` alone and run `core/tests/test_settings.py`.

## Acceptance Criteria

1. **The Plan's Premise Is Corrected**
   - Given the plan's "env-configure `USER_PHOTOS_*`" guidance
   - When the write-up is read
   - Then it records that the credentials were already env-driven since Step 3,
     and names the three settings this task actually moved

2. **Defaults Reproduce Today's Behavior**
   - Given an environment with none of the new variables set
   - When settings are loaded
   - Then `USER_PHOTOS_BUCKET` is `sg101.user.photos`,
     `USER_PHOTOS_BASE_URL` is `https://s3-us-west-1.amazonaws.com`, and
     `USER_PHOTOS_REGION` is `us-west-1`

3. **The Region Is a Setting, Not a Signature Default**
   - Given both `S3Bucket` call sites
   - When they are read after this task
   - Then each passes `region_name` explicitly from settings, and the region no
     longer depends on the constructor's default argument

4. **The Whitelist Cannot Drift From the Base URL**
   - Given a `USER_PHOTOS_BASE_URL` whose host is absent from
     `USER_IMAGES_SOURCES`
   - When settings load or the check runs
   - Then the mismatch is surfaced loudly rather than producing photos that
     upload successfully and fail to display

5. **Production Uploads to S3 Again**
   - Given `sg101/settings/production.py`
   - When it is read after this task
   - Then `USER_PHOTOS_LOCAL_UPLOAD` is `False`, and the setting still exists so
     the local branch remains reachable for tooling

6. **`.env.example` Is Complete and Honest**
   - Given the new variables
   - When `.env.example` is read
   - Then all three appear with their defaults and a comment stating they must
     match the host the existing 21,754 rows point at

7. **The Stack Still Boots From `.env` Alone**
   - Given only `.env`
   - When the stack is started and `core/tests/test_settings.py` runs
   - Then every setting resolves and the test passes, preserving Step 3's
     acceptance condition

8. **Suite, Checks and Gate Clean**
   - Given the settings changes
   - When the suite, `check`, `check --deploy` and `tools/deprecation_gate.sh`
     run
   - Then all are clean

## Metadata
- **Complexity**: Low
- **Labels**: Settings, 12-Factor, Environment, S3, Step 15
- **Required Skills**: `django-environ`, Django settings layering, reading a
  setting's real consumers before parameterizing it
