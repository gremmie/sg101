# Task: Move the Base Image from Python 3.7 to 3.10

## Description
Bump the Docker base image from `python:3.7` to `python:3.10` with
`Django==3.2.25` held fixed, and bump `bleach` — the one dependency that cannot
survive the move — so the suite comes back green on the new interpreter before
any Django rung starts.

This is the whole interpreter risk, isolated. Nothing else in Step 13 can begin
until it lands: Django 4.0 requires Python 3.8+, so the ladder is blocked on the
frozen 3.7 image.

## Background
**Why 3.10 and not the 3.8 minimum.** 3.10 is the only version that Django 3.2
*and* everything through 5.2 support. That overlap is what lets the interpreter
move alone — bump the image, keep Django where it is, get green — instead of
changing two variables at once. 3.8 would buy a second interpreter move later;
3.12 is not reachable as a solo move at all, because Django 3.2 tops out at 3.10
(support added in 3.2.9, so the current pin already has it).

| Django | Python |
| --- | --- |
| 3.2 | 3.6 – 3.10 |
| 4.0 | 3.8 – 3.10 |
| 4.1 | 3.8 – 3.11 |
| 4.2 | 3.8 – 3.12 |
| 5.2 | 3.10 – 3.13 |

**Measured 2026-08-02, and the plan's prediction was wrong.** Step 14's venv
note called four pins blockers. Every one of them installs unmodified on
`python:3.10`: `Pillow==6.2.2`, `mysqlclient==1.4.6`, `psycopg2==2.9.9` and
`lxml==4.9.4` all build and produce cp310 wheels. The prediction was wrong in
the direction that would have oversized this step.

**Installing is not importing, and that is where the one real breaker lives.**
`bleach==3.1.5` fails to import on 3.10 — `cannot import name 'Mapping' from
'collections'`, the ABC aliases 3.10 finally removed. Every other third-party
package imports clean. The bleach bump deferred since Step 10 is now the gate.

**The bleach bump is far smaller than its pin comment claims.** Both
`requirements.txt:63` and `requirements-docker.txt:50` describe 3.1.5 as "the
last line keeping the styles= kwarg core/html.py passes," which reads as though
a real CSS allowlist is at stake. It is not. `core/html.py`'s `_CLEAN_PROFILES`
has two profiles and **both pass `[]`** as the third element, and neither allows
a `style` attribute in the first place — the kwarg is redundant twice over.
Modern bleach replaced `styles=` with a `css_sanitizer` object and strips all
CSS when none is given, which is already the behavior here. The work is deleting
the kwarg at `core/html.py:53`, deleting the now-empty third tuple element from
both profiles, and updating the two `core/tests/test_html.py` assertions that
name it (lines 95 and 106, inside the `@patch('core.html.bleach.clean')` tests
at lines 88 and 99).

Worth knowing while in there: **bleach was archived upstream in 2023** in favor
of `nh3`. That is not a decision for this task — sanitization is
security-critical and swapping libraries is not an interpreter concern — but it
is the last time anyone will read this code closely for a while, so record what
you learn.

**Three 3.7-specific things in the Dockerfile expire with this change:**
- `FROM python:3.7` and the header comment explaining that `python:3.7` is EOL,
  frozen, Bullseye-based, and may need repointing at `archive.debian.org`. The
  3.10 image is a different Debian base; the whole note needs rewriting rather
  than editing.
- `RUN pip install --upgrade "pip<24.1"` — the cap exists solely because pip
  24.1+ drops Python 3.7. It should go.
- The apt comment claiming lxml and Pillow "now install from manylinux wheels on
  Py3.7, so their C-library -dev headers are no longer needed." **This is the
  trap in this task.** The 2026-08-02 measurement found both build *from sdist*
  on 3.10, which is not the same thing as installing from a wheel. Building
  Pillow from sdist without `libjpeg-dev`/`zlib1g-dev` succeeds and imports
  fine — it simply produces a Pillow with no JPEG support, which fails at
  runtime on the first thumbnail, not at build time. Verify decoded formats
  explicitly; do not infer them from a green `pip install`.

The MySQL apt entries (`default-libmysqlclient-dev`, `default-mysql-client`) and
the `mysqlclient` pin **stay** — see task 06 for why, and do not "clean them up"
in passing here.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 13, "Suggested order" item 1)
- `.agents/planning/2026-07-04-modernizing-sg101/research/upgrade-path.md`
  (the Django/Python support matrix)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Change the base image to `python:3.10` in `Dockerfile`, and rewrite the
   header comment — the 3.7 EOL/Bullseye/`archive.debian.org` note describes an
   image that is no longer in use.
