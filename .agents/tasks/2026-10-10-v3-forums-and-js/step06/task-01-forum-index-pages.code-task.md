# Task: Port the forums index and a forum's topic list to the V3 design

## Description
Move `/forums/` and `/forums/forum/<slug>/` onto `v3/base.html`, starting
from the `v3-dev` branch's templates and bringing them up to Django 5.2. The
fragments these two pages use come with them, and so does the Sass `v3-dev`
added for the forums. This is the first half of step 6's port. The topic page
is task 02.

## Background
`v3-dev` (2017) converted these two pages in `d8ec4821`. Since the merge base
(`24f83e72`), `main` has changed the same templates by only a few lines. The
one that matters here is the Django 2.2 upgrade (`028601a1`), which turned
`{% load static from staticfiles %}` into `{% load static %}` in 13 forum
templates. `v3-dev` predates it, so its copies still carry the old line, which
fails to load on Django 5.2. Of the files this task ports, that is
`forums/index.html`, `forums/last_post_info.html` and
`bio/member_flags_tag.html`.

A scan of every template step 6 ports found no other removed idiom
(`ifequal`, `ifnotequal`, `length_is`, a called `is_authenticated()`).

**The four shared fragments are used only here.** `accounts/user_stats_tag`,
`core/max_users_tag` and `core/whos_online_tag` are rendered only by
`forums/index.html`, and `bio/member_flags_tag` only inside `user_stats_tag`
(measured 2026-11-03). Porting them changes no other page.

**The Sass `v3-dev` added** (`sg101/scss/_sg101.scss`,
`_sg101_settings.scss`): the blue, surf green and shell pink colour families,
`.shiny`, `.green3`, `.inline-forms`, `.post-odd`, and the two card styles
`.sg101-card1`/`2` with their dividers. Bring over the variables and the
utility classes here. **The card styles belong to task 02**, which replaces
the alternating classes with `:nth-child`. Don't copy them in their `v3-dev`
form only to rewrite them a task later. Compare against `main`'s Sass rather
than copying files: `main` has added a great deal since 2017.

**Four fragments get V3 variants instead of being ported in place (Brian,
2026-11-03).** `v3-dev` rewrote them in place, but pages that stay on
`base.html` until release 2 or 3 still use them, and `base.html` loads no
Foundation styles or icon font:

| Fragment | `v3-dev`'s version | Old-design pages still using it |
|---|---|---|
| `navigation_tag` | Foundation breadcrumbs | 13, among them new topic, new post, edit, the topic lists and every moderator page |
| `forum_query` | Foundation input group | `topic_list`, `manage_topics`, `post_list` |
| `last_post_info` | `fi-arrow-right` instead of a PNG | `topic_list`, `mod_forum` |
| `topic_icons_tag` | `fi-burst-new`, `fi-asterisk`, `fi-lock` instead of PNGs | `topic_list` |

Ported in place, the old pages would lose their unread, sticky and locked
icons and their breadcrumb styling, and release 1 deploys while those pages
are still old. So each gets a copy under `sg101/templates/forums/v3/` holding
`v3-dev`'s markup, and the original stays as it is. The three inclusion tags
(`forum_navigation`, `last_post_info`, `topic_icons` in
`forums/templatetags/forum_tags.py`) choose between the two on `V3_DESIGN`,
the way `monthly_goal` does in `donations/templatetags/donations_tags.py`.
`forum_query` is a plain include, so the ported templates include
`forums/v3/forum_query.html` directly. The old copies go in step 12 with
`base.html`. Design §4.4's "no `forums/v3/` copies" is about whole pages, not
fragments shared by both designs.

`jump_box` and `forum_stats_tag` are used only by pages this step converts
(`forum_index`, `topic`, `index`), so they are ported in place.

**Pagination.** `v3-dev` removed the views' `page_nav` (pagination rendered to
a string because the old template shows it twice) in favour of including
`core/v3/pagination.html` in the template. Do the same for `forum_index`.
`forums/pagination.html` stays: the pages not yet converted still use it.

**Inline scripts.** `forum_query.js` and `jump_box.js` stay inline as `v3-dev`
has them. They become `forums/static/js/nav.js` in step 8 (design §4.4).

