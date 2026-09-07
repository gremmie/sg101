# Collation-dependent lookups — full audit (Step 11, task 02)

**Date:** 2026-07-25

MySQL gave SG101 case-insensitive string comparison for free through its `*_ci`
collations. Postgres is case-sensitive. This is the complete list of places the
application depended on that, with a judgement for each.

## Method

AST scan (`scan_lookups.py`, kept in the session scratchpad), not grep — the
Step 9 lesson about multi-line call signatures applies. It walks every `.py`
outside `migrations/`, collects keyword arguments to ORM query methods
(`get`/`filter`/`exclude`/`get_or_create`/`count`/…), and keeps those whose
field name is declared as a string field in some `models.py`.

Two refinements were needed, both of which changed the answer:

- `register.filter(name=...)` in template-tag modules is not an ORM call.
- **The `get_object_or_404`/`get_list_or_404` shortcuts are plain function
  calls, not attribute calls, so the first pass missed them entirely.** Four
  real findings live there, including the tag lookup.

106 raw hits. The field-name → model map is ambiguous (a `category=` kwarg is
usually an FK object, not a string), so every hit was then read in source.

## Intended case-insensitive — converted to `__iexact`

| site | lookup | what would have broken |
|---|---|---|
| `accounts/forms.py:91` | `User.get(username=)` | duplicate-by-case registration |
| `accounts/forms.py:94` | `PendingUser.get(username=)` | same, against pending registrations |
| `accounts/forms.py:97` | `IllegalUsername.get(username=)` | **blocklist evaded by case** |
| `accounts/forms.py:107` | `User.filter(email=)` | duplicate-by-case email |
| `accounts/forms.py:109` | `PendingUser.filter(email=)` | same |
| `accounts/forms.py:111` | `IllegalEmail.filter(email=)` | **blocklist evaded by case** |
| `accounts/forms.py:243` | `User.get(email=)` | forgot-username fails to find the account |
| `accounts/views.py:109` | `PendingUser.get(username=)` | registration confirmation fails |
| `bio/forms.py:146` | `User.get(username=, is_active=True)` | member search says "does not exist" |
| `messages/forms.py:47` | `User.get(username=receiver)` | PM to a hand-typed recipient fails |
| `donations/views.py:183` | `User.get(username__exact=)` | PayPal donation silently unlinked |
| `bio/views.py:83` | `get_object_or_404(User, username=)` | `/profile/view/<name>/` 404s |
| `forums/views/main.py:918` | `get_object_or_404(User, username=)` | posts-by-user 404s |
| `user_photos/views.py:142` | `get_object_or_404(User, username=)` | photo gallery 404s |
| `news/views.py:184` | `get_object_or_404(Tag, name=)` | `/news/tag/<Name>/` 404s |

The last four are URL-driven. **7,006 of 15,227 usernames carry uppercase**, so
those URLs are case-bearing in practice. Internal links are generated from
`user.username` and stay correct either way; the exposure is old bookmarks,
pasted links, and hand-typed URLs.

## Incidental — deliberately left case-sensitive

| site | value | why |
|---|---|---|
| `donations/views.py:157` | `txn_id__exact` | PayPal transaction ids are canonical |
| `user_photos/forms.py:67` | `signature=` | `md5().hexdigest()`, always lowercase |
| `forums/views/main.py:930` | `user_ip=` | value read from the database, compared to it |
| `oembed/views.py:33` | `url=` | URL cache key; case-sensitive is *more* correct |
| `elsewhere/management.py:18,30` | `get_or_create(name=)` | seeds from a fixed in-repo list |
| `forums/feeds.py:24`, `forums/tools.py:94`, `weblinks/views.py:124`, `downloads/views.py:59`, `news/views.py:116`, `forums/views/main.py:119,288,692,765`, `downloads/management/commands/dl*.py` | `slug=` | every production slug is lowercase |
| `banners/templatetags/banner_tags.py:44` | `campaign__slug=` | argument is a template literal |
| `bio/templatetags/bio_tags.py:110` | `exclude(country='')` | compares against the empty string |

## Checked and not affected

Recorded so nobody re-checks them:

- **`antispam.contains_spam`** — the site's other abuse control. Matches in
  Python (`s.lower()`; `SpamPhrase.save()` lowercases on write), never in SQL.
- **Django's `PasswordResetForm.get_users`** already uses `email__iexact`, so
  password reset was engine-independent before this task. Pinned with a test.
- **`FORCE_LOWERCASE_TAGS = True`** is already set (`sg101/settings/base.py:196`).
  django-tagging lowercases a tag name before `get_or_create`, so tag
  *creation* was already engine-independent — that is why all 1,006 production
  tags are lowercase with no case variants. It is the setting doing that, not
  the collation. Only the tag *lookup* needed changing.
