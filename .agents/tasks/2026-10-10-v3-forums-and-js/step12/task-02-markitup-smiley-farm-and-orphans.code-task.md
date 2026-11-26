# Task: Remove markItUp, the smiley farm, and the old design's orphans

## Description
Remove what the old design used and nothing V3 does: markItUp and everything
built around it, the smiley farm, templates nothing renders, and old static
files nothing loads. Every deletion is backed by a grep showing nothing
references it.

## Background
**Measured on `main` at `278b51d4`.** Recheck each row before deleting. Task
01 changes the picture slightly.

**markItUp.**

| Where | What |
|---|---|
| `static/js/markitup/` | the editor, its Markdown set, skins and `templates/preview.css` |
| `sg101/settings/base.py` | the `markitup` entries in `GPP_THIRD_PARTY_JS` and `GPP_THIRD_PARTY_CSS` |
| `comments/views.py` `markdown_preview`, `comments/urls.py` `comments-markdown_preview` (`/comments/markdown/`) | the preview endpoint. Only markItUp's `set.js` (`previewParserPath`) calls it. The post box uses `markdown_preview_v3` (`/comments/markdown/v3/`), **which stays** |
| `sg101/templates/comments/markdown_preview.html` | that endpoint's template, the one that links `preview.css` |
| `comments/tests/test_views.py` (around line 185) | the old endpoint's tests. The `_v3` tests stay |
| `comments/forms.py`, `downloads/forms.py`, `forums/forms.py` (3), `news/forms.py` | `attrs={'class': 'markItUp smileyTarget'}` on the body textarea. Nothing in V3 JS, templates or Sass reads either class. **Check the post box tag and its templates don't key on the widget's class before removing it** |
| `sg101/scss/_sg101.scss` `.markItUpEditor` | a rule for the element markItUp's JS creates |
| `gcalendar/static/css/gcalendar.css` `.markItUp`, `.markItUpEditor` | the same, loaded by `gcalendar/event.html`. Delete the rules. Delete the file and its link only if nothing else is left in it |
| `core/tests/templatetags/test_script_tags.py` | asks for `markitup`. Use another entry |
| `comments/views.py` line ~142 docstring | "a javascript editor such as markItUp" |

**Changing the Sass means rebuilding the stylesheet** (`npm run build:css` in
`sg101/`) and committing both. The forums tests pin selectors and computed
colours from `main.min.css`, so run them before committing.

**The smiley farm:** the `farm` view and its two routes in `smiley/urls.py`
(`smiley-farm`, `smiley-farm_extra`, under `/smiley/farm/`), the
`smiley_farm` inclusion tag, and `sg101/templates/smiley/smiley_farm.html`.
Nothing V3 uses them. The picker is `smiley_picker`, which stays. Check
`smiley/tests/` for tests of the farm.

**Templates nothing renders.** A name search found these candidates.
Generic views, format strings and mail bodies make many of them false
positives, so prove each one either way before deleting:

- `ygroup/pagination.html` (the `ygroup/v3/` pages include
  `ygroup/v3/pagination.html`). The plan said three `ygroup` templates. Two
  are already gone.
- `core/pagination.html`, `core/pagination_query.html`,
  `core/django_pagination.html`, `core/rfb_block.html`,
  `core/social_block.html`, `sopa.html`, `offline.html`.
- The old forum templates the plan names (`display_post.html` "and
  others"): check every non-`v3/` file under `sg101/templates/forums/`.
  Most were converted in place and are live. `forums/pagination.html` is
  still included by several pages.
- **Not here:** the three old forum fragments (`last_post_info.html`,
  `navigation_tag.html`, `topic_icons_tag.html`) and the seven old tag
  variants. They go with `V3_DESIGN` in task 03.

`404.html`, `500.html`, the `*_email.txt` bodies,
`admin/gcalendar/event/change_list.html`, `contests/contest_detail.html` and
`contests/contest_list.html` are found by Django's conventions, not by name.
They stay.

**Old static files nothing loads** (top-level `static/`; the repo has two
static trees):

- `js/jquery.form.min.js`: unused since step 8 task 03. A forums test
  asserts its absence by name, so that assertion stays.
- `js/jquery.cycle.all.min.js` (the home page loads `all3.0.3`)
- `css/pagination.css`, `css/tab-nav.css`
- the `imagesloaded` and `jquery-jeditable` entries in `GPP_THIRD_PARTY_JS`,
  and their files `js/jquery.imagesloaded.min.js` and
  `js/jquery.jeditable.mini.js`
- `icons/new.png`, if task 03's deletion of `forums/topic_icons_tag.html`
  would leave it unused. Otherwise note it for task 03.

**Keep:** `tiny_mce` (four admin `Media` classes), `timezone.js`,
`jplayer`, `flags/`, `jquery.cycle.all3.0.3.js`, `jquery-ui`.

**The grep, for each file:** its path and its basename across templates,
Python, `sg101/static/js`, every app's `static/`, `sg101/scss`, `tools/` and
fixtures. Leave out `.agents/` and `archive/`. Record any hit you judge
harmless, and why.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.5, item 4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 12)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 8 task 03: markItUp and `jquery.form` left unused)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `git grep -i markitup`, outside `.agents/` and `archive/`, finds nothing.
2. `/comments/markdown/` and `/smiley/farm/` answer 404.
   `/comments/markdown/v3/` still works.
3. Every deleted template and static file has a recorded grep showing no
   reference.
4. The stylesheet is rebuilt from the Sass, and both are committed together.
5. `core/tests/test_static.py` still passes.

## Dependencies
- Task 01: `base.html` gone. Task 01 added no URL walk or static template
  check (Brian, 2026-11-26; `STATUS.md`, step 12 task 01): a template deleted
  in error is caught by the grep before deleting, the suite, and task 04's
  browser walk.

## Implementation Approach
1. Write the tests first, and watch them fail: `/comments/markdown/`,
   `/smiley/farm/` and `/smiley/farm/extra/` 404, and their URL names don't
   reverse. Add them to the existing removed-things test
   (`core/tests/test_pruned.py`). Keep or add a test that
   `/comments/markdown/v3/` still renders a preview.
2. Remove markItUp, then the smiley farm, then each orphan. Grep first,
   every time.
3. Rebuild the CSS. Run the affected apps' tests, the forums included, then
   the full suite once under the gate.
4. Mutation-check the new tests, restore byte-identical, and leave the work
   unstaged for review.

## Acceptance Criteria

1. **markItUp is gone**
   - Given the repository outside the planning record and the archive
   - When it is searched case-insensitively for `markitup`
   - Then nothing is found

2. **The retired URLs are gone and the live preview isn't**
   - Given the URL conf after this task
   - When `/comments/markdown/`, `/smiley/farm/` and `/smiley/farm/extra/` are requested
   - Then each answers 404, and the post box's preview at `/comments/markdown/v3/` still renders

3. **No live template or asset was deleted**
   - Given the deletions
   - When `test_static.py` and the full suite run under the gate
   - Then they pass

4. **The shipped stylesheet matches the Sass**
   - Given `.markItUpEditor` removed from `_sg101.scss`
   - When `npm run build:css` runs
   - Then the committed `main.min.css` is unchanged by it

5. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Medium
- **Labels**: markItUp, smileys, removal, cleanup, static files, Sass
- **Required Skills**: Django URL conf and templates, Sass build, grep discipline
