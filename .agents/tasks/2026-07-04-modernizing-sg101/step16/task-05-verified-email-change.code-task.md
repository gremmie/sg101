# Task: Verify Email Address Changes (the Step 11 REVISIT)

## Description
`/profile/edit/` lets any member set their email address to anything at all —
an address already used by another account, or one they do not control — with no
confirmation and no uniqueness check. Registration goes to real trouble to
verify an address (`PendingUser` + emailed key + confirmation link) and this
discards that guarantee the next day.

Flagged during Step 11 task 02 on 2026-07-25 and scheduled here. **This step
gives it a second, sharper justification that did not exist when it was
deferred:** after cutover, unverified addresses are no longer just wrong data —
they are bounces charged against a shared IP pool, and Postmark suspends
accounts over bounce rates. An unverified-address feature is now a
deliverability liability, not only a correctness one.

## Background

### The code
`bio/forms.py:21-26`, in full:

```python
class EditUserForm(forms.ModelForm):
    """Form for editing the fields of the User model."""
    email = forms.EmailField(label='Email', required=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
```

No `clean_email`. `User.email` carries no `unique=True`. Nothing else guards the
path.

### What it is not
**Not an account-takeover path.** Login is by username, and a password reset
mails its link *to* the address on file, so claiming someone else's address
yields nothing readable. This should not be written up as a vulnerability.

### The three real harms
1. **You can publish someone else's address.** With `hide_email` unticked the
   address is rendered on the profile page, the member list, and every forum
   post — `bio/view_profile.html:87`, `bio/members.html:48`,
   `forums/display_post.html:25`.
2. **It damages the other account's recovery**, which is how the duplicate pairs
   below became unrecoverable.
3. **A typo silently costs you your own password reset** — no error, no mail,
   no indication anything is wrong until you need it.

### The trap — measured again 2026-08-16, unchanged
```sql
SELECT count(*), sum(n) FROM (
  SELECT lower(email), count(*) n FROM auth_user
  WHERE email <> '' GROUP BY 1 HAVING count(*) > 1) x;
→ 13 groups, 26 accounts
```

**A naive uniqueness check must reject only *changing to* a duplicate.** Adding
`exclude(pk=self.instance.pk)` alone would lock all **26** members of those
existing pairs out of saving *any* profile edit — forever, including edits that
never touch the email field. The validation must fire only when the submitted
address differs from the instance's current one. See
`research/collation-audit.md` for the pairs and their origin.

`accounts/forms.py:ForgotUsernameForm` already handles the duplicates correctly
and its comment explains why — read it before writing the check; it is the same
constraint seen from the recovery side.

### The machinery to reuse
Registration's confirm-link flow is the right model: `PendingUser` holds the
change, an emailed key confirms it, `accounts-register_confirm` completes it.
Mirror that shape for email changes.

**Import the token helper from task 08; do not write another one.** An earlier
version of this task warned against copying
`PendingUserManager._make_key()` — which mints keys from the Mersenne Twister —
and left modernizing registration as an open question. Brian settled it on
2026-08-16: task 08 replaces that helper with `secrets.token_urlsafe(32)` and
exposes it at module level precisely so this task can reuse it. **Task 08 lands
first.**

### The pending state is its own model — decided 2026-08-19

```python
class PendingEmailChange(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    new_email = models.EmailField()
    key = models.CharField(max_length=64)
    date_requested = models.DateTimeField(default=timezone.now, db_index=True)
```

**In `accounts`, beside `PendingUser`**, not in `bio`. It reuses that model's
manager idiom and `accounts.utils.make_confirmation_token()`, and the
confirmation view belongs next to `register_confirm`. `bio` currently imports
nothing from `accounts`; this is the first edge and it points the right way —
profile editing depending on account-identity machinery, not the reverse.

**`OneToOneField` is load-bearing.** It enforces at most one pending change per
user in the database, which *is* the last-request-wins rule: a second request
overwrites the row rather than racing with it. Existence of the row is the
entire pending state, so the template condition is `{% if pending_change %}` and
nothing has to encode "pending" as a flag that can disagree with the data.

`max_length=64` and the indexed date match what task 08 settled for
`PendingUser.key`, so the token helper and a `purge_expired()`-shaped sweep carry
over unchanged.

