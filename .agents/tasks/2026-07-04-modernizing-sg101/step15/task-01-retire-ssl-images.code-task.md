# Task: Retire the `ssl_images` Management Command

## Description
Delete the `ssl_images` management command and its 42 tests, along with the two
settings that exist only to serve it. The command has not run in roughly a
decade, could not have succeeded since May 2023 even if it had, and is one of
the two remaining consumers of `core/s3.py` — removing it first shrinks the API
that task 02's boto3 rewrite has to satisfy.

**This is its own commit, separately verified.** It removes 42 tests from a
suite of 887, which is a visible dent in a number this project has tracked rung
by rung; that number wants to move for one legible reason, on its own, rather
than inside a change that also rewrites S3.

## Background

### What the command was for
`ssl_images` rewrote `http:` image URLs in old forum posts, comments, news
stories and user profiles to `https:`. Images already on a whitelisted host were
rewritten in place; images anywhere else were downloaded, resized to
`PHOTO_MAX_SIZE`, and re-hosted into the `sg101.forum.photos` S3 bucket. It
exists because the site moved to https and a decade of member-pasted `http:`
images would otherwise have tripped mixed-content blocking.

It reads Markdown *source* rather than rendered HTML, which is why it carries
its own copies of Markdown's pre-3.0 image patterns — rebuilt byte-identical
during Step 13 task 08, when Markdown 3.x stopped having patterns to borrow.

### The evidence that it is dead — seven counts
Recorded in `implementation/plan.md` under Step 15 and re-verified for this task
file on 2026-08-16:

- Absent from `CELERY_BEAT_SCHEDULE` (6 entries)
- Absent from every `call_command` site in the tree (7 of them)
- Absent from `fabfile.py`, the Compose files, the Dockerfile, CI and `tools/`
- No `ssl_images.log` and no `ssl_images_cache.json` anywhere in the tree
- Last code change on `main` was **2015-11-27**, and **production's cache file is
  dated the same day** — see below
- Its output signature stops dead in the data: posts containing
  `sg101.forum.photos` run 966 in 2015, 323 in 2016, then 22, 3, 5, 3 and single
  digits through 2025 — a tail consistent with members pasting existing URLs by
  hand, not with the tool running
- It uploads to S3, so it could not have succeeded since AWS completed its TLS
  1.0/1.1 deprecation in **May 2023** regardless

**Grep confirms it today:** the only references to `ssl_images` outside
`.agents/` are the command itself and its test module. Nothing imports it,
schedules it, or documents it.

### Measured on production 2026-08-16 — the last run was 2015-11-27
Brian ran the check on the live box:

```
$ ll ssl_images*
-rw-rw-r-- 1 brian brian   2720 Nov 27  2015 ssl_images_cache.json
-rw-rw-r-- 1 brian brian 306180 Oct 29  2015 ssl_images_cache.json.bz2
```

**`save_cache()` writes the `.json` at the end of a run, so its mtime is the last
time a run completed: 2015-11-27 — the same day as the command's last code change
on `main`.** The command was last run the day it was last worked on, and never
since. This converts the "last code change 2015" count from inference into a
matched pair.

**The two files together bracket the tool's whole working life inside autumn
2015.** Runs up to **Oct 29 2015** built a substantial cache, which was archived
to `.bz2` (306 KB compressed — a lot of cached URLs); a fresh cache then started
from empty, reached 2,720 bytes, and stopped on Nov 27. **An earlier draft of
this file read the small `.json` as "one development run rather than
accumulation," which was wrong — the accumulation is in the `.bz2`.** The
conclusion is unchanged and better supported, and it matches the independent data
signature exactly: 966 posts carrying `sg101.forum.photos` in 2015, 323 in 2016,
single digits after.

Both files are owned **`brian:brian`** and sit in `PROJ_DIR`, where
`CACHE_FILENAME`'s relative path lands when the command is run by hand from the
project directory — not where a daemon under the web server's user would put it.

