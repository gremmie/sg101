# Schema Drift Audit — models.py vs. the real production schema

**Date:** 2026-07-24
**Scope:** all 26 apps, run when initial migrations were backfilled for the 21
apps that had none.
**Verdict:** **no structural drift.** Every table and every column that
`models.py` describes exists in production, with matching foreign keys. The
differences found are all type-vintage or index-vintage artifacts, listed and
resolved below.

## Why this audit is the point of the exercise

`makemigrations --check` has been a CI gate since `c76f920`, but a blanket
`makemigrations` **deliberately skips apps that have no migrations package** — it
only considers an app's models when the app is named on the command line. 21 of
26 apps had no package, so for fifteen years their `models.py` and their tables
could have drifted apart without any tool noticing. Generating an initial
migration from `models.py` and diffing it against the real tables is the first
parity check this schema has ever had.

## Method

Type mapping between engines is a poor place to hand-roll comparisons, so the
comparison is done **within one engine**:

1. `manage.py migrate` builds `sg101_frommigrations` on the same MySQL 5.7
   server from the migrations alone.
2. `information_schema` columns, indexes, and foreign keys are dumped from both
   that database and the production snapshot (`sg101`) and diffed.

The 7 tables that exist only in production are excluded — they are dead legacy
with no models left: `auth_message` (Django ≤1.3), `core_anonlastvisit`,
`core_userlastvisit`, `gcalendar_accesstoken` (returns when gcalendar is
revived), `irc_ircchannel`, `mailer_message` (django-mailer),
`membermap_mapentry`.

The same comparison was then repeated on PostgreSQL between a syncdb-built
schema and a migrations-built one.

## Results

| Comparison | Result |
| --- | --- |
| Columns present (MySQL) | **0 missing, 0 extra** across all 26 apps |
| Foreign keys (MySQL) | **identical**, both directions |
| Column definitions (MySQL) | 75 differ — all in the two categories below |
| Indexes (MySQL) | 14 extra in production — one category, below |
| PostgreSQL: syncdb-built vs migrations-built | **identical** — 0 column and 0 index differences |

### 1. `datetime` → `datetime(6)`, `time` → `time(6)` — 69 columns. No action.

Production columns have no fractional-second precision; the migrations produce
`datetime(6)`. This is MySQL vintage, not model drift: Django emits microsecond
precision on MySQL 5.6+, and these tables were created on 5.5. It affects
migrated apps (`forums`, `news`, `downloads`, `comments`, `countdown`) exactly as
much as backfilled ones, and Django's own `django_migrations` and
`django_session` too, which is the giveaway.

**Resolution:** none needed, and it does not survive the engine change —
PostgreSQL's `timestamp with time zone` always stores microseconds.

### 2. `varchar(75)` → `varchar(254)` on email columns — 3 columns. **Needs a decision.**

| Table | Column | Production | models.py |
| --- | --- | --- | --- |
| `accounts_illegalemail` | `email` | `varchar(75)` | `varchar(254)` |
| `accounts_pendinguser` | `email` | `varchar(75)` | `varchar(254)` |
| `podcast_channel` | `owner_email` | `varchar(75)` | `varchar(254)` |

This one is **real drift**: Django widened `EmailField` from 75 to 254 in 1.8
(RFC 3696), and these three columns were never widened because their apps had no
migrations to carry the change. `auth_user.email` *was* widened, by Django's own
`auth.0003_alter_user_email_max_length`, which is why it reads 254 today — a neat
illustration of exactly what the missing migrations cost.

Nothing is broken today, and no data is at risk: those three columns hold 0, 1,
and 1 rows, longest 25 characters, and the longest address anywhere in the
database is 47 (`auth_user.email`, 15,227 rows). But the failure mode is silent
— MySQL without strict mode truncates rather than erroring — so a >75-character
address would have been quietly cut.

