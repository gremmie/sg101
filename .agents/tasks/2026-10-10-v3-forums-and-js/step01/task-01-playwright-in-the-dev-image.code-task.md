# Task: Playwright in the dev image

## Description
Install Playwright for Python and its headless Chromium shell into the
Dockerfile's `dev` target, so the test suite, locally and in CI, can drive a
real browser. The `prod` target, and so leopard's image, must not change at all.

## Background
The V3 forums and JavaScript project adds a small set of browser tests for the
paths that fail silently (R15): a Foundation modal that never opens, an upload
reason that never arrives, a quick reply that never appends. All of them need a
browser in the image the suite runs in.

The Dockerfile has two targets. `prod` is what leopard runs. `dev` is built
`FROM prod AS dev`, switches back to `USER root` on purpose (the comment there
explains why), and runs `pip install -r requirements_dev.txt`. Both
`docker-compose.yml` and CI's `docker compose build web` build `dev`. A
separate CI step builds `--target prod` to check its UID. Everything this task
adds belongs after the `dev` target's `USER root`, which is where `--with-deps`
can run `apt-get`.

Research topic 3 measured, in throwaway containers from the dev image:
- `pip install playwright`: 1.63.0, 3 s, 136 MB
- `playwright install --with-deps --only-shell chromium`: 269 MB (headless
  shell and ffmpeg), plus the Debian packages `--with-deps` pulls
- the dev image was 2.21 GB before

Those were measured in a container, not in a Dockerfile build. This task
records the real before and after.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§7.2)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/playwright.md (install cost, `--only-shell`, architectures)
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 1)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Add `playwright`, pinned to an exact version, to `requirements_dev.txt`,
   with a short comment in that file's style saying what it is for. Never add
   it to `requirements.txt`.
2. In the Dockerfile's `dev` target, after `pip install -r
   requirements_dev.txt`, run `playwright install --with-deps --only-shell
   chromium`. The browser must land somewhere the container user can read at
   run time. Check where Playwright puts it (`PLAYWRIGHT_BROWSERS_PATH`, or the
   default under the installing user's home), and confirm it still resolves
   when Compose bind-mounts the checkout over `/app`.
3. Keep the `dev` target's comments accurate. Its "this resolves to the three
   tools it adds" line will become stale.
4. The `prod` target must be untouched: no Dockerfile line above `FROM prod AS
   dev` changes, `requirements.txt` is identical, and `playwright` cannot be
   imported in an image built with `--target prod`.
5. Record, for the dev image before and after: its size (`docker image ls`)
   and its build time without cache. Also record the `prod` image's size
   before and after, which must match. These numbers go in the task's notes
   for Brian, not in code comments.

## Dependencies
- Docker Desktop on the Mac (aarch64). CI's `ubuntu-latest` runner is x86-64,
  and Playwright ships Chromium for both, but only aarch64 has been tried.
- Network access during the build, to download the browser.

## Implementation Approach
1. Before changing anything, measure: build `dev` and `prod` with
   `--no-cache`, timing each, and record their sizes.
2. Make the requirement and Dockerfile changes.
3. Rebuild both and measure again.
4. Smoke-check in the dev container that a headless Chromium launches and
   loads a page, e.g. `python -c` with `sync_playwright()` against
   `about:blank` or a `data:` URL. This proves the shell and its system
   libraries are present. It isn't a test, so don't commit it.
5. Run the full suite and the deprecation gate (AGENTS.md) to show nothing
   else moved.

## Acceptance Criteria

1. **Chromium launches in the dev image**
   - Given an image built from the `dev` target
   - When a script in it starts `sync_playwright()` and launches headless Chromium
   - Then a page loads without errors about missing executables or shared libraries

2. **The prod image is unchanged**
   - Given images built with `--target prod` before and after the change
   - When their sizes and `requirements.txt` are compared, and `python -c "import playwright"` runs in the new one
   - Then the sizes match, the file is identical, and the import fails with `ModuleNotFoundError`

3. **Works under the bind mount**
   - Given `docker compose up -d`, which mounts the checkout over `/app`
   - When Chromium is launched via `docker compose exec web`
   - Then it is found and launches, so the browser is not stored under the mounted path

4. **Costs recorded**
   - Given the before and after builds
   - When the task is handed to Brian for review
   - Then the dev image's size and build time, before and after, and the prod image's size, are reported with the commands that measured them

5. **Suite and gate still pass**
   - Given the rebuilt dev image
   - When the suite runs, and then the deprecation gate runs as its own pass
   - Then both pass, with the same test count as before

## Metadata
- **Complexity**: Low
- **Labels**: Docker, Playwright, test infrastructure, CI
- **Required Skills**: Dockerfile multi-stage builds, pip, Playwright install
