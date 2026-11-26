# Task: Retire `base.html`

## Description
Put two safety nets in place, then delete the old design's base template and
the files only it loads. The nets are a test that renders every named URL
taking no arguments, and a static check that no template extends `base.html`.
Then update the tests that still describe two designs.

## Background
**Nothing extends `base.html` now** (measured on `main` at `278b51d4`). Step
11 removed the shoutbox, the last thing that did. `git grep "extends
['\"]base.html"` finds only `tools/ssg101/templates/home.html`, which extends
that tool's own `tools/ssg101/templates/base.html`. **`tools/ssg101/` is a
standalone tool with its own template directory: leave it alone.**
`fixed/base.html`, `store/base.html`, `news/base.html`, `podcast/base.html`,
`weblinks/base.html` and `admin/base.html` are different templates and stay.

**What `base.html` loads, and whether anything else does:**

| Asset | Used elsewhere? |
|---|---|
| `navbar.html` (include) | no. Only `accounts/tests/test_views.py` names it, in a docstring |
| `css/blueprint/` (screen, print, ie) | no |
| `css/base.css` | no |
| `themes/kds/sgLogo.png` | no |
| `{% script_tags "jquery" %}` → the `jquery` entry in `GPP_THIRD_PARTY_JS` (Google CDN jQuery 1.11.1) | no other template asks for `jquery` |
| `js/jquery.cycle.all3.0.3.js` | **yes**: `home.html`. Keep |
| `core/mp3comp_block.html`, `images/sg101-celebrating.jpg`, `logos/*` | **yes**: `v3/base.html`. Keep |
| `icons/new.png` | **yes**: `forums/topic_icons_tag.html`, an old variant task 03 deletes. Task 02 rechecks it |
| the `potd`, `poll`, `contest`, `donations`, `core`, `countdown` tags | yes, from `v3/base.html` |

The `script_tags`, `css_tags` and `js_tags` tags themselves stay: several V3
pages use them for `jquery-ui`. Only the `jquery` entry goes.
`core/tests/templatetags/test_script_tags.py` asks for `jquery`, so update it.

**Tests that describe two designs:**

- `core/tests/test_navigation.py`: the module docstring says "the forums
  wear `base.html`", and `test_the_forums_design_has_no_wiki_link`'s docstring
  says the same. Since release 1 the forums index has been V3.
- `gcalendar/tests/test_navigation.py`: the same, in its module docstring and
  `test_the_forums_design_links_to_the_calendar`.
- `accounts/tests/test_views.py` `test_the_navbars_submit_logout_as_a_post`:
  its docstring says the forums index renders `navbar.html`.
- `forums/tests/test_moderation.py` (3) and `forums/tests/test_views.py` (6):
  `assertTemplateNotUsed(response, 'base.html')`. Once the file is gone these
  pass whatever the page does. Replace them with `assertTemplateUsed(response,
  'v3/base.html')` where the test doesn't already assert it, or drop them
  where it does.

Decide for each whether the two-design test becomes one test, or keeps
testing two URLs for coverage. Rewrite the docstrings so they say what is
true now. Don't leave a docstring describing a design that doesn't exist.

**The URL walk** (plan, step 12 tests): for every named route in the URL conf
that takes no arguments, GET it as an anonymous visitor and as a logged-in
member. Any status below 500 passes (redirects to login, a 405 on POST-only
views and a 404 are all fine). An exception, `TemplateDoesNotExist` among
them, fails the test and names the route. The test client re-raises view
exceptions, so this works without parsing anything. Walk the resolver
recursively, through `include()`s. Skip `admin:` routes; Django tests its
own admin. List any other skips in the test, each with its reason. Guard
against the walk finding nothing, as `core/tests/test_static.py` does.

**The static check:** no `.html` under the project's template directories
(read them from `engines['django'].template_dirs`, as `test_static.py` does)
has `{% extends "base.html" %}` with either quote style, and
`sg101/templates/base.html` doesn't exist. Step 10 task 03 added a narrower
version for the forums templates. Widen that one, or replace it, rather than
having two.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.5, items 4 and 5)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 12)
- `core/tests/test_static.py` (walking the template directories; the guard against an empty walk)
- `git show b9c4aef1` (the shoutbox removal: the shape of a removal commit)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. The URL walk and the static check exist, and both pass before any
   deletion, apart from the static check's "the file doesn't exist" half.
2. `sg101/templates/base.html`, `sg101/templates/navbar.html`,
   `static/css/blueprint/`, `static/css/base.css` and `static/themes/kds/`
   are deleted, each shown unreferenced by a grep first.
3. `GPP_THIRD_PARTY_JS` has no `jquery` entry, and no template asks for it.
4. No test or docstring describes the forums as wearing `base.html`, and no
   test asserts `assertTemplateNotUsed(..., 'base.html')`.
5. `core/tests/test_static.py` still passes. It reads every literal
   `{% static %}` name and every local third-party path.

## Dependencies
- Step 11 shipped (`46da51e3`): nothing extends `base.html`.
- A branch `retire-base-html`, cut from `main` after these task files are
  committed there.

## Implementation Approach
1. Write the URL walk and the static check. Run them, and expect the
   static check's existence half to fail. Mutation-check the walk: point a
   no-argument view at a missing template and watch it fail and name the
   route.
2. Grep each asset in the table, then delete the files and the `jquery`
   entry.
3. Update the navigation, accounts, script-tag and forum tests. Run the
   affected apps' tests against the running stack, one run at a time.
4. Run the full suite once under the gate. Mutation-check what's new,
   restore byte-identical, and leave the work unstaged for review.

## Acceptance Criteria

1. **Every argument-free page renders**
   - Given every named route taking no arguments, admin's excepted
   - When each is requested anonymously and as a member
   - Then none raises and none answers 500 or above

2. **The walk catches a missing template**
   - Given a no-argument view pointed at a template that doesn't exist
   - When the URL walk runs
   - Then it fails and names that route

3. **One base template**
   - Given the project's template directories
   - When the static check runs
   - Then no template extends `base.html`, and `base.html` doesn't exist

4. **The old assets are gone and nothing misses them**
   - Given Blueprint, `base.css`, `themes/kds`, `navbar.html` and the jQuery 1.11 entry deleted
   - When the suite, including `test_static.py`, runs under the gate
   - Then it passes

5. **The tests describe one design**
   - Given the navigation, accounts and forum tests
   - When they are read
   - Then none says the forums wear `base.html` or asserts it unused

## Metadata
- **Complexity**: Medium
- **Labels**: base.html, removal, cleanup, templates, tests
- **Required Skills**: Django templates, URL resolver, Django test client
