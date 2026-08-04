# Task: Bump Pillow and Replace Image.ANTIALIAS

## Description
Move `Pillow` off the 9.5.0 pin and replace `Image.ANTIALIAS`, which Pillow 10
removed, with `Image.Resampling.LANCZOS` across the seven non-test call sites
and the six test assertions that name it.

This is a latent break with a wide blast radius: nothing fails until Pillow
crosses 10, and then **thumbnailing breaks everywhere at once** — avatars,
uploaded photos, the photo of the day, and the SSL image migration command.

## Description of scope
**Starting point updated 2026-08-03: this task begins at `Pillow==9.5.0`, not
6.2.2.** Task 01 had to move Pillow after all. 6.2.2 installed on 3.10 and
imported on 3.10, then **aborted the interpreter at shutdown** — `free():
invalid pointer`, exit 134, on both arm64 and amd64 — so any process that
imports PIL and returns died on a signal. 9.5.0 is quiet, ships a cp310 wheel,
and **still has `Image.ANTIALIAS`**, which is what keeps this task separate: the
constant's removal is a Pillow 10 concern and 9.5.0 stops one version short of
it.

So the split still holds, just from a new baseline. The interpreter needed a
Pillow that does not abort; this task needs a Pillow past 10, which is where
`ANTIALIAS` goes away. A thumbnail regression here is attributable to the
resampling change rather than to the interpreter.

**One consequence worth expecting:** on 9.5.0 every one of the seven call sites
now emits `DeprecationWarning: ANTIALIAS is deprecated and will be removed in
Pillow 10`. That noise is the work of this task made visible, not a new defect.

## Background
**The call sites, verified 2026-08-03.** The plan counts seven; there are seven
non-test sites **and six more in tests** that the plan does not mention:

Non-test (7):
- `core/images/upload.py:96`, `:104`, `:138`, `:146` — four `thumbnail()` calls
- `core/images/utils.py:42` — `resize()`
- `core/management/commands/ssl_images.py:101` — `thumbnail()`
- `potd/models.py:25` — `resize()`

Tests (6):
- `core/tests/images/test_upload.py:43`, `:46`, `:110`, `:113`
- `core/tests/images/test_utils.py:43`, `:51`

**The test sites are the reason this is not a blind find-and-replace.** Four of
them assert against `image_mock.ANTIALIAS` — a `Mock` attribute, which exists
whatever it is called. A mock will happily return an attribute named `ANTIALIAS`
long after the real Pillow has removed it, so **these tests cannot fail on this
bug**. They will keep passing against a Pillow that no longer has the constant,
and the first real signal will be a broken thumbnail in production.

That makes this task's real deliverable a test that would actually catch the
regression, not just the constant swap. Consider whether the image tests should
exercise a real `PIL.Image` for at least one path rather than mocking the
library wholesale.

**`Image.Resampling.LANCZOS` is the replacement**, and `ANTIALIAS` was an alias
for `LANCZOS` all along, so the resampling filter itself does not change. What
changes is the constant's home: `Image.Resampling` is an enum added in Pillow
9.1. Check the floor — if the chosen Pillow version predates 9.1, the enum is
not there.

**Verify what else changed between 9.5.0 and the target.** This project's image
handling includes EXIF-sensitive upload paths and a management command that
rewrites images. The bump is not just the one constant.

**Interaction with task 01.** Task 01 landed on `Pillow==9.5.0` from a wheel and
did **not** need to add `libjpeg-dev` back. If the target version has a cp310
wheel this stays true; if it ever falls back to an sdist build, the Dockerfile
comment names the check (`features.check('jpg')`). Do not assume in either
direction.

### The `.format` trap living on these exact lines

Brian raised JPEG and PNG as formats that have caused trouble here before, which
turned up something the ANTIALIAS swap sits directly on top of. **Verified on
9.5.0, 2026-08-03.**

`Image.format` is only populated on an image *opened from a file*. `thumbnail()`
mutates in place and keeps it; **`crop()` and `resize()` return new objects, and
those come back with `.format = None`**:

```
opened       format= PNG
after crop   format= None
after resize format= None
```

So `image.save(f, format=image.format)` succeeds after `thumbnail()` and raises
after `resize()`. It presents as "PNG uploads broke, JPEGs were fine" — or the
reverse — depending purely on which helper the path went through, which is what
makes it hard to place.

**Both `resize()`/`crop()` callers already work around it, and neither says so:**

- `potd/models.py:66` captures `format = image.format` on the line *before*
  `scale_image()` (line 67, a `resize()`), then saves with the captured value.
- `bio/forms.py:98` stashes `self.file_type = self.image.format` at parse time
  and saves with that at line 122, after `downscale_image_square()` — which is
  `core/images/utils.py`'s `crop()` + `resize()`.