- **No `__contains`/`__startswith`/`__endswith`** anywhere in application code.
- **No raw SQL, `.extra()`, or cursor use** outside the sqlite test pragma.
- Admin `search_fields` generate `__icontains` unless prefixed.
- `core/views.py:41` already used `username__istartswith`;
  `weblinks/forms.py:16` already used `url__iexact`.

## Production data

Measured against the MySQL snapshot. **`GROUP BY email` on a `*_ci` column
groups case-insensitively** — the same trap this task is about, and it produced
a wrong first answer here until `BINARY` was forced.

| measure | value |
|---|---|
| users | 15,227 |
| usernames containing uppercase | 7,006 |
| **username case-collision groups** | **0** |
| emails containing uppercase | 1,043 |
| `auth_user.email` collision groups (CI) | 13 |
| — byte-identical duplicates | **12** *(13 after `0003` — see below)* |
| — differing **only** by case | **1** |
| blank emails | 4 |
| `accounts_pendinguser` / `illegalusername` / `illegalemail` | 1 / 4 / 0 rows, no collisions |
| tags | 1,006 (all lowercase, 0 collisions) — **1,001 of them live; see below** |
| forum slugs non-lowercase | 0 |

## `tagging_tag` does not survive — resolved 2026-09-07

The tag-cloud half of the ORDER BY audit was blocked on Step 19 Phase C under the
rule *do not record a decision about a table you may delete*. **Task 04 settled
it: `django-tagging` is replaced by a PostgreSQL `ArrayField`, so `tagging_tag`
and `tagging_taggeditem` both go.** Decision record and numbers in `STATUS.md`
§ "Step 19 Phase C task 04".