**The crontab was therefore not checked, and does not need to be.** It is the one
count that cannot be seen from the repo, but no result it could return would
argue for keeping the command: `ssl_images` uploads to S3 from Python 2.7, so it
has been failing since May 2023 regardless, and any entry would be a dead entry.
The only residual gap is a *later* run that crashed before `save_cache()`, which
`/svr/django-sites/sg101/sg101/logs/ssl_images.log` would show since the
`FileHandler` opens before any work happens. Not considered worth the trip.

**Incidental, for Step 21:** both cache files are untracked in production's
working copy and appear as `?` in the `hg status` audit. They are artifacts, not
modifications, and a fresh clone correctly drops them.

### Retiring the command is NOT retiring the bucket
`sg101.forum.photos` must keep serving indefinitely. **15,690 posts and 16
comments** carry `sg101.forum.photos` URLs inside their stored HTML — a decade
of forum images breaks the day that bucket stops answering. Nothing in this task
touches the bucket, its contents, or its lifecycle policy.

What this task removes is the code that *writes* to it. Reads are unaffected
because reads do not go through this code at all: they are plain `<img>` URLs in
stored markup.

### The two settings it orphans
`HOT_LINK_PHOTOS_BASE_URL` and `HOT_LINK_PHOTOS_BUCKET`
(`sg101/settings/base.py:337-338`) have **exactly one consumer between them** —
`ssl_images.py:59-60`. They go with the command.

`USER_IMAGES_SOURCES` does **not** go: `core/html.py:64` and
`user_photos/forms.py:134` both read it, and it is the hotlink whitelist for the
whole site.

### The four models it touches
`MODEL_CHOICES = ['comments', 'posts', 'news', 'profiles']`, backed by imports of
`bio.models.UserProfile`, `comments.models.Comment`, `forums.models.Post` and
`news.models.Story`. The command's own history includes commits named "Modify
ssl_images to update news models" and "Prevent mixed content in UserProfiles" —
**check all four for helper code that was added for this command and is now
unreferenced**, rather than assuming the blast radius is one file.

### The Py2 `gen_key()` dies here
`ssl_images.py` carries a `gen_key()` that is Python 2-shaped and was scheduled
for a fix by an earlier draft of the plan. It is deleted rather than fixed.
`core/images/upload.py:51`'s `make_key()` — the one the live upload path uses —
was already correct and is untouched: it does
`b64encode(uuid.uuid4().bytes, b'-_').rstrip(b'=').decode('ascii')`, with bytes
altchars and a decode. **These are two separate upload paths and only the
retired one was broken.**

### What the 42 tests were covering that nothing else does
`resize_image()` was found **wholly uncovered** by Step 13 task 07's mutation
testing — 201 tests stayed green with it reverted — so its 42 tests are not
uniformly load-bearing. But `html_check`, `process_post` and `process_html` do
carry real coverage of URL rewriting logic.

**Before deleting, confirm none of that logic has a second caller.** If
`core/download.py`'s `download_file` or `core/functions.py`'s `remove_file` are
left with no callers once the command goes, say so in the write-up — but do not
delete them in this commit without checking the whole tree first.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 15's `ssl_images` paragraphs, and the "not retiring the bucket" note)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 13 task 08, which rebuilt this command's Markdown patterns; Step 13 task
  07, which found `resize_image()` uncovered)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Re-verify the seven counts of evidence before deleting**, rather than
   trusting this task file's table. A dead-code claim that goes unchecked into a
   deletion is the one kind that cannot be walked back cheaply.
2. Delete `core/management/commands/ssl_images.py` and
   `core/tests/management/commands/test_ssl_images.py`.
3. Remove `HOT_LINK_PHOTOS_BASE_URL` and `HOT_LINK_PHOTOS_BUCKET` from
   `sg101/settings/base.py`. **Leave `USER_IMAGES_SOURCES` alone** — it has two
   live consumers.
