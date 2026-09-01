# Task: Restore the Calendar Links to the Site Navigation

## Description
Put the Calendar link back into the site's two live base templates. It was
removed in 2023 when the sync was broken and has kept `/calendar/` unreachable
from anywhere on the site since. This is the last task in Step 18 and it is
gated on task 03: do not advertise the calendar until the pipeline is proven.

## Background

### The link was removed in response to the outage, not before it
`7073a406`, **2023-03-19**, "Remove links to calendar & member map", deleted
`<li><a href="{% url 'gcalendar-index' %}">Calendar</a></li>` from both base
templates. Brian removed it deliberately once the sync had stopped working.

**The dates matter, because they rule out a tempting causal story.** The last
event of any kind was submitted **2023-01-12** — *two months before* the links
came out. So the removal did not cause the collapse in submissions; the sync
failure did, and the removal is what has kept the page unreachable since. Any
write-up claiming members stopped submitting because they could not find the
page has the order backwards.

### Both templates are live
This is not a one-line change to a legacy file:

| Template | Templates extending it |
|---|---|
| `sg101/templates/base.html` | **26** — the forums, flatpages |
| `sg101/templates/v3/base.html` | **55** |

The forums, the busiest part of the site, still run on the older design. Both
need the link.

### DO NOT revert the commit
`7073a406` removed **two** links: the calendar's and the Member Map's. The
`membermap` app was **pruned in Step 4** and `membermap-index` no longer exists
as a URL name. Reverting the commit — or copying its diff in reverse — puts
`{% url 'membermap-index' %}` back into both base templates, and
`NoReverseMatch` is raised **at render time**, not at import. That would 500
every page on the site that extends either base, which is all of them, and no
test that only checks imports would catch it.

Restore the calendar link by hand. The Member Map's removal is correct and
permanent.

That commit also bumped the copyright year (2018 → 2023) in both files. Leave
that alone; it is unrelated.

### Where each link goes
From the diff of `7073a406`:

- `sg101/templates/base.html` — in the main nav list, between **Submit News**
  and **Contact**.
- `sg101/templates/v3/base.html` — in the **Surf Music** dropdown, above
  **Downloads**.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R27)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 18`
- `git show 7073a406` — the removal, for the exact positions

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add `<li><a href="{% url 'gcalendar-index' %}">Calendar</a></li>` to
   `sg101/templates/base.html`, in its original position in the nav list.
2. Add the same to `sg101/templates/v3/base.html`, in the **Surf Music**
   dropdown, in its original position.
3. **Do not restore the Member Map link** in either file. `membermap-index` does
   not exist.
4. Match each file's surrounding indentation and markup style. The two navs are
   structured differently.
5. Add a test that both base templates render with the calendar link present and
   that it points at `gcalendar-index`. A rendering test is what catches a
   `NoReverseMatch`; an import test is not.
6. Confirm no other navigation surface still needs it — check the footer blocks
   and any sitemap or menu partial.

## Dependencies
- **Task 03 must be complete and its end-to-end run successful.** Restoring the
  link before the sync works advertises a submission form whose output goes into
  a queue nobody drains — which is the state that produced the 32 stranded
  events.
- `gcalendar-index` is already routed (`gcalendar/urls.py:10`) and has never
  stopped working; only the links to it were removed.

## Implementation Approach
1. Read `git show 7073a406` for the exact original placement in both files.
2. Add the calendar link to each by hand. Do not revert or reverse-apply.
3. Write the render tests, and confirm they fail before the templates are edited.
4. Render both designs in the running stack — a forums page for `base.html`, a
   V3 page for `v3/base.html` — and click through to `/calendar/`.
5. Grep for `membermap` afterwards to prove nothing reintroduced it.

## Acceptance Criteria

1. **The link is back in both designs**
   - Given a page extending `base.html` and a page extending `v3/base.html`
   - When each is rendered
   - Then both contain a Calendar link resolving to `gcalendar-index`

2. **The Member Map link is not restored**
   - Given the working tree after this task
   - When it is grepped for `membermap`
   - Then no template references it, and no `{% url 'membermap-index' %}` exists

3. **Every page still renders**
   - Given the full test suite, which exercises views across both designs
   - When it is run
   - Then it passes with no `NoReverseMatch`

4. **The route works from the link**
   - Given the running stack
   - When the Calendar link is followed from a forums page and from a V3 page
   - Then `/calendar/` returns 200 and the embedded calendar renders

5. **The tests have been mutation-verified**
   - Given the new render tests
   - When the link is removed from each template in turn
   - Then the corresponding test fails

## Metadata
- **Complexity**: Low
- **Labels**: gcalendar, navigation, templates, both designs
- **Required Skills**: Django templates, testing
