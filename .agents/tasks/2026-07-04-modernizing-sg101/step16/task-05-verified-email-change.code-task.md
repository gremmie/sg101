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

### Fix order, from the plan
Verify on change > uniqueness check > don't display an unverified address.

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

8. **Reuse `core.functions.send_mail`.** It is the wrapper every other path uses
   and the one task 02 makes reliable.

9. **Generate the confirmation key with task 08's shared helper**, and compare it
   with `secrets.compare_digest`. Do not add a second token implementation.

10. **Consider the interaction with a stale list.** Members whose addresses are
    already dead cannot confirm a change, which is correct behaviour — but it
    means a member with a dead address on file can no longer update it
    themselves. Make sure the failure is legible on screen, and that an admin
    path exists, rather than leaving them stuck with no explanation.

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
  verified address
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
