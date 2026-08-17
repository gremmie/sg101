# Task: Remove the "Email This Story to a Friend" Feature

## Description
Delete `news.views.email_story` and everything that exists to serve it: the
view, its thanks view, the form, two URLs, two templates, two template links and
three tests. **Brian's call, 2026-08-16** — the feature is a 2008-era affordance
that social sharing displaced, and his judgement is that nobody uses it.

This supersedes an earlier version of this task that hardened the feature
instead — removing a user-supplied `Reply-To` and adding a rate limit. Deletion
is strictly better: it removes the abuse surface rather than narrowing it, and
it lands before Postmark ever sees traffic from this domain.

## Background

### Why this is a Step 16 task rather than a Step 19 prune
Ordinarily a dead-feature deletion belongs on Step 19's prune list. This one is
here because of what it would do on a shared IP pool.

`email_story` is **the only path in the site that sends to an arbitrary
external recipient.** Three properties combine badly:

1. **The recipient is unbounded** — any address on the internet, typed into a
   form, with no relationship to the site required.
2. **No CAPTCHA and no rate limit.** The contact form has a honeypot and
   reCAPTCHA (`contact/forms.py:34-56`); this view has neither, and a member can
   drive it in a loop.
3. **The `Reply-To` is attacker-chooseable, transitively.**
   `reply_to=request.user.email` (`news/views.py:246`) looks trustworthy — it is
   the account's registered address, not form input. But `/profile/edit/` lets
   any member set that to an arbitrary unverified address, which is exactly what
   task 05 fixes.

`@login_required` is the only real control, and registration is open. On a
dedicated IP the blast radius was a domain Brian already controls. On Postmark's
shared pool the cost lands on every other sender, and the provider's response to
abuse is account suspension — which would take registration confirmations and
password resets down with it.

Deleting it before cutover means the first messages Postmark ever sees from
`surfguitar101.com` cannot come from this path.

### Usage was never measurable
Stated plainly because it is the basis of the decision: **there is no send log,
no counter and no model recording invocations**, so usage could not be measured
from the snapshot. The call is Brian's judgement, not a measurement, and is
recorded as such. (If item 3 of the 2026-08-16 discussion — per-send email
logging — had existed, this would have been a data question.)

### The full surface, enumerated 2026-08-16
- `news/views.py:224-253` — `email_story`
- `news/views.py:261-266` — `email_thanks`. Note it renders
  `news/send_story.html`, not a thanks template; there is no `email_thanks.html`
  in the tree. A latent oddity the deletion moots.
- `news/forms.py:52-61` — `SendStoryForm`
- `news/urls.py:17-19` — `news-email_story` and `news-email_thanks`
- `sg101/templates/news/send_story.html`
- `sg101/templates/news/send_story_email.txt`
- `sg101/templates/news/story.html:51` — the link
- `sg101/templates/news/story_summary.html:76` — the link
- `news/tests/test_display_views.py:121-135` — three tests
  (`test_email_story_requires_login`, `test_email_story_form_renders`,
  `test_email_story_sends_mail`)

### Contact form is unaffected
`contact/forms.py:75` also sets a `Reply-To` from user input and **stays exactly
as it is.** Its `recipient_list` is `settings.MANAGERS`, so it can only ever mail
Brian; an arbitrary `Reply-To` on a message to your own inbox is the standard
contact-form pattern and is what makes the reply button work. There is no third
party to abuse. Do not touch it.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `step15/task-01-retire-ssl-images.code-task.md` — the house pattern for a
  clean deletion with a moving test count
- `step16/task-05-verified-email-change.code-task.md` — the transitive half of
  the `Reply-To` problem, fixed independently
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` —
  Step 19's prune list, for context on why this one is not there

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Delete the whole surface listed in the background** — view, thanks view,
   form, both URLs, both templates, both template links, three tests.

2. **Remove imports left unused in `news/views.py`.** `send_mail` and
   `GPP_NO_REPLY_EMAIL` exist in that module only for this feature; check
   `get_full_name` and `render_to_string`, which may have other callers there.
   Do not leave a dangling import, and do not remove one that is still used.

3. **Grep for `news-email_story` and `news-email_thanks` across the whole tree**
   before declaring it done, templates included. A `{% url %}` referencing a
   removed name is a 500 at render time, not an import error, so nothing else
   will catch it.

4. **Expect the test count to move 866 → 863** and say so in the commit message.
   This project tracks that number rung by rung; an unexplained change in it
   costs someone an investigation.

5. **This is its own commit.** It is a clean deletion and should be legible as
   one, separate from the settings and backend work in tasks 01 and 02.

6. **Leave `contact/forms.py` untouched.**

7. **Do not add a redirect or a tombstone URL.** The links are gone from the two
   templates, so the only inbound traffic would be a stale bookmark or a
   crawler; a 404 is the correct answer.

## Dependencies
- None. Independent of every other task in this step, and **preferably lands
  before cutover** so the path cannot send through Postmark even once.

## Implementation Approach
1. Grep the tree for both URL names and for `email_story` / `SendStoryForm` to
   confirm the surface list is complete.
2. Delete views, form, URLs, templates and template links.
3. Delete the three tests.
4. Clean up now-unused imports; run the linter.
5. Run the suite under `docker_test` and confirm 863.
6. Load a news story page and a story summary page and confirm they render with
   no dangling link.

## Acceptance Criteria
- **Given** the tree after the change
  **When** grepped for `email_story`, `email_thanks`, `SendStoryForm`,
  `news-email_story`, `news-email_thanks`, `send_story.html` and
  `send_story_email.txt`
  **Then** there are no matches outside `.agents/`
- **Given** the suite under `docker_test`
  **Then** it is green at **863 tests**, down exactly three
- **Given** a news story page and a story summary page
  **When** rendered
  **Then** both render without error and show no email-a-friend link
- **Given** `news/views.py`
  **Then** it has no unused imports and the linter is clean
- **Given** `contact/forms.py`
  **Then** it is byte-identical to before this task
- **Given** `check`, `check --deploy` and `tools/deprecation_gate.sh`
  **Then** all are clean

## Metadata
- **Complexity**: Low
- **Labels**: News, Deletion, Abuse Prevention, Deliverability, Step 16
- **Required Skills**: Django URL/template/view removal, tracing a feature's full
  surface before deleting it
- **Decision**: Brian, 2026-08-16 — remove rather than harden
