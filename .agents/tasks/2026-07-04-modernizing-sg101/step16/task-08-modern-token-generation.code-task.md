# Task: Replace Home-Grown Token Generation with `secrets`

## Description
`PendingUserManager._make_key()` mints the registration confirmation key from
the Mersenne Twister. Replace it — and the registration code word — with the
`secrets` module, and make the key comparison constant-time. **Brian's call,
2026-08-16**, after the pattern was flagged as something not to propagate into
task 05's new email-confirmation flow.

Doing this *before* task 05 means the new flow inherits a correct helper instead
of copying a bad one, which is the whole reason this is its own task rather than
a footnote in that one.

## Background

### What it does today
`accounts/models.py:67-73`:

```python
def _make_key(self):
    s = ''.join(random.sample(string.printable, 8))
    delta = datetime.date.today() - datetime.date(1846, 12, 28)
    days = base64.urlsafe_b64encode(str(delta * 10).encode('ascii')).decode('ascii')
    raw = u'%s%s%s%s' % (settings.SECRET_KEY, self.create_count, s, days)
    key = hashlib.sha1(raw.encode('utf-8')).hexdigest()[::2]
    return key
```

Four ingredients: `SECRET_KEY`, an in-memory counter, eight characters sampled by
`random.sample`, and today's date scaled by ten and base64'd. SHA-1'd, then every
*other* hex character taken — yielding 20 characters.

### An honest assessment of the risk
**This is not an active emergency, and should not be written up as one.** The
inclusion of `SECRET_KEY` in the hashed input means an attacker who cannot read
the settings cannot reproduce a key, whatever the quality of the other
ingredients. The practical exposure is small: a one-day expiry window, one
pending user at the time of writing, and a key that must be paired with a
known username.

What is wrong with it is that its security rests entirely on one ingredient
while *appearing* to rest on four. `random.sample` is the Mersenne Twister — not
a CSPRNG, and observable output can reveal its state. `create_count` is a
per-process counter that resets on restart. The date component is identical for
every key minted the same day. Taking every other character of a SHA-1 halves
the digest for no stated reason. None of these add entropy an attacker could not
model; they add the *appearance* of entropy, which is worse than a short honest
token because it discourages the question.

`secrets.token_urlsafe(32)` is one line, is unambiguously correct, and needs no
reasoning about `SECRET_KEY` exposure.

### The comparison is not constant-time
`accounts/views.py:118` is `if pending_user.key != key:`. A byte-wise
comparison in principle leaks position-of-first-difference through timing.
Over HTTP against a 20-character key this is not a practical attack, but
`secrets.compare_digest` is a drop-in replacement and is the right idiom.

### The field is too narrow for a modern token
`PendingUser.key` is `models.CharField(max_length=20)`, sized for exactly the
20 characters `_make_key()` returns. `secrets.token_urlsafe(32)` produces 43
characters, so **this needs a migration**, not just a code change.

### What else the audit found — and what to leave alone
Grepped across the tree 2026-08-16:

**In scope:**
- `accounts/models.py:67-73` — the registration key. The primary target.
- `accounts/forms.py:43` — `generate_registration_code()`, building an
  anti-spam code word as `random.choice(CODE_WORD_CHOICES)` plus
  `random.randint(100, 999)`. Human-typed, low-stakes, and the search space is
  small either way — but `secrets.choice` and `secrets.randbelow` cost nothing
  and remove a `random` import from a security-adjacent module.

**Explicitly out of scope — do not fix:**
- `wiki/middleware.py:36,64` uses `random.sample(string.printable, 64)` in the
  same style, and is the closest sibling of the registration key. **The `wiki`
  app is being deleted in Step 19.** Fixing it would be work thrown away; leave
  it and let the deletion handle it.
- `core/templatetags/core_tags.py:243` (banner rotation),
  `weblinks/views.py:170` (random link), `potd/tools.py` (photo of the day) —
  cosmetic selection, no security property. Leave them.
- `contests/models.py:96` picks a contest winner with `random.choice`. Fairness,
  not secrecy, and non-adversarial. Leave it, but it is the one judgement call
  here worth a second opinion.