**Rejected: fields on `bio.UserProfile`.** Three reasons, the middle one specific
to this codebase:

- It is already a 20-field hot table, read on every profile view, member-list row
  and forum post, for columns that are non-null a few hours a year.
- **It is a search document.** `search/receivers.py:132` queues a Celery reindex
  on `UserProfile` writes, so every change request *and* every expiry sweep would
  dirty the profile row and reindex data that is not indexed.
- A sweep cannot `.delete()` a set of columns. `PendingUser.purge_expired()` is a
  `.delete()`, and requirement 3 says to follow it; nulling fields is a different
  and messier shape that re-triggers the reindex above.

### Fix order, from the plan
Verify on change > uniqueness check > don't display an unverified address.

### The UI, decided 2026-08-19

Requirement 7 as originally written covers *other people's* views. What the owner
sees was unspecified, and it is the actual interface.

- **On save, a flash**: `messages.success` telling them the change is pending and
  to confirm from the new address. `bio/views.py:edit_profile` already uses the
  `messages` idiom, so this is the existing pattern.
- **And a persistent notice**, because a flash dies on the next page load while
  the pending state does not. The email field keeps showing the **verified**
  address; below it a block names the pending one, marked as awaiting
  confirmation, with **resend** and **cancel**.
- **Cancel is not a nicety.** Without it a typo'd address leaves the member
  waiting out the expiry with no recourse and no way to retry to the right
  address.
- **Two small confirm templates** mirroring `register_success.html` /
  `register_failure.html` rather than reusing them: different wording, and reuse
  would couple two flows that will drift.
- **The courtesy mail to the old address carries no action link.** The background
  above establishes there is no takeover path, so a "this wasn't me" link would
  add attack surface to answer a risk that does not exist. It names a contact
  instead.

**Both use Foundation callouts, and the flash half is already free.** Checked
2026-08-19 rather than assumed: `sg101/settings/base.py:204` maps Django's
message constants onto Foundation's callout classes (`ERROR → alert`,
`INFO → primary`, and so on), and `core/message_list.html` renders
`<div class="{{ message.tags }} callout">`. So `messages.success(...)` emits a
`success callout` with no template work. 40 templates already use callouts and
`main.scss` includes the component.