This branch, `v3-forums-release-1`, carries steps 6 to 8 and is not deployed
before step 8. Its planning and STATUS changes are committed on it (Q11).

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§2.4 R12, §4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/v3-dev-forums.md (what `v3-dev` converted, and the fragment list)
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 6)
- AGENTS.md (the v3 stylesheet is a committed build artifact; two page designs coexist)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Bring over from `v3-dev`: `forums/index.html`, `forums/forum_index.html`,
   and the fragments `forum_query`, `jump_box`, `navigation_tag`,
   `topic_icons_tag`, `last_post_info`, `forum_stats_tag`, plus
   `accounts/user_stats_tag`, `bio/member_flags_tag`, `core/max_users_tag`,
   `core/whos_online_tag`.
2. Replace `{% load static from staticfiles %}` with `{% load static %}`
   wherever a ported template has it.
3. Diff each ported file against `main`'s version before replacing it, and
   keep any mainline change that isn't the `staticfiles` line.
4. `forums.views.main.index` and `forum_index` add `'V3_DESIGN': True`;
   `forum_index` drops `page_nav` and its template includes
   `core/v3/pagination.html`.
5. Add the colour variables and utility classes from `v3-dev`'s Sass, then
   `npm run build:css` in `sg101/` (or `make css`) and commit the Sass and
   `main.min.css` together.
6. `navigation_tag`, `forum_query`, `last_post_info` and `topic_icons_tag`
   get V3 variants under `forums/v3/`, and their originals are unchanged. The
   three inclusion tags take the context and choose the template on
   `V3_DESIGN`. The ported templates include `forums/v3/forum_query.html`.
   Before porting `jump_box` and `forum_stats_tag` in place, grep again to
   confirm only converted pages use them.

## Dependencies
- Steps 2 to 5 (deployed): the V3 base template on jQuery 3.
- Branch `v3-forums-release-1`, cut from `main`.

## Implementation Approach
1. For each file, `git show v3-dev:<path>` beside `main`'s copy, and record
   what each side changed since `24f83e72`.
2. Grep which templates use each fragment, and confirm the split above still
   holds: in place for `jump_box` and `forum_stats_tag`, V3 variants for the
   other four.
3. Write the render tests first and watch them fail on today's templates.
4. Port the templates, the view context, and the Sass. Rebuild the CSS.
5. Run the forums tests, then the full suite, then the deprecation gate as a
   separate run (one test run at a time: they share `test_sg101`).
6. Mutation-check the new tests (for example, drop `V3_DESIGN` from one view
   and confirm its test fails), restore, and confirm the files are
   byte-identical.

## Acceptance Criteria

1. **Both pages render on the V3 design for each role**
   - Given a forum with topics, and an anonymous visitor, a member, and a moderator of that forum
   - When each requests `/forums/` and `/forums/forum/<slug>/`
   - Then each gets 200, and the response was rendered from `v3/base.html` with `V3_DESIGN` in its context

2. **The index's shared fragments render**
   - Given the forums index
   - When it is requested
   - Then the user stats, maximum users and who's online blocks are in the response

3. **Pagination comes from the V3 fragment**
   - Given a forum with more topics than one page holds
   - When its second page is requested
   - Then the page renders `core/v3/pagination.html` and the view's context no longer has `page_nav`

4. **The four shared fragments choose their variant**
   - Given a V3 page and an old-design page that use the same fragment (for example `forum_index` and the topic list at `/forums/unanswered/` for `topic_icons` and `last_post_info`, and `forum_index` and `new_topic` for `forum_navigation`)
   - When each is requested
   - Then the V3 page renders the `forums/v3/` template and the old page renders the original, with its PNG icons and its `forum-nav` headings

5. **Unconverted pages are unchanged**
   - Given the old-design pages that use these fragments
   - When each is requested
   - Then it renders with 200 on `base.html`, and its fragment templates are byte-identical to `main`'s

6. **The stylesheet is rebuilt**
   - Given the Sass changes
   - When `npm run build:css` is run
   - Then `main.min.css` contains the new classes and is committed with the Sass

7. **Tests are seen to fail**
   - Given the new render tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Medium
- **Labels**: forums, templates, V3 design, Sass, Django
- **Required Skills**: Django templates and test client, Foundation 6 Sass, git archaeology