**Recommended resolution:** let the widening happen as part of the engine move —
the converted tables should be `varchar(254)` to match `models.py`, since the
conversion is building a new schema anyway. It needs an explicit step because
pgloader derives column widths from the MySQL source, so it would carry the 75
across. **Owner decision required:** widen during conversion (recommended), or
correct the models down to 75 (not recommended — it contradicts Django's own
field default and would reject legitimate addresses).

### 3. `char(2)` → `varchar(2)` — 1 column. No action.

`bio_userprofile.country` is `char(2)` in production, `varchar(2)` in the model.
A CharField has always generated `varchar`, so this column was created or altered
by hand at some point. The two are interchangeable for a fixed 2-character
country code, and both convert to `varchar(2)` on PostgreSQL.

### 4. Column defaults on `news_story.priority` / `news_pendingstory.priority`. No action.

Production carries a database-level `DEFAULT 0`; the migrations don't. Django has
never emitted database defaults — it supplies field defaults in Python — so this
is a hand-applied `ALTER` or a pre-migration artifact. It cannot cause a wrong
value: Django always sends the column explicitly. It is also in a *migrated* app,
so it predates this work.

### 5. 14 redundant single-column indexes in production. No action.

All 14 are an index on the leading column of an existing composite unique index,
on m2m through-tables and the `*lastvisit` tables (`auth_user_groups(user_id)`,
`forums_topic_bookmarkers(topic_id)`, `polls_choice_voters(choice_id)`, and so
on). Old Django created a separate index for FK columns on MySQL; current Django
doesn't, because InnoDB's foreign key already requires one and the composite
index satisfies the prefix. They are harmless and were not created by any
migration — the migrations-built schema simply lacks them.

**Note for the conversion:** pgloader copies indexes from the MySQL source, so
the converted database may carry these 14 while a migrations-built one does not.
On PostgreSQL they are not redundant (foreign keys are not auto-indexed there),
so they're worth keeping if they arrive — but the difference should be expected
rather than treated as a conversion fault.

## Separate finding — an unapplied Django migration

`auth.0012_alter_user_first_name_max_length` (widens `auth_user.first_name` from
30 to 150) **is not applied** to the production database. It is not drift and not
related to the backfill — it shipped with Django 3.2 and was missed when that
upgrade's migrations were applied. It stays pending here deliberately, so that
"faking changes nothing" remains literally true.

**Owner decision required:** it is a real `ALTER` on 15,227 rows. Cleanest is to
apply it as part of the conversion, when the table is being rebuilt anyway.

## Gotcha for the cutover runbook

Backfilling made an already-recorded migration retroactively inconsistent.
`forums/migrations/0001_initial.py` has declared `('oembed', '__first__')` as a
dependency since 2015. That was inert while oembed had no migrations; the moment
oembed got one, Django's `check_consistent_history` saw `forums.0001_initial`
applied before its dependency and **refused to run any `migrate` command at
all** on the existing database:

```
django.db.migrations.exceptions.InconsistentMigrationHistory: Migration
forums.0001_initial is applied before its dependency oembed.0001_initial
```

`--fake` can't fix it, because the consistency check runs before the command
does anything. The one-time unlock is to record that migration directly, which
is precisely what `--fake` would have written:

```python
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
MigrationRecorder(connection).record_applied('oembed', '0001_initial')
```

Safe here because oembed's tables were confirmed column-for-column against the
models first. **Any database that already has the old migration history needs
this same one-time step** — including production at cutover, unless the converted
database is carrying a `django_migrations` table that already has the row.

## Verification that the backfill changed nothing

`--fake-initial` for the 20 remaining apps, against the production snapshot:

- column definitions: **identical** before and after (551 rows compared)
- indexes: **identical** before and after (261 rows compared)
- per-table row counts across all 91 tables: **the only change is
  `django_migrations`, 40 → 61**, i.e. exactly the 21 initial migrations
- live data intact: 15,227 users, 463,221 forum posts, 35,692 topics — matching
  the figures recorded when the snapshot was first loaded

Both build paths were then confirmed to agree, and a fresh PostgreSQL database
now builds from `migrate` alone in a single pass — no `--run-syncdb`, and none
of the phase-ordering machinery the engine work needed before this.
