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
| — byte-identical duplicates | **12** |
| — differing **only** by case | **1** |
| blank emails | 4 |
| `accounts_pendinguser` / `illegalusername` / `illegalemail` | 1 / 4 / 0 rows, no collisions |
| tags | 1,006 (all lowercase, 0 collisions) |
| forum slugs non-lowercase | 0 |

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
