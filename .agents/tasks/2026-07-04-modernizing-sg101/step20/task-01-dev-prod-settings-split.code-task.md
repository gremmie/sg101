# Task: Split the Dev and Prod Images and Settings

## Description
Give the project a production image and a production settings module that are
actually distinct from the development ones, and fix the database backend both
settings modules still declare. This is the first task of Step 20 because every
task after it configures a production settings module that does not yet exist in
usable form.

## Background
**Carried in 2026-08-07 from Step 13 task 06, and unresolved since.**
`research/docker-strategy.md` records both *"the dev override owns the debug
toolbar"* and *"one image runs dev and prod"*, and those cannot both hold: one
image means the production image either carries `django-debug-toolbar` or it does
not.

**Three things are measurably wrong today:**

- `sg101/settings/production.py:14` and `sg101/settings/local.py:11` both declare
  `django.db.backends.mysql`, five steps after the PostgreSQL move.
  `sg101/settings/databases.py` already provides `from_env()` and is not used by
  either.
- The `if DEBUG and find_spec(...)` guard around the debug toolbar protects
  nothing in production, because `production.py` never goes through `local.py`.
- `Dockerfile` is a single stage ending in
  `CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]`, so there is no
  production image to speak of.

**The toolbar's MIDDLEWARE position is deliberate.** It sits after
`CommonMiddleware`, that placement was measured, and the reason is commented in
place. It must survive this change.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/docker-strategy.md` —
  the two contradictory claims this task resolves
- `sg101/settings/databases.py` — the `from_env()` mechanism that already exists

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Convert `Dockerfile` to a multi-target build: a `prod` target installing from
   `requirements.txt`, and a `dev` target layering `requirements_dev.txt` on top
   of it.
2. Point `production.py` at `databases.from_env()` rather than a hardcoded
   engine. Do the same for `local.py`.
3. Move the debug toolbar into a development-only settings module, and drop the
   `if DEBUG and find_spec(...)` guard entirely once the toolbar cannot reach
   production.
4. Preserve the toolbar's MIDDLEWARE position after `CommonMiddleware`, with its
   explanatory comment intact.
5. Point `docker-compose.yml` at the `dev` target so the development workflow is
   unchanged.

## Dependencies
- `sg101/settings/databases.py`, already present and tested
- `requirements.txt` / `requirements_dev.txt`, already split
- The existing test suite as the regression gate

## Implementation Approach
1. Read the current `Dockerfile` and settings modules, and record what each
   actually does before changing anything.
2. Split the Dockerfile into `prod` and `dev` targets, `dev` built `FROM prod`.
3. Rewire both settings modules onto `from_env()`, and verify against a running
   container rather than by reading.
4. Move the toolbar to the dev settings module and remove the dead guard.
5. Run the full suite; it is the gate, not a smoke script.

## Acceptance Criteria

1. **The prod image does not carry development tooling**
   - Given the image built at the `prod` target
   - When its installed packages are listed
   - Then `django-debug-toolbar` is absent

2. **The dev image is unchanged in behavior**
   - Given the image built at the `dev` target and the existing compose file
   - When the development stack is started
   - Then the debug toolbar renders as it does today

3. **Production settings read the database from the environment**
   - Given `DB_ENGINE=postgresql` and production settings
   - When `DATABASES` is read
   - Then the backend is `django.db.backends.postgresql` and no MySQL engine
     string remains in `production.py` or `local.py`

4. **The toolbar's middleware position is preserved**
   - Given the development settings module
   - When `MIDDLEWARE` is inspected
   - Then the toolbar still sits immediately after `CommonMiddleware`, with its
     comment

5. **The suite stays green**
   - Given the full test suite
   - When it is run against both settings modules
   - Then it passes, with new tests covering the settings split itself

## Metadata
- **Complexity**: Medium
- **Labels**: Docker, Settings, Configuration, Production Hardening
- **Required Skills**: Docker multi-stage builds, Django settings layout
