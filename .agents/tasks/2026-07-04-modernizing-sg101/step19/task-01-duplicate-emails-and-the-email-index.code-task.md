# Task: Clear the Duplicate-Email Pairs and Build the Partial Unique Index

## Description
Write one data migration in `accounts/` that blanks the losing address on every
duplicate-email pair and then creates a **partial functional unique index** on
`auth_user`:

```sql
CREATE UNIQUE INDEX auth_user_email_lower_uniq ON auth_user (LOWER(email))
    WHERE email <> ''
```

The resolution was decided 2026-09-05 and is not open here. What this task owes
is a migration that computes the pairs rather than hardcoding them, states its
tie-breaks, and is verified against a **freshly converted production snapshot**
rather than only against the already-migrated dev database.

This is the smallest of Phase C's four items and it goes first deliberately: it
establishes the rehearsal procedure — `tools/pgloader/convert.sh` then
`tools/pgloader/post_convert.py` — that the other three reuse.

## Background

### The decision, and what is not being reopened
Recorded in `STATUS.md` under *Step 19 Phase C — the duplicate-email pairs,
DECIDED 2026-09-05*, with the evidence in `research/collation-audit.md`:

1. **Build the partial unique index.**
2. **The losing account keeps everything except its address** — `email = ''` and
   nothing else. No deactivation, no merge, no content moved. It keeps its posts
   and can still log in; it loses self-serve password reset until someone gives
   it an address back.
3. **Keeper is most-recent-login.** The two candidate rules — most posts, most
   recent login — agree on 12 of the 13 pairs and differ only on
   `member08@example.com`, where the tie breaks toward the account the member
   actually uses.

### This reverses a Step 11 decision, narrowly
`research/collation-audit.md`'s Decision 1 reads *"No unique index on
`auth_user.email`. The data cannot satisfy one in either direction."* That is
true of a **plain** unique index on the column, which the four blank addresses
defeat on their own. A partial functional index was not considered there. The
reversal is that narrow and the task file should not read as though the earlier
decision was careless.

### The index must be partial, permanently
Four accounts hold `email = ''`, and one of them is **`Anonymous` (id 1)** — a
phpBB inheritance. An early version of this site ran phpBB, where deleting a
user reassigned their posts to `Anonymous`; it holds **796 posts and 78 topics**
and has an unusable password. It must never carry an address. So `WHERE email
<> ''` is the correct permanent shape, not a workaround for a transitional data
problem. The other three blanks are `c4logic` (345, inactive), `Huatulphonic`
(808, last seen 2006-12-30) and `Clevedale_Renamed_By_Admin` (7819).

### Why this is worth building at all, since nothing is broken
**The trap this item is famous for was handled on 2026-08-22.** Step 16 task 05
wrote `bio.forms.EditUserForm.clean_email` the way it needs to be written: it
returns early when the address is unchanged, so none of the 26 members is locked
out of saving a profile edit, and it rejects only *changing to* a taken address.
`accounts.forms.RegistrationForm.clean_email` has checked `email__iexact` all
along, and `ForgotUsernameForm` lists every match rather than calling `get()`.

**No new pair can be created through the site.** What buys the index is that the
admin and the management shell go around both form checks — the same argument
`accounts/0002_auth_user_username_lower_unique.py` already makes for usernames:
*"the admin, a management shell, and two registrations racing each other all go
around it."* That is not hypothetical here; `c4logic` was deactivated by hand in
production while this was being decided.

### The 13 pairs as measured in production, 2026-09-05

| Address | Keeps the address | Blanked |
|---|---|---|
| `member13@example.com` | `terma_reverb` 6177 · 2026-05-31 · 52 posts | `ymastorak` 11446 · 0 |
| `member07@example.com` | `sdubose` 1114 · 2026-03-15 · 9 | `scoot` 540 · 1 |
| `member02@example.com` | `Jester` 10107 · 2025-04-08 · 17 | `JesterR` 7707 · 0 |
| `member12@example.com` | `Turnip` 142 · 2024-11-07 · 30 | `Turnip_Returns` 14260 · 0 |
| `member06@example.com` | `Admiral_Fishwich` 4456 · 2024-01-20 · 118 | `MajorReverb` 2922 · 4 |
| `member08@example.com` | `kinghawaii` 892 · 2023-07-21 · 4 | `kinghawaii50` 1279 · 15 |
| `member11@example.com` | `alphaking` 6981 · 2022-06-17 · 195 | `alphaking1` 13092 · 1 · inactive |
| `member09@example.com` | `NothingDiesWithBlueSkies` 4045 · 2020-01-04 · 36 | `TastyGrog` 3757 · 11 |
| `member03@example.com` | `SurfBeat` 2373 · 2019-03-18 · 285 · inactive | `Joey` 2947 · 11 · inactive |
| `member04@example.com` | `knucklesnuclear` 5180 · 2016-06-06 · 60 | `guitarbrad` 379 · 0 |
| `member10@example.com` | `SpitfireMkI` 4053 · 2015-03-01 · 30 | `UnmannedBassPlayer` 2592 · 6 |
| `member01@example.com` | `Hydronaught` 3566 · 2013-08-19 · 12 | `Drippy` 3111 · 6 |
| `member05@example.com` | `LouSeefer` 5898 · 2012-04-05 · 1 | `mudbone99` 4769 · 0 |

