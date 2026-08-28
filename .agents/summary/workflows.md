# Workflows

**Generated 2026-08-27.**

## Local development

The stack is Docker Compose. Services: `postgres` (16), `redis`, `web`,
`worker`, `beat`, and `db` (mysql:5.7) which is **profile-gated behind
`--profile mysql`** and exists only for snapshot conversion and verification
against the pre-migration database.

```
docker compose up -d
docker compose exec web python manage.py migrate
```

`.env` is git-ignored and loaded via Compose's `env_file:`. Seed it from the
committed `.env.example`, which carries working defaults — including
Cloudflare's public Turnstile test keys, so a fresh checkout has working forms
with no account anywhere.

## Testing — two runs, not one

```
docker compose exec web python manage.py test --settings=sg101.settings.docker_test
```

**The deprecation gate is a separate run**, and it is what has caught every
Django removal on this project a version before it landed:

```
docker compose run --rm -e PYTHONWARNINGS="$(tools/deprecation_gate.sh)" web \
    python manage.py test --noinput --settings=sg101.settings.docker_test
```

`tools/deprecation_gate.sh` **only prints the filter**. Running the script and
seeing exit 0 is not the gate passing — the gate is the suite run with that
filter applied. The script exists so CI and a developer use one list; a second
copy typed into the workflow would rot silently.

**`PYTHONWARNINGS` rather than `-W`, deliberately:** `-W` does not reach
subprocesses, and `core/tests/test_settings.py` runs assertions through a
subprocess helper that would otherwise sit outside the gate.

## Writing tests — two things that will bite

**Logging is disabled wholesale in the test settings.** `assertLogs` sees nothing
until you re-enable it, and the failure presents as a missing log line that is
not missing:

```python
old_disable = logging.getLogger().manager.disable
logging.disable(logging.NOTSET)
self.addCleanup(logging.disable, old_disable)
```

`contact/tests/test_views.py` and `antispam/tests/test_turnstile.py` both do
this.

**`CELERY_TASK_ALWAYS_EAGER` hides worker faults by construction.** A broken
deferred task passes the suite and fails in a browser. This has happened; see
Step 16 task 05 in `STATUS.md`.

## CI

`.github/workflows/ci.yml`, on push and PR to **`modernize` only**. `main` is
preserved legacy history and deliberately has no CI. CI seeds `.env` from
`.env.example` and builds the same Compose image a developer runs, so the
database is identical rather than merely similar.

## Deployment

`fabfile.py` exists and is **stale** — its `update` task runs `hg pull --update`,
from before the Step 2 move to git. Deployment to a new host is Step 21 and has
not happened. Do not treat `fabfile.py` as the live deploy path.

## Changing anything rendered

Markdown renders at save time into a sibling field. A rendering change needs a
data migration to re-render existing rows; a template change alone will not.

## Where the project record lives

`.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` is authoritative for
what has been done and why, including the reasoning behind decisions that look
odd. `.agents/tasks/.../stepNN/` holds the task files. **Search these before
concluding something is undocumented** — a great deal of apparent mystery in
this codebase is recorded there with the measurement attached.