Two correct orderings, one line apart, held in place by nothing but the author's
memory. The ANTIALIAS edits land on `potd/models.py:25` and
`core/images/utils.py:42` — inside that blast radius. **Do not reorder or
"simplify" those captures**, and leave a comment at both sites naming why the
capture precedes the scale, so the next reader does not tidy it away.

This also sharpens the test argument above: the existing image tests mock PIL
wholesale, so a `.format` regression is exactly as invisible to them as the
ANTIALIAS removal is. **A real-`PIL.Image` round-trip of a PNG specifically
catches both** — PNG because it is the format whose save is most likely to be
attempted with a `None` format, and because RGBA is the mode that fails loudest
if anything downstream tries to write it as JPEG.

**For reference, what 9.5.0 actually supports** (round-tripped, not read off a
feature flag): JPEG (RGB), PNG (RGBA, with alpha), GIF (palette) and WebP all
save, reopen and thumbnail cleanly; `jpg`, `zlib`, `libtiff`, `jpg_2000`, `webp`
and `freetype2` all report available. Re-run that check against the target
version rather than assuming it carries forward.

### `thumbnail()` output already moved once, silently — measure, don't hash

**The 6.2.2 → 9.5.0 jump task 01 made changed thumbnail pixels, and nothing
caught it.** Measured 2026-08-03 by diffing the whole used PIL surface across
both versions against a byte-identical fixture:

| Size | max channel Δ | mean Δ | pixels differing |
|---|---|---|---|
| 120×120 | 25/255 | 0.74 | 23.3% |
| 64×64 | 9/255 | 0.63 | 33.3% |
| 32×32 | 7/255 | 0.63 | 49.7% |

Sub-perceptual, and the fixture was deliberately harsh (high-frequency pixel
noise; real photographs drift less). **`resize()` was byte-identical** — only
`thumbnail()` moved, which is `core/images/upload.py:96,104,138,146` and
`ssl_images.py:101`.

**Two causes, not one.** `reducing_gap` — added in Pillow 7.0, doing a
`reduce()` pre-pass — accounts for 64×64 and 32×32, where passing
`reducing_gap=None` changes the hash back. It does **not** account for 120×120,
where the default and `reducing_gap=None` agree with each other and both differ
from 6.2.2. Something else in the resize path moved as well; if this task's
target version shifts output again, do not assume `reducing_gap` explains it.

**This is why AC4 asks for a tolerance rather than a hash.** The
ANTIALIAS→LANCZOS rename genuinely cannot move a pixel — `Image.ANTIALIAS` *is*
`Resampling.LANCZOS`, both value 1 — but crossing versions can, and a
hash-equality check will fail for reasons that do not matter while telling you
nothing about whether the result still looks right.

**Everything else in the used surface was verified unchanged** across that same
jump, so this task does not need to re-litigate it: `_getexif()` still present
and returning the orientation tag (`orient_image` works), all four `transpose()`
constants byte-identical, `ImageFile.Parser` identical including `.format`
preservation, JPEG re-save bytes identical, `MAX_IMAGE_PIXELS` unchanged, and
truncated-file rejection identical. `Image.open()` now raises
`UnidentifiedImageError` on garbage instead of bare `OSError`, but it subclasses
`OSError` and `bio/forms.py:94` catches `IOError`, so it is still caught —
worth knowing only because narrowing that `except` clause would break it.

**Not covered by that measurement**, and worth adding here if the target version
is a large jump: real EXIF-heavy camera files (the fixture carried one tag), ICC
profile preservation, animated GIFs, and the S3 upload path end to end.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 13, the Pillow paragraphs -- read the 2026-08-03 CORRECTION first,
  which supersedes the "decoupled from the interpreter" claim above it)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump `Pillow` in both `requirements.txt` and `requirements-docker.txt`, past
   10 so the removal is actually crossed rather than deferred again.
2. Replace `Image.ANTIALIAS` with `Image.Resampling.LANCZOS` at all seven
   non-test call sites.
3. Update the six test assertions — and **fix the fact that four of them assert
   against a mock attribute and therefore cannot detect this class of bug.** At
   least one image path must be exercised against a real `PIL.Image`, and the
   round-trip must include **a PNG**, not only a JPEG.
4. **Preserve the `.format` capture ordering at `potd/models.py:66` and
   `bio/forms.py:98`**, and add a comment at each naming why the capture has to
   precede the scale. `crop()`/`resize()` return new objects with
   `.format = None`; these two lines are the only thing keeping PNG and JPEG
   thumbnails saving correctly, and the ANTIALIAS edits land beside them.
