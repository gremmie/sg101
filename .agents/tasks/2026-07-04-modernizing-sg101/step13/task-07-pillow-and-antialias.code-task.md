# Task: Bump Pillow and Replace Image.ANTIALIAS

## Description
Move `Pillow` off the 6.2.2 pin and replace `Image.ANTIALIAS`, which Pillow 10
removed, with `Image.Resampling.LANCZOS` across the seven non-test call sites
and the six test assertions that name it.

This is a latent break with a wide blast radius: nothing fails until Pillow
crosses 10, and then **thumbnailing breaks everywhere at once** — avatars,
uploaded photos, the photo of the day, and the SSL image migration command.

## Description of scope
**This is deliberately not part of the interpreter move.** The plan originally
assumed `Pillow==6.2.2` would not build on Python 3.10 and would therefore be
forced along with the base image. The 2026-08-02 measurement disproved that: it
builds and produces a cp310 wheel. So Pillow is decoupled, and it should be
bumped on its own evidence rather than smuggled into task 01 where a thumbnail
regression would be attributed to the interpreter.

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

**Verify what else changed between 6.2.2 and the target.** That is a large span
— roughly six years of releases — and this project's image handling includes
EXIF-sensitive upload paths and a management command that rewrites images. The
bump is not just the one constant.

**Interaction with task 01.** If task 01 had to add back `libjpeg-dev` and
friends to build Pillow from sdist, this task may be able to drop them again if
the target version ships manylinux wheels for cp310. Check; do not assume in
either direction.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 13, "The Pillow bump is now decoupled from the interpreter")

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump `Pillow` in both `requirements.txt` and `requirements-docker.txt`, past
   10 so the removal is actually crossed rather than deferred again.
2. Replace `Image.ANTIALIAS` with `Image.Resampling.LANCZOS` at all seven
   non-test call sites.
3. Update the six test assertions — and **fix the fact that four of them assert
   against a mock attribute and therefore cannot detect this class of bug.** At
   least one image path must be exercised against a real `PIL.Image`.
4. Verify the resampling output is unchanged. `ANTIALIAS` aliased `LANCZOS`, so
   thumbnails should be byte-identical or near it; a visible difference means
   something other than the rename happened.
5. Review the 6.2.2 → target changelog for anything else touching this project's
   paths — EXIF handling, `thumbnail()` semantics, format support, and the
   image-validation path in `core/images/`.
6. Confirm decoded format support on the built image, especially JPEG. This is
   the same trap task 01 flags: a Pillow built without the codec imports fine
   and fails at runtime.
7. Revisit the Dockerfile's image-library apt entries in light of whatever task
   01 left them as.

## Dependencies
- Task 01 (Python 3.10) — this can run any time after it; it does not depend on
  the Django rungs
- The site's image paths: avatars, user photos, photo of the day

## Implementation Approach
1. Write the failing test first. Before bumping anything, establish a test that
   exercises a real `PIL.Image` through one of the site's thumbnail paths and
   would fail if `ANTIALIAS` vanished. Confirm it passes on 6.2.2.
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

4. **Thumbnails Are Visually Unchanged**
   - Given the same source image before and after the bump
   - When a thumbnail is generated through each of the four upload paths, the
     `potd` path and the `utils` resize
   - Then output matches pre-bump output, since `ANTIALIAS` aliased `LANCZOS`

5. **Uploads Still Work End to End**
   - Given the running site
   - When an avatar and a user photo are uploaded, including a JPEG with EXIF
     orientation
   - Then both are accepted, oriented and thumbnailed correctly

6. **JPEG Support Confirmed**
   - Given the built image
   - When a JPEG is opened through the site's own path
   - Then it decodes — proving the build linked the codec rather than silently
     dropping it

7. **Changelog Reviewed**
   - Given the span from 6.2.2 to the target version
   - When the changelog is reviewed against this project's image paths
   - Then any other relevant change is either addressed or recorded as
     considered and dismissed

8. **Suite Green**
   - Given the bumped Pillow
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass and `check` is clean

## Metadata
- **Complexity**: Medium
- **Labels**: Pillow, Images, Dependencies, Test Coverage, Step 13
- **Required Skills**: Pillow/PIL APIs, image processing, writing tests that
  fail against the bug before trusting them
