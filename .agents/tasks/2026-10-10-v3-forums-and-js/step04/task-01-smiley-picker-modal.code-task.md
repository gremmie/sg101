# Task: The smiley picker modal and its toolbar button

## Description
Render every smiley into a new post box modal, server-side, and add a smiley
button to the post box toolbar that opens it. This is the markup half of #9:
after this task the modal opens and shows every smiley, and task 02 makes
clicking one insert its code.

## Background
Smiley codes such as `:)` already become images when a post is rendered
(`core/markup.py` → `smiley.utils.SmilifyMarkdown`). Only a way to *insert*
them from the V3 post box is missing (Q3, R8). The old markItUp editor shows
the 20 main smileys inline through `{% smiley_farm %}` and fetches the 65
extras from `/smiley/farm/extra/` into a jQuery UI dialog.

Design §4.2 renders them all into the page instead, through a new inclusion
tag. Brian confirmed that over fetching on open (2026-10-17), on these
measurements:

- **Markup cost:** dev's 85 smileys as buttons are 13.9 KB, **1.8 KB
  gzipped**. The live polls page is 7.1 KB gzipped, for comparison.
- **Images load only when the modal opens.** Headless Chromium 153 in the dev
  image, 85 `loading="lazy"` images in a `display: none` box: 0 requested
  before it is shown, all 85 once it is shown. Chromium's lazy-load margin
  covers the whole picker, so they load together, not on scroll. The control
  (no `loading` attribute) requested all 85 at page load. Firefox and Safari
  weren't measured; task 03 checks one by hand.
- Fetching would keep an endpoint alive (step 9 removes `/smiley/farm/`) and
  add loading and failure states, to save those 1.8 KB.

`Smiley.objects.get_smilies(extra)` (`smiley/models.py`) returns the rows
whose `is_extra` matches, in `title` order, cached an hour under `smileys`
or `smileys_extra`. Its `if smilies:` check never caches an empty set. Tests
run on Django's default `LocMemCache`, which lasts the whole test process,
so a test that changes smileys MUST clear the cache in its `setUp` (or the
cached set from an earlier test is what renders). The `smilies.json` fixture
holds the real set (`core` `SiteMarkdupTestCase` uses it).

The modals are shared, one set per page, in `core/v3/post_box_modals.html`.
It is included by news submit, profile edit, message compose and view, the
V3 comment form (downloads, POTD, polls, contests), the event page, and
download add. Grep for the include rather than trusting this list.

**The button's icon is undecided.** Foundation Icons, the only icon font V3
loads, has no smiley (`fi-social-facebook` is its only "face" match). The
candidates found so far are the site's own `:)` smiley image and a Unicode ☺.
Present them to Brian with a screenshot of each at phone width; don't choose.

At phone width the toolbar shows link, hot-link, upload, preview and help;
the smiley button makes six. Step 5 checks whether seven fit at 360 px
(design §7.3); task 03 checks six.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.2, R8)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/idea-honing.md (Q3)
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 4)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `{% smiley_picker %}`, an inclusion tag in `smiley/templatetags/smiley_tags.py`,
   rendering `get_smilies(False)` then `get_smilies(True)`.
2. Each smiley is a `<button type="button" data-code="…">` around
   `<img loading="lazy" src="…" alt="…" title="title code">`, with the code
   HTML-escaped by Django's autoescaping, not by hand.
3. A smiley modal in `post_box_modals.html` (`id="smiley-modal"`, a Reveal
   like the others, scrollable), holding the picker and a **Done** button
   that closes it (`data-close`).
4. A smiley button in `core/v3/post_box.html`, `data-open="smiley-modal"`,
   visible on small screens, with an accessible name. Icon per Brian's choice.
5. No JavaScript changes beyond what the button needs to open the modal
   (Foundation's `data-open` already does that). Insertion is task 02.

## Dependencies
- Step 3, deployed: Reveal's `aria-hidden` and focus fixes apply to the new
  modal unchanged.

## Implementation Approach
1. Write the tag tests and see them fail.
2. Add the tag and its template; then the modal and the toolbar button.
3. Screenshot the icon candidates at 375 px for Brian, and apply his choice.
4. Run the suite and the deprecation gate as separate runs.

## Acceptance Criteria

1. **Main set first**
   - Given main and extra smileys
   - When `{% smiley_picker %}` renders
   - Then every main smiley's button comes before every extra one's

2. **Codes escaped**
   - Given a smiley whose code contains `"` or `<` or `&`
   - When the picker renders
   - Then its `data-code` attribute holds the escaped code and the markup is intact

3. **Every post box page has the modal**
   - Given each page that includes `post_box_modals.html`
   - When it renders
   - Then it contains `#smiley-modal` with the picker, and each post box has a smiley button opening it

4. **Lazy images**
   - Given the rendered picker
   - When inspected
   - Then every image has `loading="lazy"` and alt text

5. **It opens**
   - Given news submit in a browser
   - When the smiley button is clicked
   - Then the modal is visible, holds every smiley, and no page error is raised; Done closes it

## Metadata
- **Complexity**: Low
- **Labels**: Smileys, templates, template tags, post box, #9
- **Required Skills**: Django inclusion tags and templates, Foundation Reveal, Playwright