**The cloud's ordering decision carries over unchanged.** `ORDER BY
tagging_tag.name` becomes an ordering on the unnested array element — the same
strings under the same `en_US.utf8` collation — and the two orderings were
measured identical across all 1,001 live tags. "Keep PostgreSQL's ordering"
stands.

### The one finding here that outlives the table

Two stories' tags disagree between `news_story.tags` and the join table:

```
story 1539 (2021-10-31)   column: jay-poisön    join table: jay-poison
story 1730 (2024-10-12)   column: thálasses     join table: thalasses
```

**This is MySQL's accent-insensitive collation on `tagging_tag.name`'s unique
index, and it is production data — the MySQL snapshot holds the same bytes, so
the PostgreSQL conversion did not cause it.** In both cases an ASCII-spelled tag
already existed (`jay-poison` 2020-11-08, `thalasses` 2024-06-04), so
`Tag.objects.get_or_create()` matched the later accented submission to it: the
join table points at the ASCII tag while the column keeps what the author typed.
Four other accented tags — `bárujárn`, `diabolico-coupè`, `electrohúmedos`,
`taner-öngür` — kept their accents precisely because each has one story and never
had an ASCII twin to be folded into.

**It is also a latent behaviour change from the engine switch**, of the same
family as the rest of this audit: PostgreSQL's index is not accent-insensitive,
so re-saving story 1539 today would create a *second* tag and split the two
spellings across two tag pages. Nothing has re-saved it, so nothing has fired —
and the `ArrayField` migration takes the join table's ASCII spelling, which is
what every page renders today, closing it.

**The live tag figures, also from task 04:** 1,001 tags across 3,931 rows on
1,208 stories. The 1,006/4,561 recorded above counts **630 orphaned join rows**
(616 pointing at deleted `news_pendingstory` rows, 14 at deleted stories) and
**5 tags reachable only through them**, plus 3 tags used by nothing at all.

### The 13 email groups

Twelve are **not** case collisions — two accounts holding the same address,
byte for byte. They read as people who made a second account years later:

```
member01@example.com          Drippy | Hydronaught
member02@example.com           JesterR | Jester
member04@example.com   guitarbrad | knucklesnuclear
member05@example.com          mudbone99 | LouSeefer
member06@example.com        MajorReverb | Admiral_Fishwich
member07@example.com            scoot | sdubose
member08@example.com              kinghawaii | kinghawaii50
member09@example.com          TastyGrog | NothingDiesWithBlueSkies
member10@example.com        UnmannedBassPlayer | SpitfireMkI
member11@example.com               alphaking | alphaking1
member12@example.com           Turnip | Turnip_Returns
member13@example.com            terma_reverb | ymastorak
```

They exist today on MySQL, are untouched by the engine change, and would defeat
a plain case-sensitive unique index just as surely as a case-insensitive one.
**Left alone** — data hygiene for Step 19, not a Step 11 problem.

One group was a true case variant, normalized by
`accounts/0003_normalize_case_variant_emails`:

```
id 2373  SurfBeat  member03@example.com   is_active=0
id 2947  Joey      member03@example.com   is_active=1   -> lowercased
```

### Re-measured 2026-09-05 on the converted database — it is **13 pairs**, not 12

The figures above are correct as measured, and they were measured *before*
`accounts/0003_normalize_case_variant_emails` ran. **That migration did not remove
the thirteenth group — it converted it.** Lowercasing `member03@example.com`
made `SurfBeat` and `Joey` byte-identical, so the case variant became a duplicate
pair of exactly the same kind as the other twelve.

Measured against the running PostgreSQL, `GROUP BY email HAVING count(*) > 1` on
15,227 users: **13 groups, 26 accounts, every group of size 2, all byte-identical.**
So the "26 members" in the trap note downstream has been right all along, and every
"12 pairs" that contradicts it is the stale half of the pair of numbers.

### The 26 accounts, with the activity that bears on resolving them

Recorded because the item has always carried the *count* and never the *shape*, and
the shape is what decides whether "delete one" is a decision or a judgement call.

| Address | Account A | Account B | Reads as |
|---|---|---|---|
| `member11@example.com` | `alphaking` 6981, active, 2022-06-17 | `alphaking1` 13092, **inactive**, 2022-05-16 | already resolved by deactivation |
| `member03@example.com` | `SurfBeat` 2373, **inactive**, 2019-03-18 | `Joey` 2947, active, 2016-09-22 | already resolved by deactivation |
| `member05@example.com` | `mudbone99` 4769, 2011-03-07 | `LouSeefer` 5898, 2012-04-05 | A never returned after joining |
| `member12@example.com` | `Turnip` 142, 2024-11-07 | `Turnip_Returns` 14260, 2024-04-19 | B never returned after joining |
| `member08@example.com` | `kinghawaii` 892, 2023-07-21 | `kinghawaii50` 1279, 2007-10-20 | B abandoned in 2007 |
| `member04@example.com` | `guitarbrad` 379, 2006-07-05 | `knucklesnuclear` 5180, 2016-06-06 | A abandoned in 2006 |
| `member01@example.com` | `Drippy` 3111, 2011-08-13 | `Hydronaught` 3566, 2013-08-19 | both long dormant |
| `member10@example.com` | `UnmannedBassPlayer` 2592, 2010-03-18 | `SpitfireMkI` 4053, 2015-03-01 | both long dormant |
| `member09@example.com` | `TastyGrog` 3757, 2017-07-11 | `NothingDies…` 4045, 2020-01-04 | both long dormant |
| `member06@example.com` | `MajorReverb` 2922, 2012-02-08 | `Admiral_Fishwich` 4456, 2024-01-20 | B still current |
| `member02@example.com` | `JesterR` 7707, 2013-09-29 | `Jester` 10107, 2025-04-08 | B still current |
| `member07@example.com` | `scoot` 540, 2016-08-07 | `sdubose` 1114, **2026-03-15** | B currently active |
| `member13@example.com` | `terma_reverb` 6177, **2026-05-31** | `ymastorak` 11446, **2025-07-21** | **both currently active** |

Dates are `last_login`. Two pairs are already half-deactivated and need no member
contacted; three more have a half that logged in once and never came back. **The
hard case is `member13@example.com`, where both accounts have been used this year**,
and `member12@example.com` and `member07@example.com` are the next hardest — one
live account each, with forum history behind the other.

**No resolution is decided.** Merge, deactivate one side, blank one address, or
leave the data and guard only in the form — the record has never chosen, and the
choice edits real members' accounts, so it belongs to a decision sitting rather
than to a cleanup. What the shape above establishes is that a single blanket rule
will not fit all thirteen. [[measure-before-recording-in-planning-docs]]

### Provenance, and a re-measurement against production — 2026-09-05

**The table above was read from the Docker snapshot, and that needs saying.** The
newest `date_joined` in it is 2026-07-07, so it is a production snapshot roughly
two months old. Four rows in the whole 15,227 carry sub-second `last_login`
precision — ids 1, 2, 5 and 12 — which is Django writing to Postgres rather than a
value converted from MySQL, i.e. someone logging in locally. **None of the 26 pair
accounts is among them**, so the figures were not perturbed by local use.

**Re-read through jaguar's own Django on 2026-09-05**, and every id, username,
`is_active` and `last_login` in the 13 groups matches the snapshot exactly. One
row in the database does not: `c4logic` reads `is_active=False` in production and
`True` in the snapshot, because Brian deactivated it there directly. **A known
production change absent from the snapshot is the cleanest possible demonstration
of the caveat**, and it arrived by itself.

### Post counts, which are the signal `last_login` is not

| Address | Account | Status | Last login | Posts | Topics |
|---|---|---|---|---|---|
| `member01@example.com` | `Drippy` 3111 | active | 2011-08-13 | 6 | 1 |
| | `Hydronaught` 3566 | active | 2013-08-19 | 12 | 4 |
| `member02@example.com` | `JesterR` 7707 | active | 2013-09-29 | 0 | 0 |
| | `Jester` 10107 | active | 2025-04-08 | 17 | 1 |
| `member03@example.com` | `SurfBeat` 2373 | inactive | 2019-03-18 | 285 | 30 |
| | `Joey` 2947 | inactive *(2026-09-05)* | 2016-09-22 | 11 | 2 |
| `member04@example.com` | `guitarbrad` 379 | active | 2006-07-05 | 0 | 0 |
| | `knucklesnuclear` 5180 | active | 2016-06-06 | 60 | 0 |
| `member05@example.com` | `mudbone99` 4769 | active | 2011-03-07 | 0 | 0 |
| | `LouSeefer` 5898 | active | 2012-04-05 | 1 | 0 |
| `member06@example.com` | `MajorReverb` 2922 | active | 2012-02-08 | 4 | 2 |
| | `Admiral_Fishwich` 4456 | active | 2024-01-20 | 118 | 13 |
| `member07@example.com` | `scoot` 540 | active | 2016-08-07 | 1 | 0 |
| | `sdubose` 1114 | active | 2026-03-15 | 9 | 2 |
| `member08@example.com` | `kinghawaii` 892 | active | 2023-07-21 | 4 | 3 |
| | `kinghawaii50` 1279 | active | 2007-10-20 | 15 | 9 |
| `member09@example.com` | `TastyGrog` 3757 | active | 2017-07-11 | 11 | 4 |
| | `NothingDiesWithBlueSkies` 4045 | active | 2020-01-04 | 36 | 7 |
| `member10@example.com` | `UnmannedBassPlayer` 2592 | active | 2010-03-18 | 6 | 1 |
| | `SpitfireMkI` 4053 | active | 2015-03-01 | 30 | 4 |
| `member11@example.com` | `alphaking` 6981 | active | 2022-06-17 | 195 | 23 |
| | `alphaking1` 13092 | inactive | 2022-05-16 | 1 | 0 |
| `member12@example.com` | `Turnip` 142 | active | 2024-11-07 | 30 | 7 |
| | `Turnip_Returns` 14260 | active | 2024-04-19 | 0 | 0 |
| `member13@example.com` | `terma_reverb` 6177 | active | 2026-05-31 | 52 | 3 |
| | `ymastorak` 11446 | active | 2025-07-21 | 0 | 0 |

**Five pairs have a half that never posted at all**, which login dates alone did
not reveal — and one of them, `member13@example.com`, had been written up as the
hardest case in the set on the strength of two recent logins. It is the easiest.
**The lesson is not that `last_login` is wrong but that it was the only column
asked for**, and a second column reversed the reading. [[measure-before-recording-in-planning-docs]]

### The four blank-address accounts

| id | username | active | last login | what it is |
|---|---|---|---|---|
| 1 | `Anonymous` | no | — | **phpBB inheritance.** An early version of this site ran phpBB, where deleting a user reassigned their posts to `Anonymous`. It holds **796 posts and 78 topics**, has an unusable password (`!`), and must never carry an address |
| 345 | `c4logic` | no | 2006-08-15 | deactivated in production 2026-09-05 |
| 808 | `Huatulphonic` | yes | 2006-12-30 | logged in the day after joining, never again |
| 7819 | `Clevedale_Renamed_By_Admin` | no | 2013-11-15 | the username records an admin action |

`Anonymous` is the reason the unique index must be partial rather than plain, and
it is a permanent reason rather than a transitional one.

## Decisions

1. **No unique index on `auth_user.email`.** The data cannot satisfy one in
   either direction. `__iexact` lookups only.
2. **Functional unique index on `LOWER(username)`** — 0 collisions, so it
   builds cleanly. Guarded to skip **MySQL**, which has no functional indexes
   and needs none (its collation already makes the column's `UNIQUE`
   case-insensitive). Postgres and SQLite both get it, so the default sqlite
   suite exercises it.
3. **No `CIText` family** (AC 7) — deprecated in Django 4.2, removed in 5.1,
   i.e. inside Steps 13 and 14. `db_collation` is 4.2+ and unavailable on 3.2.
   `UniqueConstraint(Lower(...))` is 4.0+, and `auth_user` is not our model, so
   the index has to be raw SQL in a migration.

## Live bug, engine-independent

`ForgotUsernameForm.save()` called `User.objects.get(email=email)` with no
`MultipleObjectsReturned` handler. All 13 groups reached it **today, on
MySQL** — those users got a 500 and could never recover their username.
Converting the lookup to `__iexact` neither created nor worsened this; fixed
here because it is the same line.
