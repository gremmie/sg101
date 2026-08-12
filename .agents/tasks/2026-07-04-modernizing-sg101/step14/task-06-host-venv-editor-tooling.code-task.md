# Task: Host venv for Editor Tooling

## Description
Create a host-side `.venv` matching the image's interpreter and dependencies, so
an editor language server can resolve the project's imports. This is the "also
unlocks" the plan attaches to Step 14, and it is the first point in the project
where it is actually achievable.

**This task changes no application code.** It cannot break the site, the suite,
or CI. That makes it the safest task in the step, and also the one to cut first
if the step needs trimming.

## Background
**The problem.** Everything has run in Docker since Step 1, and on Python 3.7
there was no host interpreter that could install the pins at all. So there is no
venv on the host, and pyright (via ALE) cannot resolve a single third-party
import — every `django`, `celery` and `PIL` import is flagged, which makes the
real diagnostics unfindable in the noise.

**It was attempted on 2026-07-31 and abandoned** on the belief that four pins
would not build on a modern Python: `mysqlclient`, `Pillow==6.2.2`,
`lxml==4.9.4`, `psycopg2==2.9.9`. **That belief was measured wrong on
2026-08-02**, and the situation has improved twice since:

- `Pillow` is now **12.3.0**, which ships manylinux and macOS wheels. The source
  build that would have needed `libjpeg` on the host is gone entirely — this is
  why the plan says to do the venv *after* Step 13's task 07, and that task is
  done.
- Step 13 task 06 moved `psycopg2` to 2.9.12 and the celery stack to the current
  line, so the pin set is modern rather than frozen.

**The caveat that still applies, and it is the reason this is not a five-minute
job.** *Builds from sdist is not installs from a wheel.* The 2026-08-02
measurement — and the 3.12 measurement in task 01 — both ran **inside the
image**, where the Dockerfile's apt packages supply the headers. A host venv has
whatever the host has, and this host has neither:

```
mysql_config    not found
pg_config       not found
```

Homebrew is available at `/opt/homebrew/bin/brew`, so both are obtainable —
`mysql-client` and `libpq` respectively — but that is a choice to make
deliberately rather than a yak to shave by reflex.

**`mysqlclient` is the one import that can be left unresolved.** The plan
originally offered "or drop that pin," and Step 13 settled it the other way: the
pin stays, because `tools/pgloader/verify.py` and `verify_data.py` need
`MySQLdb` to verify the production cutover. But **nothing in the application
imports it** — only those two tools — so a venv without it resolves every import
in every file except two, both of which are throwaway migration tooling. That is
the cheap path. The expensive path is `brew install mysql-client` and putting
`mysql_config` on `PATH`. Either is defensible; pick one and record it.

**Match the image's interpreter exactly.** The host default is currently
**Python 3.14.2** via asdf, and the image after task 01 is **3.12**. A venv on
3.14 would type-check against a different standard library than the one the code
runs on — which is precisely the class of mismatch this project has spent Steps
8, 13 and 14 eliminating. Install 3.12 through asdf and build the venv on that.

**`django-stubs` is not optional.** Without it pyright flags every
`Model.objects` and every field access, because both are runtime-generated
descriptors rather than declared attributes — so the language server would still
be useless despite the venv resolving imports. It needs a `mypy`/pyright
configuration stanza naming the settings module to do its best work.

**Naming it `.venv` in the repo root is what makes ALE find it with no
configuration**, which is the whole point. That name then has to be kept out of
two places:

- **`.gitignore`** — currently has `.env` at line 15 but no `.venv`. These are
  different entries; adding one does not cover the other.
- **`.dockerignore`** — currently lists `.git`, `.agents`, `__pycache__` and
  friends but no `.venv`. This one matters more than it looks: the repo root is
  bind-mounted into the container at `/app`, and the `COPY . /app` layer would
  otherwise pull a host-built venv — with host-architecture binary wheels —
  into the image.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 14, "Also unlocks — a local venv for editor tooling," and the two
  corrections beneath it)
- `DOCKER.md` (what the image installs, and why the container remains the place
  work actually runs)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Install **Python 3.12** on the host (asdf) to match the image after task 01,
   and create `.venv` in the repo root from it.
2. Install the project's dependencies into it from `requirements_dev.txt`, plus
   `django-stubs`.
3. **Decide and record how `mysqlclient` is handled** — either install
   `mysql-client` via Homebrew so it builds, or omit it and accept two
   unresolved `MySQLdb` imports in `tools/pgloader/`. Do the same for
   `psycopg2`/`libpq` if it does not install from a wheel on this host.
4. Add `.venv` to **both** `.gitignore` and `.dockerignore`.
5. Configure `django-stubs` so pyright resolves `Model.objects` and field
   attributes, naming the settings module it should load.
6. **Verify the venv is inert with respect to everything else**: the image still
   builds, the suite still runs in the container, and the `.:/app` bind mount
   does not carry `.venv` in.
7. Document the setup — how to recreate it, what it is for, and **that it is not
   where the code runs**. The container remains the execution environment; this
   venv exists so an editor can read the code.
8. Record which packages installed from wheels on the host versus needing a
   source build, since that is the thing the July attempt got wrong.

## Dependencies
- Task 01 (Python 3.12 image) — the venv should match it
- Step 13 task 07 (Pillow 12.3.0), which removed the source build that blocked
  the July attempt
- Ideally task 05, so the venv is built against the final pin set rather than
  one that is about to change

## Implementation Approach
1. Install 3.12 via asdf and create `.venv`.
2. Install `requirements_dev.txt` and see what actually fails on this host,
   rather than pre-emptively brew-installing headers.
3. Resolve or accept each failure, recording the choice.
4. Add `django-stubs` and configure it.
5. Add the two ignore entries, then **prove the `.dockerignore` entry works** by
   rebuilding the image and confirming `.venv` is absent from it.
6. Open a few representative files in the editor — a model, a view, a settings
   module, a management command — and confirm the diagnostics are real ones
   rather than unresolved-import noise.

## Acceptance Criteria

1. **The venv Exists and Matches the Image**
   - Given the host
   - When `.venv/bin/python --version` is run
   - Then it reports **3.12**, matching the image rather than the host default

2. **Imports Resolve in the Editor**
   - Given the configured language server
   - When a module importing Django, Celery, PIL and the site's own apps is
     opened
   - Then no unresolved-import diagnostics are reported, except any deliberately
     accepted and recorded in requirement 3

3. **Model Attributes Resolve**
   - Given `django-stubs` installed and configured
   - When a file using `Model.objects` and field attributes is opened
   - Then neither is flagged as unknown

4. **The venv Is Ignored by git and Docker**
   - Given `.venv` in the repo root
   - When `git status` is run and the image is rebuilt
   - Then `.venv` appears in neither — and the Docker half is verified by
     inspecting the built image, not by reading `.dockerignore`

5. **The Container Is Unaffected**
   - Given the new `.venv`
   - When the image is built and the suite runs in the container
   - Then both behave exactly as before this task

6. **The Setup Is Documented and Honest About Its Role**
   - Given the completed task
   - When the documentation is read
   - Then it says how to recreate the venv, how `mysqlclient` was handled and
     why, and states plainly that the container is still where code runs

## Metadata
- **Complexity**: Low
- **Labels**: Developer Tooling, venv, pyright, django-stubs, Step 14
- **Required Skills**: Python virtual environments and packaging on macOS,
  language-server configuration, Docker build context