**The persistent notice is the part that needs markup**, since it is model state
rather than a message — hand-written into `edit_profile.html`. Start from
`warning callout`: the state is "action still required from you", not success.
Brian's call, and worth revisiting against the rendered page rather than settled
here.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` —
  Step 16's REVISIT paragraph
- `research/collation-audit.md` — the 13 pairs and how they arose
- `accounts/models.py:37-89` and `accounts/forms.py:195-235` — the machinery to
  mirror
- `step16/task-04-email-story-reply-to.code-task.md` — the transitive
  consequence of unverified addresses

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Make an email change pending until confirmed.** Saving the profile stores
   the requested address somewhere other than `User.email`, emails a
   confirmation link to the **new** address, and only writes `User.email` when
   that link is followed. The old address stays live until then.

2. **Notify the old address that a change was requested.** A one-line courtesy
   mail to the outgoing address is the only signal a member gets if someone else
   changes their address, and it costs one email.

3. **Expire pending changes**, following `PendingUser.purge_expired()`'s
   one-day precedent. Decide whether expiry is swept by the existing cleanup
   task or evaluated on use; the sweep is more consistent with the codebase.

4. **Reject changing *to* an address another account already uses**, matching
   case-insensitively (`email__iexact`) since the duplicates arose partly from
   case and collation.

5. **The uniqueness check must fire only when the address actually changes.**
   Compare against `self.instance.email` first and skip validation entirely when
   unchanged. **Verify explicitly that a member in one of the 13 duplicate pairs
   can still save a profile edit** — this is the specific regression the check
   invites, and it must have its own test.

6. **Do not add `unique=True` to `User.email` in this task.** The 26 existing
   rows would make the migration fail, and reconciling them is a data question
   with a human in the loop, not a schema question. Form-level validation is the
   right scope here; note the model constraint as a follow-on once the data is
   clean.

7. **Do not display an unverified address.** Until confirmation, the profile
   page, member list and forum posts should show the previously verified
   address, not the pending one.

   **This is a verification, not a change — consequence of the model decision
   above (2026-08-19).** The pending address never enters `User.email`, so those
   three templates already render the verified address and need no edit. Confirm
   it by test rather than by reading them; the criterion stays because the
   *property* still has to hold, not because there is work to do.

8. **Reuse `core.functions.send_mail`.** It is the wrapper every other path uses
   and the one task 02 makes reliable.

9. **Generate the confirmation key with task 08's shared helper**, and compare it
   with `secrets.compare_digest`. Do not add a second token implementation.

10. **Consider the interaction with a stale list.** Members whose addresses are
    already dead cannot confirm a change, which is correct behaviour — but it
    means a member with a dead address on file can no longer update it
    themselves. Make sure the failure is legible on screen, and that an admin
    path exists, rather than leaving them stuck with no explanation.

    **Resolved 2026-08-19.** The admin path already exists — Django's stock
    `UserAdmin` edits `auth.User.email` directly, and that write bypasses this
    flow entirely. So the work here is only the on-screen half: the pending
    notice must say plainly that confirmation goes to the new address, and point
    at the contact form for a member who cannot reach it. Do not build a second
    admin surface.

## Dependencies
- **Task 08** — the shared `secrets` token helper. Hard prerequisite.
- Independent of the provider swap; can land before or after.
- **Landing it before the first bulk send is preferable**, so unverified
  addresses stop accumulating before Postmark starts measuring bounce rates.

## Implementation Approach
1. Write the failing tests first: a change to a duplicate address is rejected; a
   change to a fresh address does not take effect until confirmed; a member in a
   duplicate pair can still save unrelated profile edits.
2. Add the pending-change model or reuse `PendingUser`'s shape, with a
   `secrets`-generated key.
3. Add `clean_email` to `EditUserForm` with the changed-only guard.
4. Add the confirmation view and URL, mirroring `accounts-register_confirm`.
5. Add the notification to the old address.
6. Wire expiry into the cleanup task.
7. Audit the three display templates for unverified addresses.
8. Run the suite under `docker_test`.

## Acceptance Criteria
- **Given** a member submitting an address another account already uses
  (any case)
  **Then** the form rejects it with a clear error, and `User.email` is unchanged
- **Given** a member submitting a fresh address
  **Then** `User.email` is **unchanged** until the emailed link is followed, and
  a confirmation mail is sent to the new address
- **Given** the confirmation link is followed within the expiry window
  **Then** `User.email` becomes the new address and the pending record is gone
- **Given** the link is followed after expiry
  **Then** it is refused with a legible message and `User.email` is unchanged
- **Given** a member who is one of the **26 accounts in the 13 duplicate pairs**
  **When** they save a profile edit that does not touch the email field
  **Then** it **succeeds** — this test must exist and must fail against a naive
  `exclude(pk=…)` implementation
- **Given** a pending, unconfirmed address
  **Then** the profile page, member list and forum posts show the previously
  verified address — asserted by test, since the model decision means those
  templates are unchanged and nothing else would catch a regression
- **Given** a member who has just requested a change
  **Then** the edit page shows the **verified** address in the email field and a
  persistent notice naming the pending one, and that notice survives a page
  reload — a flash alone does not satisfy this
- **Given** a member with a pending change who cancels it
  **Then** the pending record is gone, `User.email` is unchanged, and they can
  immediately request a different address
- **Given** a member who requests a second change while one is pending
  **Then** the first is replaced rather than duplicated, and the old address is
  notified again
- **Given** the old address
  **Then** it receives notification that a change was requested
- **Given** the new confirmation key
  **Then** it is generated by `secrets`, not `random`
- **Given** the suite under `docker_test`
  **Then** it is green

## Metadata
- **Complexity**: Medium — small surface, but the duplicate-pair constraint makes
  the obvious implementation wrong
- **Labels**: Accounts, Email Verification, Data Integrity, Deliverability, Step 16
- **Required Skills**: Django `ModelForm` validation, confirmation-token flows,
  `secrets`, reading an existing pattern before mirroring it
- **Origin**: flagged Step 11 task 02, 2026-07-25; duplicate count re-measured
  2026-08-16 (13 groups / 26 accounts, unchanged)
