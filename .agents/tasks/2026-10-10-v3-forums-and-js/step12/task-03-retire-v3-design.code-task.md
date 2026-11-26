# Task: Retire the `V3_DESIGN` flag

## Description
With `base.html` gone, nothing renders the old variants of the shared tags.
Make the eight tags render their `v3/` templates unconditionally, delete the
ten old variant templates, and take the flag out of every file that sets it.
This is its own commit (design §4.5 item 6). It touches nearly every app, and
the change is mechanical.

## Background
**Measured on `main` at `278b51d4`.** The design's counts (eight tags, eight
templates, 21 files) predate the forum releases.

**The eight tags and their old templates:**

| Tag | Module | Old template deleted |
|---|---|---|
| `latest_contests_block` | `contests/templatetags/contest_tags.py` | `contests/latest_contests_block_tag.html` |
| `birthday_block` | `core/templatetags/core_tags.py` | `core/birthday_block.html` |
| `countdown_events` | `countdown/templatetags/countdown_tags.py` | `countdown/countdown_tag.html` |
| `monthly_goal` | `donations/templatetags/donations_tags.py` | `donations/monthly_goal_tag.html` |
| `unread_messages` | `messages/templatetags/messages_tags.py` | `messages/unread_messages_tag.html` |
| `latest_poll_block` | `polls/templatetags/poll_tags.py` | `polls/latest_poll_block_tag.html` |
| `photo_of_the_day` | `potd/templatetags/potd_tags.py` | `potd/potd_block.html` |
| `render_fragment`, behind three forum tags | `forums/templatetags/forum_tags.py` | `forums/last_post_info.html`, `forums/navigation_tag.html`, `forums/topic_icons_tag.html` |

`render_fragment`'s docstring explains why the fragments had two variants.
Once there's one, consider whether `render_fragment` still earns its place
or the three tags should name their `forums/v3/` templates directly. Choose
the simpler. Keep the `v3/` paths as they are: moving templates out of
`v3/` directories is not this task.

**`news/templatetags/news_tags.py` puts `'V3_DESIGN': True` into its own
context.** Find out what it was for (likely a fragment that read the flag),
and remove it.

**Where the flag is set: 25 non-test Python files, 108 lines.**
`accounts/urls.py` (`extra_context` on auth views), and the views in
`accounts`, `antispam`, `bandmap`, `bio`, `contact`, `contests`, `core`,
`donations`, `downloads`, `forums/views/{favorites,main,spam,subscriptions}`,
`gcalendar`, `messages`, `news`, `podcast`, `polls`, `potd`, `search`,
`sg101/views.py`, `user_photos`, `weblinks`, `ygroup`. Read each before
editing: a context dict left empty, or an `extra_context` left with nothing
in it, should go too, not stay as `{}`. No template reads the flag
(`grep -rn V3_DESIGN sg101/templates` finds nothing).

**Tests that pass the flag:** `core/tests/templatetags/test_core_tags.py`
(`test_render_v3`), `contests/tests/test_contest_tags.py`, and the forum tests
in `forums/tests/test_views.py` and `test_moderation.py`. Fold them into
plain renders. A test of the old variant goes, and a test of the V3 variant
stays without the flag. Step 10 task 03's tests check for
`messages/v3/unread_messages_tag.html` to prove the flag was set (`STATUS.md`,
step 10 task 03). Find those and decide whether they still test anything.

**`AGENTS.md`** says `base.html` and `V3_DESIGN` are "retired together".
Rewrite that bullet for what's true afterwards. `.agents/summary/` is a dated
snapshot: leave it.

**`git grep V3_DESIGN`**, outside `.agents/` and `archive/`, finds nothing
afterwards. Extend task 01's static check to say so. If a check under
`core/tests/` can't run `git` (the test image may have no `.git`), walk
the source tree from `settings.BASE_DIR` instead, skipping `.agents/`,
`archive/` and `node_modules/`.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.5, item 6)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 12, the `V3_DESIGN` bullets)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 6 task 01: why the forum fragments got `v3/` variants chosen on the flag)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Each of the eight tags renders its `v3/` template with no condition.
2. The ten old variant templates are deleted, each shown unreferenced once
   the tags no longer name them.
3. No Python file sets `V3_DESIGN`, and no context dict or `extra_context`
   is left empty because of its removal.
4. The static check asserts that `V3_DESIGN` appears nowhere in the source.
5. The work is one commit, separate from tasks 01 and 02.

## Dependencies
- Tasks 01 and 02: `base.html` gone, the URL walk and static check in place.

## Implementation Approach
1. Extend the static check for `V3_DESIGN` and watch it fail.
2. Change the eight tags, then delete the old templates. Rendering any
   page without the flag should now give the V3 sidebar and header. A
   test of one tag rendered from a bare `Context()` shows it.
3. Remove the flag from the views and `accounts/urls.py`, file by file, and
   update the tests.
4. Run each touched app's tests against the running stack, one run at a
   time, then the full suite once under the gate. Then run the browser tests
   in step 3's set: the header, menu and Orbit.
5. Mutation-check (restore an old-variant branch in one tag, and the bare
   `Context()` test fails), restore byte-identical, and leave the work
   unstaged for review.

## Acceptance Criteria

1. **The shared tags render V3 without being told to**
   - Given a template using one of the eight tags, rendered with a bare context
   - When it renders
   - Then the output is the `v3/` template's markup

2. **The flag is gone**
   - Given the source outside the planning record and the archive
   - When the static check runs
   - Then `V3_DESIGN` is found nowhere and the check passes

3. **Every page still renders on the V3 chrome**
   - Given the flag removed from every view
   - When the URL walk, the full suite under the gate and step 3's browser tests run
   - Then they pass

4. **One commit**
   - Given the step's history
   - When it is read
   - Then the flag's removal is a commit of its own

## Metadata
- **Complexity**: Medium
- **Labels**: V3 design, template tags, removal, cleanup
- **Required Skills**: Django template tags and views, mechanical refactoring