- Every `uuid.uuid4()` in `tools/` and `core/images/upload.py` already draws
  from `os.urandom`. Correct as-is.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `step16/task-05-verified-email-change.code-task.md` — the consumer of the new
  helper
- `accounts/views.py:99-130` — `register_confirm`, the comparison site
- Python `secrets` documentation, particularly `token_urlsafe` and
  `compare_digest`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Replace `_make_key()` with `secrets.token_urlsafe(32)`.** Delete the
   counter, the date arithmetic, the `SECRET_KEY` mixing and the SHA-1 — not as
   an aesthetic preference, but because leaving any of it invites the reader to
   believe it is doing something.

2. **Widen `PendingUser.key`** to hold a 43-character token, with a migration.
   Prefer a length with headroom over one sized exactly to today's token.

3. **Do not invalidate keys already issued.** There is one pending user at the
   time of writing and a one-day expiry, so the window is small — but a widened
   column accepts the old short keys unchanged, and `purge_expired()` clears them
   within a day. Confirm an in-flight registration still completes rather than
   assuming it.

4. **Use `secrets.compare_digest` in `accounts/views.py:118`.**

5. **Provide the token helper somewhere task 05 can reuse it** rather than
   leaving it as a private method on `PendingUserManager`. A module-level
   function in `accounts` or `core` is enough; the point is that task 05 imports
   it instead of writing its own.

6. **Update `generate_registration_code()`** to `secrets.choice` and
   `secrets.randbelow`, and drop the now-unused `random` import from
   `accounts/forms.py` if nothing else there uses it.

7. **Leave `wiki/middleware.py` alone**, per the background, and note in the
   commit message that Step 19 covers it — so the next person to grep for
   `random.sample` finds the reasoning rather than an apparent oversight.

8. **Do not change the URL shape.** `accounts-register_confirm` takes
   `username` and `key`; a longer key changes the URL's length, not its
   structure. Confirm the route still matches — the token is URL-safe base64,
   which includes `-` and `_`.

## Dependencies
- None. **Should land before task 05**, which will import the helper.

## Implementation Approach
1. Write a test asserting the generated key is at least 32 characters and that
   two successive keys differ; watch it fail against the current 20-character
   implementation.
2. Add the module-level token helper using `secrets.token_urlsafe(32)`.
3. Point `create_pending_user` at it; delete `_make_key()` and its now-unused
   imports (`random`, `base64`, `hashlib`, `string`, `datetime` — check each).
4. Add the migration widening `PendingUser.key`.
5. Switch the comparison to `secrets.compare_digest`.
6. Update `generate_registration_code()`.
7. Exercise a full registration end-to-end in the container: register, read the
   emailed link, follow it, confirm the account is created.
8. Run the suite under `docker_test`, plus `check` and the gate.

## Acceptance Criteria
- **Given** the new helper
  **Then** it returns a URL-safe token of at least 32 characters, drawn from
  `secrets`, and two calls never return the same value
- **Given** that test
  **When** run against the unmodified `_make_key()`
  **Then** it **fails** — mutation-verified
- **Given** a full registration performed in the container
  **Then** the emailed confirmation link works and the account is created
- **Given** a `PendingUser` row holding a legacy 20-character key
  **Then** its confirmation link still works after the migration
- **Given** a wrong key
  **Then** confirmation is refused, and the comparison uses
  `secrets.compare_digest`
- **Given** the tree grepped for `random.sample`
  **Then** the only remaining hit is `wiki/middleware.py`, which Step 19 deletes
- **Given** `accounts/models.py` and `accounts/forms.py`
  **Then** neither imports `random`, and no import is left unused
- **Given** the suite under `docker_test`, `check`, `check --deploy` and
  `tools/deprecation_gate.sh`
  **Then** all are clean

## Metadata
- **Complexity**: Low — the change is small; the migration and the
  legacy-key-compatibility check are what make it more than a one-liner
- **Labels**: Accounts, Security, Tokens, Migration, Step 16
- **Required Skills**: Python `secrets`, Django migrations on a `CharField`
  width, reasoning honestly about what a weak PRNG does and does not expose
- **Decision**: Brian, 2026-08-16 — modernize registration and reuse for email
  change