4. **Check all four touched models** (`bio.UserProfile`, `comments.Comment`,
   `forums.Post`, `news.Story`) for helpers added for this command that are now
   unreferenced. Report what you find; delete only what is provably orphaned.
5. **Check `core/download.py` and `core/functions.py`** for the same. Do not
   delete a shared helper in this commit on the strength of one caller leaving.
6. Do **not** touch the `sg101.forum.photos` bucket, its contents, or any stored
   markup referencing it.
7. Confirm the test count moves **887 → 845** and that the delta is exactly the
   42 removed tests — not 42 removed and something else quietly broken.
8. Suite green, `check` clean, `makemigrations --check` clean, deprecation gate
   green (`tools/deprecation_gate.sh`).

## Dependencies
- Step 14 complete: Django 5.2.17 / Python 3.12.14, 887 tests green
- No task in Step 15 depends on this one having run — but tasks 02 and 04 are
  smaller if it has, since it removes an `S3Bucket` consumer

## Implementation Approach
1. Re-run the evidence sweep first. Grep for `ssl_images` across the whole tree;
   check `CELERY_BEAT_SCHEDULE`, `call_command` sites, `fabfile.py`, Compose, the
   Dockerfile, CI and `tools/`; confirm no log or cache file exists.
2. Ask about production's crontab if it has not already been settled — it is the
   one input the repo cannot supply.
3. Delete the two files, then let the import errors and the test count tell you
   what else referenced them.
4. Remove the two orphaned settings; verify by grep that nothing else reads them.
5. Sweep the four models and the two `core` helpers for orphaned code. Report;
   delete only the provable.
6. Run the suite and confirm the count is exactly 845.
7. Write up what the deletion actually removed, including anything found in step
   5 that was left in place and why.

## Acceptance Criteria

1. **The Evidence Is Re-Verified, Not Inherited**
   - Given the seven counts recorded in the plan
   - When this task begins
   - Then each is re-checked against the tree as it stands today, and any that no
     longer holds is reported before any deletion happens

2. **Command and Tests Removed**
   - Given `ssl_images.py` and `test_ssl_images.py`
   - When both are deleted
   - Then nothing in the tree imports either, and the project starts, checks
     clean, and runs its suite

3. **Test Count Moves By Exactly 42**
   - Given a suite of 887 tests before the deletion
   - When the suite runs after it
   - Then it reports exactly 845 passing, with no errors and no new skips

4. **The Orphaned Settings Go, the Live One Stays**
   - Given `HOT_LINK_PHOTOS_BASE_URL`, `HOT_LINK_PHOTOS_BUCKET` and
     `USER_IMAGES_SOURCES`
   - When the settings module is read after this task
   - Then the first two are gone, `USER_IMAGES_SOURCES` is unchanged, and
     `core/html.py` and `user_photos/forms.py` still resolve it

5. **The Bucket Still Serves**
   - Given 15,690 posts and 16 comments embedding `sg101.forum.photos` URLs
   - When a sample of those posts is rendered after the deletion
   - Then their images still load, because nothing about the bucket or the stored
     markup was touched

6. **Orphan Sweep Reported**
   - Given the four models and the two `core` helpers the command used
   - When the sweep completes
   - Then the write-up names what was found orphaned, what was deleted, and what
     was deliberately left in place with the reason

7. **Gate and Checks Clean**
   - Given the deletion
   - When `tools/deprecation_gate.sh`, `check` and `makemigrations --check` run
   - Then all are clean, and the gate's ignore list is unchanged (this task
     removes code, it does not change dependencies)

## Metadata
- **Complexity**: Low
- **Labels**: Dead Code, Deletion, S3, Management Commands, Step 15
- **Required Skills**: Evidence-based dead-code verification, Django management
  commands and settings, reading a deletion's blast radius before taking it