**This table is context, not the migration's input.** It is a 2026-09-05 reading
and the migration runs against a snapshot taken at cutover. Hardcoding these 26
ids would silently skip a fourteenth pair created in between.

### Where this actually runs
`tools/pgloader/convert.sh` converts a fresh production MySQL dump; pgloader
copies `django_migrations` across as production had it (Django 1.9 era), and
`tools/pgloader/post_convert.py` then calls `migrate` with `fake_initial=True`
to apply everything since. **This migration runs there, at cutover, against real
production data, once.** Nothing is done by hand and nothing at a SQL prompt.

`accounts/0003_normalize_case_variant_emails` is the precedent for the data half
— it is the migration that lowercased `member03@example.com` during the
Step 11 conversion, which is how that group became the thirteenth byte-identical
pair. `accounts/0002_auth_user_username_lower_unique` is the precedent for the
index half, including the MySQL guard.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — *Step 19 Phase C —
  the duplicate-email pairs, DECIDED 2026-09-05*, the decision record
- `.agents/planning/2026-07-04-modernizing-sg101/research/collation-audit.md` —
  the original audit, the production re-measurement, post counts, and the four
  blank-address accounts
- `accounts/migrations/0002_auth_user_username_lower_unique.py` — the index shape
  and the MySQL guard to copy
- `accounts/migrations/0003_normalize_case_variant_emails.py` — the data-migration
  precedent in the same app

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **One migration in `accounts/`, containing both halves.** The blanking and the
   index creation belong in the same migration so the database is never left in a
   state where one ran and the other did not.

2. **Compute the duplicate groups at run time.** Group by `LOWER(email)` over
   `email <> ''`, having `count(*) > 1`. Do not hardcode ids or addresses.

3. **Keeper rule: most recent `last_login`.** Within each group the account with
   the greatest `last_login` keeps the address; every other row in the group gets
   `email = ''`.

4. **State the tie-breaks, do not discover them.** None of the current 13 pairs
   hits either case, and the migration will meet databases where one does:
   - A `NULL` `last_login` **loses** to any non-null one.
   - All-null or exactly-equal timestamps: the **lowest `id`** keeps the address.
   - A group of three or more: one keeper, all others blanked.

5. **Nothing but `email` changes.** No `is_active` edit, no deletion, no
   reassignment of posts or profiles.

6. **MySQL guard on the index, as in `0002`.** MySQL 5.7 has no functional
   indexes and needs none. The blanking half still runs on MySQL.

7. **Decide the reverse explicitly.** Blanking cannot be undone from the row, so
   either the reverse restores addresses captured in the migration, or the
   migration declares itself irreversible with a comment saying why. Do not leave
   `RunPython` to its default.

8. **Idempotency must be verified, not assumed.** Once the groups are gone a
   second run should find nothing and change nothing.

## Dependencies
- `accounts/migrations/0002` and `0003` — precedents for both halves
- `tools/pgloader/convert.sh` and `tools/pgloader/post_convert.py` — the
  conversion path this must be verified through
- A MySQL production snapshot to convert; `MYSQL_DB=sg101_pristine
  tools/pgloader/convert.sh` converts a pristine copy without disturbing the
  working database
- `docker_test` settings for the suite

## Implementation Approach

1. Write the migration with the grouping query and the rule, and a module
   docstring that states the decision and its date, in the style of `0002` and
   `0003`.
2. Add tests that build duplicate groups in a test database and assert the
   keeper, the blanking, the tie-breaks and idempotency. Include the
   three-account group and the null-`last_login` case, neither of which exists in
   production.
