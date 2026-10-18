# Task: Clicking a smiley inserts its code at the cursor

## Description
Add `post_box/smileys.js`: clicking a smiley in the picker inserts its code
into the active post box at the cursor, padded with spaces so the renderer
recognises it. The modal stays open so several can be added.

## Background
`get_smiley_regexes` (`smiley/models.py`) matches a code only between
whitespace or line ends: `(^|\s|(?<=\s))CODE(\s|$)`. So the padding is
required, not cosmetic. A code typed against a word (`word:)`) stays text.
The lookbehind lets two codes separated by one space both match.

`post_box/editor.js`'s `insertAtCursor(textarea, text, { ownLine })` inserts
at the saved selection and leaves the caret after the insertion; the
textarea keeps its selection while a modal has focus. A textarea the member
never focused inserts at the end (`trackCaret`). `ownLine` is the precedent
for a padding option: it adds a newline only where one is missing.

`post_box.js` makes the post box whose modal button was clicked the
**active** one (`getActive`), and the modals insert into it. Profile edit has
two post boxes sharing one set of modals.

**The picker is non-modal and draggable, to match the old one** (Brian,
2026-10-18). markItUp's "more smileys" window is jQuery UI's `dialog()` with
default options (`static/js/markitup/sets/markdown/set.js`): no overlay, the
page behind usable, draggable by its title. So members can see, and click
into, their post while picking. It appended each code to the *end* of the
post; the new picker inserts at the cursor.

Measured on dev without changing `foundation.min.js` (attributes added to the
served HTML in flight, 1280 × 900): Reveal reads `data-overlay="false"` and
`data-close-on-click="false"` into its options; the modal then has no
`.reveal-overlay` and is `position: fixed`; a click in the textarea leaves it
open and focuses the textarea (without `data-close-on-click="false"`, 6.2.0
closes an overlay-less modal on any outside click); setting its `top` and
`left` moved it from (320, 151) to (30, 40), and scrolling the page 400 px
left it in place. **Caveat, accepted:** a window resize re-centres it, to
(300, 91): Reveal repositions open modals on resize. Avoiding that means
editing Foundation, which this task doesn't.

On phones, Reveal shows the `small` modal full-screen, so there's nothing to
drag there.

**Every `import` in these modules MUST end in `;`.** Production's static
storage hashes module imports, and `core` `ModuleImportHashingTests` fails
the build on one without (step 2 task 01).

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.2, R8)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 2 tasks 01 and 02: the module conventions)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `post_box/smileys.js`, initialised from `post_box.js` with `getActive`
   like `hot_link.js` and `uploads.js`, and a `MODAL_BUTTONS` entry for the
   smiley button.
2. A click on a `[data-code]` button inserts that code into the active post
   box through `insertAtCursor`, adding a space before it unless it follows
   whitespace or starts the text, and after it unless whitespace or the end
   follows. Never doubled.
3. The caret ends after the inserted code (and its trailing space, if one was
   added), so a second smiley lands after the first.
4. The modal stays open after a click; only Done or the close controls close it.
5. **Non-modal:** `#smiley-modal` gets `data-overlay="false"` and
   `data-close-on-click="false"` (`post_box_modals.html`). The other post box
   modals are unchanged.
6. **Draggable by its title row** on medium screens and up, with pointer
   events, by setting the modal's `top` and `left`. It can't be dragged off
   screen so far that the title row is lost. No drag at small widths.
7. **The active post box follows the member.** Focusing a post box's textarea
   while the picker is open makes it the one smileys go into (profile edit,
   two boxes). Opening the picker from a box's button still makes that box
   active, as now.
8. No jQuery. No change to `foundation.min.js`.

## Dependencies
- Task 01 (the picker markup and the modal).

## Implementation Approach
1. Write the render test and the browser tests; see the browser ones fail.
2. Add the padding (an `insertAtCursor` option or a helper in `smileys.js`,
   whichever reads better beside `ownLine`), then `smileys.js`.
3. Make the modal non-modal (the two attributes), then the drag handler, then
   the focus tracking in `post_box.js`.
4. Mutate each of padding, drag and focus tracking; see a test fail for each;
   restore and `cmp`.
5. Run the suite and the deprecation gate as separate runs.

## Acceptance Criteria

1. **Padding meets the renderer**
   - Given text with codes inserted as the module pads them, two adjacent among them
   - When rendered through `core/markup.py`
   - Then each code becomes its smiley image

2. **Mid-word insertion**
   - Given the caret inside a word in a post box
   - When a smiley is clicked
   - Then the textarea holds exactly the expected text, with one space on each side of the code

3. **Two in a row**
   - Given a smiley just inserted
   - When a second is clicked
   - Then both are present, separated by exactly one space

4. **No doubled spaces**
   - Given the caret already between spaces, or at the start or end of the text
   - When a smiley is clicked
   - Then no extra space is added on a side that already has one, or at the text's ends

5. **The active post box**
   - Given profile edit's two post boxes
   - When the smiley modal is opened from the second and a smiley clicked
   - Then only the second box changes

6. **Stays open**
   - Given the open smiley modal
   - When a smiley is clicked
   - Then the modal is still visible; Done closes it

7. **The post stays usable**
   - Given the open smiley modal
   - When the member clicks into the textarea
   - Then the modal is still open, there is no overlay, and the textarea has focus

8. **Draggable on wider screens**
   - Given the open smiley modal at desktop width
   - When its title row is dragged
   - Then the modal moves with the pointer, and its title row stays on screen

9. **Not draggable on phones**
   - Given the open smiley modal at about 375 px
   - When its title row is dragged
   - Then the modal doesn't move

10. **The active box follows focus**
    - Given profile edit, the picker opened from the first box
    - When the member clicks into the second box and clicks a smiley
    - Then only the second box changes

11. **Mutation**
    - Given the padding removed, the drag handler removed, or the focus tracking removed, each alone
    - When the tests run
    - Then a test fails for each

## Metadata
- **Complexity**: Medium
- **Labels**: Smileys, JavaScript, ES modules, post box, drag, Foundation Reveal, #9
- **Required Skills**: Vanilla JavaScript, pointer events, textarea selection APIs, Django tests, Playwright (mouse drag)
