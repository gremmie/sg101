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
5. No jQuery.

## Dependencies
- Task 01 (the picker markup and the modal).

## Implementation Approach
1. Write the render test and the browser tests; see the browser ones fail.
2. Add the padding (an `insertAtCursor` option or a helper in `smileys.js`,
   whichever reads better beside `ownLine`), then `smileys.js`.
3. Mutate: drop the padding and see the tests fail; restore and `cmp`.
4. Run the suite and the deprecation gate as separate runs.

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

7. **Mutation**
   - Given the padding removed
   - When the browser tests run
   - Then they fail

## Metadata
- **Complexity**: Medium
- **Labels**: Smileys, JavaScript, ES modules, post box, #9
- **Required Skills**: Vanilla JavaScript, textarea selection APIs, Django tests, Playwright