3. Prove the index rejects what it should: a second account cannot be given an
   address another holds, case-insensitively, while two blanks remain legal.
4. **Rehearse on a freshly converted snapshot.** Convert a pristine production
   dump, run `post_convert.py`, and confirm 13 rows were blanked, the index
   built, and `LOWER(email)` is unique over the non-blank rows.
5. Update `research/collation-audit.md`'s Decision 1 to point at the reversal, so
   the audit does not go on saying no index is possible.

## Acceptance Criteria

**Amended 2026-09-05, on Brian's challenge: migrations mostly do not need
tests.** A migration runs once per database and is append-only, so a test guards
a regression that structurally cannot happen — and `0002` and `0003` both shipped
untested, with `0003`'s effect visible in the production data today, which is
better evidence than a unit test. **The primary gate here is criterion 9**, the
rehearsal on a freshly converted snapshot, because it exercises the rule against
13 real groups and can assert every keeper against the decided table.

Tests are kept for exactly one thing: **the branches the production data cannot
reach** — a null `last_login`, an exact tie, a group of three. Those exist only
to serve a fourteenth pair appearing in the cutover snapshot, which is the same
risk the compute-don't-hardcode requirement addresses. Their value is getting the
rule right before it touches a snapshot, not regression protection.

Criteria 3 and 4 were originally written as unit tests and are not. Asserting
that a PostgreSQL unique index rejects a duplicate is testing PostgreSQL.

1. **The pairs are cleared by the stated rule**
   - Given a database holding the 13 duplicate groups
   - When the migration runs
   - Then exactly 13 rows have `email` set to `''`, and in each group the
     surviving address belongs to the account with the greatest `last_login`

2. **Nothing else about the losing accounts changes**
   - Given an account that loses its address
   - When the migration has run
   - Then its `is_active`, its posts, its topics and its profile are untouched,
     and it can still authenticate

3. **The index exists and enforces case-insensitive uniqueness** *(verified on
   the converted snapshot and by the migration applying at all, not by a unit
   test)*
   - Given the migration has run on PostgreSQL
   - When a second account is given an address another account already holds, in
     any combination of case, by the admin or the shell
   - Then the write fails on `auth_user_email_lower_uniq`

4. **Blank addresses remain legal, without limit** *(the suite is the evidence —
   most of its 165 `create_user()` calls pass `''`, so a predicate that did not
   exempt blanks would fail the suite loudly)*
   - Given `Anonymous` and the three other blank-address accounts
   - When the index is in place
   - Then all four coexist, and a fifth account may also be blanked

5. **Tie-breaks behave as specified** *(unit-tested — production has no such
   group, so the rehearsal is blind to this)*
   - Given a group where one account has a null `last_login`, and a group where
     two are exactly equal
   - When the resolution rule runs
   - Then the null loses, and the equal case is settled by lowest `id`

6. **A group of three is handled** *(unit-tested, same reason)*
   - Given three accounts sharing one address
   - When the resolution rule runs
   - Then one keeps it and two are blanked

7. **Idempotent** *(unit-tested)*
   - Given the rule has already run
   - When it is run again against the same rows
   - Then no row changes and no error is raised

8. **MySQL is guarded**
   - Given the migration runs against MySQL 5.7
   - When it completes
   - Then the blanking has been applied and no functional index was attempted

9. **Verified on a freshly converted production snapshot**
   - Given a pristine production dump converted by `tools/pgloader/convert.sh`
   - When `tools/pgloader/post_convert.py` runs the migration chain
   - Then it completes without error, 13 rows are blanked, and a
     `GROUP BY LOWER(email) HAVING count(*) > 1` over the non-blank rows returns
     nothing

10. **The reverse is a decision, not an accident**
    - Given the migration
    - When its reverse is read
    - Then it either restores the addresses or refuses with a stated reason, and
      the choice is explained in the docstring

11. **The suite is green, and the rule's tests are mutation-verified**
    - Given the full test suite, and separately the deprecation gate, on
      `docker_test`
    - When each is run in the container
    - Then both pass — this also checks that the new index does not break the 165
      existing `create_user()` calls, which is a separate question from whether
      the migration is correct — and each new assertion about the rule has been
      observed to fail against a deliberate mutation, reversing the keeper rule
      included

## Metadata
- **Complexity**: Medium
- **Labels**: accounts, data migration, schema, PostgreSQL, partial index, Step 19 Phase C
- **Required Skills**: Django migrations, PostgreSQL functional and partial indexes, SQL aggregation, pgloader conversion workflow
