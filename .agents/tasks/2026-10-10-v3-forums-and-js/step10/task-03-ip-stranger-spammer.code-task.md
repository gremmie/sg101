# Task: The post IP, stranger and spammer pages on V3, and no forum template on `base.html`

## Description
Move the four short moderator pages, `post_ip.html`, `stranger.html`,
`spammer.html` and `spammer_nailed.html`, from `base.html` to
`v3/base.html`. With them converted, no forum template extends `base.html`;
replace the step 9 tests that relied on an old forum page with a static
check that none does.

## Background
**The views**, all login required:

| View | URL | Template |
|---|---|---|
| `post_ip_info` (`forums/views/main.py`) | `/forums/post/ip/<post_id>/` | `post_ip.html` |
| `spammer` (`forums/views/spam.py`) | `/forums/spammer/<post_id>/` | `spammer.html` |
| `spammer_nailed` (`spam.py`) | `/forums/spammer/nailed/<spammer_id>/` | `spammer_nailed.html` |
| `stranger` (`spam.py`) | `/forums/stranger/<post_id>/` | `stranger.html` |

**The pages are text and one button.** `stranger` and `spammer` each have a
confirmation paragraph and a POST button when the moderator may act, and a
sentence for each refusal (no longer a stranger; no permission), then "Return
to the post". `spammer_nailed` reports success or failure. `post_ip` names the
post, its author and IP, and lists every user who has posted from that IP,
each with a link to their posts. Keep the wording, except as below.

**Make the spammer button look drastic.** It deactivates an account and
deletes all its posts and comments; the page already says so in bold. A
`button alert` (Foundation's red) for Deactivate, and a primary button for
promoting a stranger, are the obvious styles; show Brian.

**The whois link: measure, then ask.** `post_ip` links the IP to
`http://www.dnsstuff.com/tools/whois/?ip=…`. Check what that URL does today
(with a documentation address from RFC 5737, never a real member's IP, and
nothing quoted into the repository), and bring Brian the result with
options: keep it, point it at another whois service, or drop the link.
`spammer_nailed` says "his/her account"; leave the wording unless Brian asks.

**No forum template on `base.html`.** After tasks 01 and 02 and this one,
`grep "extends 'base.html'" sg101/templates/forums/` finds nothing.
`test_old_pages_keep_the_old_fragments` and
`test_unconverted_pages_stay_on_the_old_design` (`test_views.py`) have no
old forum page left to check: delete them, and add a test that no template
under `sg101/templates/forums/` extends `base.html`. The old fragment
variants stay for step 12.

**Existing tests**: `SpammerToolTests` (`test_moderation.py`): the spammer
page renders for a moderator, deactivating a stranger, refusing a non-stranger
and a non-moderator, the nailed page, and promoting a stranger. Keep them
passing. `post_ip_info` has no view test; add one (renders for a
moderator, lists the IP's users, and whatever it does for a member, as
today).

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 10)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 8 task 04: the confirmation pages)
- `antispam/utils.py` (`deactivate_spammer`, what the spammer button runs)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. The four templates extend `v3/base.html`; their four views pass
   `'V3_DESIGN': True`.
2. Each page keeps its wording, its branches and its POST.
3. The spammer button is styled as a drastic action.
4. A test shows no template in `sg101/templates/forums/` extends
   `base.html`; the two step 9 old-page tests are deleted.
5. `post_ip_info` has a view test.

## Dependencies
- Tasks 01 and 02: the other old forum templates.

## Implementation Approach
1. Measure the whois link and put the options to Brian.
2. Write the tests first: each page on `v3/base.html`; the refusal branches
   still render their sentences; `post_ip` lists the IP's users; the static
   no-`base.html` check. Watch them fail.
3. Convert the four templates and their views; delete the two old tests.
4. Check each page on dev at 360 and 1280, with no writes: the spammer and
   stranger pages are only opened, not submitted.
5. Run the forums tests, then the full suite once, under the gate.
6. Mutation-check each new test, restore byte-identical, and leave the work
   unstaged for review.

## Acceptance Criteria

1. **All four pages are V3**
   - Given a moderator and a stranger's post
   - When they open the IP, stranger, spammer and nailed pages
   - Then each extends `v3/base.html`

2. **The tools still act**
   - Given a stranger's post
   - When the moderator promotes the stranger, or deactivates a spammer
   - Then the account changes as today and the confirmation page follows

3. **Refusals still explain themselves**
   - Given a member who isn't a stranger, or a moderator of another forum
   - When the pages are opened
   - Then the matching sentence is shown and there is no button

4. **No forum page is on the old design**
   - Given the templates after this task
   - When the static check runs
   - Then no template under `sg101/templates/forums/` extends `base.html`

5. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Low
- **Labels**: forums, templates, V3 design, moderation, antispam
- **Required Skills**: Django views and templates, Foundation 6
