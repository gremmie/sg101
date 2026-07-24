# Task: Restore Case-Insensitive Lookup Behavior Lost with MySQL Collations

## Description
MySQL gives SG101 case-insensitive string comparison for free through its `*_ci`
collations. PostgreSQL is case-sensitive. Several pieces of application code
depend on the MySQL behavior without saying so, and will silently change meaning
on Postgres. Find every such dependency, decide how to preserve the behavior, and
lock it in with tests that fail on a case-sensitive engine without the fix.

This is a **behavior-parity** task, not a performance or cleanup task. The
failure mode is silent: nothing errors, the application simply starts allowing
things it used to reject.

## Background
Step 1's snapshot analysis confirmed **every collation in the production database
is case-insensitive** (`utf8_general_ci`, `latin1_swedish_ci`). The application
has therefore never needed `__iexact` to get case-insensitive matching on
usernames, emails, or tags.

A scan of the identity-related code found these collation-dependent lookups:

```
accounts/forms.py:91    User.objects.get(username=username)
accounts/forms.py:94    PendingUser.objects.get(username=username)
accounts/forms.py:97    IllegalUsername.objects.get(username=username)
accounts/forms.py:107   User.objects.filter(email=email).count()
accounts/forms.py:109   PendingUser.objects.filter(email=email).count()
accounts/forms.py:111   IllegalEmail.objects.filter(email=email).count()
accounts/forms.py:243   User.objects.get(email=email)
bio/forms.py:146        User.objects.get(username=username, is_active=True)
```

The first six are **registration-time uniqueness and blocklist checks**. On MySQL,
registering `BrianNeal` when `brianneal` exists is rejected, and an
`IllegalUsername`/`IllegalEmail` blocklist entry matches regardless of case. On
Postgres, both protections quietly stop working — duplicate-by-case accounts
become possible and the blocklist becomes case-evadable. The blocklist bypass is
the more serious of the two, since it is an abuse control.

`accounts/forms.py:243` is the **password-reset lookup by email**, and
`bio/forms.py:146` is a username lookup.

**Live data, checked against the production snapshot:**
- **Usernames: 0 case-collision groups** — a case-insensitive uniqueness
  constraint can be applied safely as-is.
- **Emails: 13 case-collision groups** — a naive case-insensitive unique index on
  `auth_user.email` **will fail to build**. These 13 need a decision before any
  constraint is attempted. Note also that `get(email=email)` at line 243 can
  already raise `MultipleObjectsReturned` today; determine whether that is a
  live bug and whether it is reachable.

**Implementation choice — avoid `CITextField`.** `django.contrib.postgres.fields`
provides `CIText`/`CICharField`/`CIEmailField`/`CITextField` on Django 3.2, but
they are **deprecated in Django 4.2 and removed in 5.1** in favour of
`db_collation` with a non-deterministic collation. Steps 13 and 14 take this
project to 4.2 and then 5.2, so adopting CIText fields now creates guaranteed
rework two steps out. Verify the exact deprecation timeline before deciding, and
prefer an approach that survives the remaining rungs untouched — explicit
`__iexact` lookups in application code, backed where appropriate by a functional
unique index (`CREATE UNIQUE INDEX ... ON auth_user (LOWER(username))`) applied
through a migration. `db_collation` is not available on Django 3.2.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/database-migration.md`
  (case-sensitivity findings, §"Snapshot findings")

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Audit the whole codebase for collation-dependent comparisons, not just the
   eight sites listed above. Cover usernames, emails, tags, slugs, and any other
   string identity lookup. The list above is a starting point produced by a
   targeted scan of `accounts/`, `bio/`, `forums/`, and `core/` — it is not
   guaranteed complete.
2. For each site found, decide and record whether case-insensitive behavior is
   *intended* or *incidental*. Do not blanket-convert; a lookup that should be
   case-sensitive must be left alone and noted as such.
3. Preserve intended case-insensitive behavior using an approach that survives
   the Django 4.2 and 5.2 rungs. Do not introduce `CIText`-family fields.
4. Resolve the 13 email case-collision groups: identify them, determine whether
   they represent real duplicate accounts or benign variations, and choose a
   course (leave as-is with `__iexact` lookups and no constraint, merge, or
   flag for manual review). Do not delete or merge user data without explicit
   sign-off.
5. Add tests that fail on a case-sensitive engine without the fix and pass with
   it. These are the deliverable that proves parity — a test that passes on both
   MySQL and Postgres regardless of the fix has not tested anything.
6. Any database constraint added must be applied through a migration, so it
   reaches both fresh databases and the converted production database.

## Dependencies
- Task 01 (a running Postgres to test case-sensitive behavior against)
- The production snapshot loaded in MySQL, for collision analysis

## Implementation Approach
1. Scan for collation-dependent lookups across all apps; produce the full list
   with an intended/incidental judgement per site.
2. Write the failing tests first, against Postgres, to demonstrate each
   regression concretely.
3. Apply the chosen fix — `__iexact` lookups, plus functional unique indexes
   where a real uniqueness guarantee is wanted.
4. Investigate the 13 email collisions and the reachability of
   `MultipleObjectsReturned` at `accounts/forms.py:243`; report findings and the
   recommended course before acting on user data.
5. Confirm the tests now pass on Postgres and still pass on MySQL and sqlite.

## Acceptance Criteria

1. **Complete Audit Recorded**
   - Given the codebase
   - When the audit is complete
   - Then every collation-dependent lookup is listed with an intended-vs-
     incidental judgement, and the list demonstrably covers more than the eight
     sites named in this task

2. **Registration Uniqueness Preserved**
   - Given an existing user `brianneal` on Postgres
   - When someone attempts to register `BrianNeal`
   - Then registration is rejected, matching current MySQL behavior

3. **Blocklist Cannot Be Evaded by Case**
   - Given an `IllegalUsername` or `IllegalEmail` blocklist entry on Postgres
   - When someone attempts to register a case-variant of that value
   - Then the attempt is rejected

4. **Password Reset Finds the Account**
   - Given a user registered with a mixed-case email on Postgres
   - When a password reset is requested using a different case
   - Then the account is found and the reset proceeds

5. **Tests Prove the Regression**
   - Given the new tests and the fix reverted
   - When the suite runs on Postgres
   - Then the new tests fail; and with the fix applied they pass on Postgres,
     MySQL, and sqlite alike

6. **Email Collisions Resolved or Explicitly Deferred**
   - Given the 13 case-collision groups in `auth_user.email`
   - When the task is complete
   - Then each is either resolved, or a documented decision exists to leave it
     with a stated reason; and no uniqueness constraint has been added that the
     existing data cannot satisfy

7. **No Deprecated Field Types Introduced**
   - Given the implemented solution
   - When the codebase is inspected
   - Then no `CIText`, `CICharField`, `CIEmailField`, or `CITextField` is used,
     and the chosen mechanism is verified to work on Django 4.2 and 5.2

## Metadata
- **Complexity**: High
- **Labels**: Database, PostgreSQL, Data Integrity, Authentication, Behavior
  Parity, Step 11
- **Required Skills**: PostgreSQL collations and functional indexes, Django ORM
  lookups and migrations, Django auth, data analysis