5. Verify the resampling output **perceptually, not by hash**. The rename itself
   cannot change pixels — `ANTIALIAS` is `Resampling.LANCZOS`, same value 1 —
   but a version jump can and already has (see the measurement below). Compare
   with a stated tolerance on channel delta, and treat a byte difference as
   something to quantify rather than as a failure.
6. Review the 9.5.0 → target changelog for anything else touching this project's
   paths — EXIF handling, `thumbnail()` semantics, format support, and the
   image-validation path in `core/images/`.
7. Confirm decoded format support on the built image -- JPEG and PNG at minimum.
   This is the same trap task 01 flags: a Pillow built without the codec imports
   fine and fails at runtime.
8. Revisit the Dockerfile's image-library apt entries in light of whatever task
   01 left them as.

## Dependencies
- Task 01 (Python 3.10) — this can run any time after it; it does not depend on
  the Django rungs
- The site's image paths: avatars, user photos, photo of the day

## Implementation Approach
1. Write the failing test first. Before bumping anything, establish a test that
   exercises a real `PIL.Image` through one of the site's thumbnail paths and
   would fail if `ANTIALIAS` vanished. Confirm it passes on 9.5.0.
2. Bump Pillow and watch that test fail. **A regression test that has not been
   seen to fail against the bug proves nothing** — the Step 12 lesson applies
   directly here, where a test written for a template comment passed against the
   broken template.
3. Swap the constant at all seven sites; watch the test go green.
4. Update the six mock-based assertions.
5. Read the changelog and check the non-obvious paths: `ssl_images` (a
   management command that rewrites images in place) and `core/images/upload.py`
   (EXIF and orientation).
6. Smoke: upload an avatar, upload a user photo, set a photo of the day, and
   compare rendered thumbnails against pre-bump output.

## Acceptance Criteria

1. **Pillow Past 10**
   - Given the updated requirements
   - When Pillow's version is read in the built image
   - Then it is past 10, so the `ANTIALIAS` removal is actually crossed

2. **No ANTIALIAS Remains**
   - Given the completed task
   - When the tree is searched for `ANTIALIAS`
   - Then there are no matches in application or test code

3. **A Test Actually Catches the Regression**
   - Given a test exercising a real `PIL.Image` through a site thumbnail path
   - When `Image.Resampling.LANCZOS` is reverted to `Image.ANTIALIAS`
   - Then that test fails — demonstrating the coverage gap the six mock-based
     assertions leave open

4. **Thumbnails Are Perceptually Unchanged, Measured Not Assumed**
   - Given the same source image before and after the bump
   - When a thumbnail is generated through each of the four upload paths, the
     `potd` path and the `utils` resize
   - Then the per-channel difference against pre-bump output stays within a
     stated tolerance — **max channel delta ≤ 25/255 and mean ≤ 1.0 is the
     band the 6.2.2 → 9.5.0 jump already produced**, so anything inside it is
     resampling drift and anything beyond it is a real regression to explain.
     A hash comparison is the wrong instrument here and will fail for reasons
     that do not matter

5. **Uploads Still Work End to End, for PNG as Well as JPEG**
   - Given the running site
   - When an avatar and a user photo are uploaded — a JPEG with EXIF
     orientation, and an RGBA PNG
   - Then all are accepted, oriented and thumbnailed correctly, with the PNG
     retaining its alpha channel rather than being flattened or rejected

6. **The `.format` Capture Still Guards the Save**
   - Given `potd/models.py` and `bio/forms.py` after the ANTIALIAS edits
   - When a PNG is pushed through the photo-of-the-day thumbnail path and the
     avatar downscale path
   - Then both save successfully, and a test fails if either capture is moved
     after its `resize()`/`crop()` — proving the ordering is covered rather than
     merely preserved by luck

7. **Both Capture Sites Are Commented**
   - Given the two `.format` captures
   - When each is read
   - Then a comment states that `crop()`/`resize()` return new images with
     `.format = None`, so a later reader cannot tidy the ordering away without
     seeing the consequence

8. **JPEG and PNG Support Confirmed**
   - Given the built image
   - When a JPEG and a PNG are opened through the site's own path
   - Then both decode — proving the build linked the codecs rather than silently
     dropping them

9. **Changelog Reviewed**
   - Given the span from 9.5.0 to the target version
   - When the changelog is reviewed against this project's image paths
   - Then any other relevant change is either addressed or recorded as
     considered and dismissed

10. **Suite Green**
   - Given the bumped Pillow
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass and `check` is clean

## Metadata
- **Complexity**: Medium
- **Labels**: Pillow, Images, Dependencies, Test Coverage, Step 13
- **Required Skills**: Pillow/PIL APIs, image processing, writing tests that
  fail against the bug before trusting them