2. Remove the `pip<24.1` cap; it exists only for 3.7.
3. Hold `Django==3.2.25` unchanged in both requirements files. This task changes
   the interpreter and nothing else about the framework.
4. Bump `bleach` to a version that imports on 3.10, and update its pin comment in
   **both** `requirements.txt` and `requirements-docker.txt` — the current
   comment is factually wrong about why the pin exists.
5. Remove `styles=` from the `bleach.clean()` call at `core/html.py:53` and drop
   the now-unused third element from both `_CLEAN_PROFILES` entries.
6. **Verify sanitization behavior did not change**, rather than assuming the
   redundancy argument holds. Existing `core/tests/test_html.py` coverage plus
   the two updated assertions must demonstrate that the same tags, attributes
   and CSS are stripped before and after.
7. **Verify Pillow's compiled format support explicitly** on the new image —
   JPEG at minimum, since thumbnailing is the site's most common image path.
   Add apt build dependencies back if support is missing.
8. Update the CI workflow's stale version references: `.github/workflows/ci.yml`
   line 4 ("Python 3.7 / Django 3.2") and line 29 ("Build the image (Py3.7 /
   Django 3.2)").
9. Record which packages built from sdist versus installed from wheels, and the
   image build time before and after. Later steps need to know which of these
   are slow builds rather than rediscovering it.

## Dependencies
- Step 12 complete (798 tests green on PostgreSQL as of 2026-08-02)
- Compose defaults to PostgreSQL; the `mysql` profile is unaffected by this task
- CI runs `--settings=sg101.settings.docker_test`, not the dev settings

## Implementation Approach
1. Change `FROM` and remove the pip cap; build the image and let it fail. The
   failure list is the real dependency inventory, not the plan's prediction.
2. Bump bleach and make the `core/html.py` change together — the import failure
   and the API change are the same package's problem.
3. Build, then **import every third-party package** rather than trusting the
   install. That distinction is what this task exists to respect.
4. Verify Pillow's format support and lxml's parser before running the suite.
5. Run the full suite with `--settings=sg101.settings.docker_test`, plus
   `check` and `makemigrations --check`.
6. Smoke the site — with particular attention to anything that renders
   user-submitted markup (`clean_html` is on that path) and anything that
   generates a thumbnail.

## Acceptance Criteria

1. **The Image Builds on 3.10**
   - Given the updated `Dockerfile`
   - When the image is built from scratch with no layer cache
   - Then it completes, and `python --version` inside it reports 3.10

2. **Every Dependency Imports**
   - Given the built image
   - When each third-party package in `requirements-docker.txt` is imported
   - Then all imports succeed, including bleach

3. **Django Is Unchanged**
   - Given the completed task
   - When `requirements.txt` and `requirements-docker.txt` are inspected
   - Then `Django==3.2.25` is untouched, and no Django-version-driven code
     change is included in this task

4. **Sanitization Behavior Is Preserved**
   - Given the `styles=` kwarg removal and the bleach bump
   - When markup exercising both `_CLEAN_PROFILES` profiles is sanitized
   - Then the same tags, attributes and inline CSS are stripped as before the
     bump, demonstrated by test assertions rather than inspection

5. **Pillow Can Decode JPEG**
   - Given the new image
   - When a JPEG is opened and thumbnailed through the site's own image path
   - Then it succeeds — proving the sdist build linked against libjpeg rather
     than silently dropping the codec

6. **Suite Green on the New Interpreter**
   - Given the 3.10 image
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all 798 tests pass, and `check` and `makemigrations --check` are clean

7. **CI Green**
   - Given the pushed branch
   - When the GitHub Actions workflow runs
   - Then it builds the 3.10 image and the suite passes, with no stale "Py3.7"
     text left in the workflow

8. **Stale Comments Corrected**
   - Given the completed task
   - When the `Dockerfile` header, the pip cap, the apt/wheel note, and both
     bleach pin comments are reviewed
   - Then each either describes the 3.10 reality or is gone, with no comment
     left asserting something the build no longer does

## Metadata
- **Complexity**: Medium
- **Labels**: Python 3.10, Docker, Dependencies, bleach, Interpreter, Step 13
- **Required Skills**: Docker image builds, Python packaging and C-extension
  builds, HTML sanitization
