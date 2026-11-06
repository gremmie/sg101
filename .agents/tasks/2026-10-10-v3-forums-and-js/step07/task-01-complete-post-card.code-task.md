# Task: Complete the V3 post card with everything in R14

## Description
Give `forums/display_post_v3.html` every capability today's
`display_post.html` has (R14): the post anchors, quote-reply, edit, flag and
delete, the stranger and spammer tools, attachments, the signature, "Last
edited", PM and email links, the stranger highlight, and the IP link for
moderators. The post tools are buttons that carry `data-post-id`. This task is
the template, its Sass and its tests. The flag and delete buttons do nothing
until task 02 gives the page `topic.js`.

## Background
Step 6 ported the card as `v3-dev` left it: the author card, the posted date,
the permalink icon, the unread mark, the bare IP, and the body. Research topic
1 lists what it lacks, and `display_post.html` on this branch is the item-for-item
reference. It stays as it is: `edit_post.html` still uses it.

**Permalinks are broken on the branch now.** `goto_post` (`/forums/post/<id>/`,
what `Post.get_absolute_url` returns) redirects to `?page=N#p<id>`. The old
card has `<a name="p{{ post.id }}">` and `id="post-{{ post.id }}"`; the V3 card
has neither, so a permalink lands at the top of the page. Keep both names:
`p<id>` because old links, emails and search results carry it, and `post-<id>`
because task 02's delete targets it. `<a name>` is obsolete in HTML5; an `id`
on an element does the same job. `p<id>` and `post-<id>` can't both be the id
of one element, so put them on two.

**Each item, and who sees it** (from `display_post.html`):

| Item | Shown to |
|---|---|
| Quote-reply link, `forums-new_post` with `?quote=<id>` | `can_reply` |
| Edit link (`post_edit_button`) | the post's author, or a moderator |
| Flag button | everyone today. Flagging needs a login (`flag_post` returns 403 otherwise) |
| Delete button | `can_moderate` |
| Stranger tools: "acquaintance" (`forums-stranger`), "spammer" (`forums-spammer`) | `can_moderate`, on a stranger's post that isn't the viewer's own |
| IP as a link to `forums-post_ip_info` | `can_moderate` |
| PM link (`send_pm_url`) and email link | signed-in viewers; email only if the author hasn't set `hide_email` |
| Signature (`signature_html`), "Last edited" (`has_been_edited`) | everyone |
| Attachments (`item.html` for each of `post.attachments.all`) | everyone |
| Stranger highlight on the post info | everyone, when the author `is_stranger` |

**The flag button for an anonymous visitor.** Today it shows and the server
refuses. Match today, or show it only to signed-in viewers? Ask Brian; don't
choose.

**`post_edit_button`** is an inclusion tag that renders a PNG icon from
`forums/post_edit_button.html`. The V3 card needs a V3 variant. Follow step
6's pattern, a `forums/v3/` template chosen on `V3_DESIGN` (see
`forum_tags.py` line 43), or put the condition inline in the card. Either is
fine. Say which, and why.

**Icons are for Brian to choose at task 03's review.** The old card uses PNGs
from `static/icons/`; V3 pages use Foundation Icons (`fi-*`). Use `fi-*`
icons with a `title` and an accessible label on each, and treat the choice of
icon as provisional. Record the ones used, so the review has a list.

**The phone layout has an open question.** Below medium the author card is
`show-for-medium`, so the PM and email links can't live only there, or phones
lose them. The tools row and the post's header are the candidates. Put them
somewhere that works at 360 px and flag it for task 03. Brian decides there.

**The stranger highlight** is `.stranger { background: #FFF6BF }` in the old
`static/css/base.css`. V3 needs its own rule in `_sg101.scss`, readable on
both card colours. Rebuild `main.min.css` and commit both.

**`bio`'s `UnverifiedAddressIsNotDisplayedTestCase.test_forum_post`** is
`@unittest.expectedFailure` until the card has its email link. Adding the link
makes it an unexpected success, which fails the suite. Remove the decorator
and its comment then.

**The full-size image link is not part of this task** (STATUS, step 6 task
02: Brian took it back out on 2026-11-04).

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§2.4 R14, §4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/v3-dev-forums.md (what the card lacks)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 6: the card's colours, the `@expectedFailure`, the full-size image decision)
- `sg101/templates/forums/display_post.html` (the reference, item for item)
- `core/tests/browser.py` (`BrowserTestCase`)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `display_post_v3.html` renders every item in the table above, each to the
   viewers the table names and to no one else.
2. Post tools that act in place (flag, delete) are `<button type="button">`
   elements with `data-post-id`, not links with `id="fp-N"` to parse. Tools
   that go to a page (quote, edit, the stranger tools, the IP) stay links.
3. Each post carries both anchors, `p<id>` and `post-<id>`.
4. `quick_reply_ajax` still renders the card correctly. Its context has
   `can_moderate` and `can_reply` but no `user` key; check that the request's
   `user` reaches the card through the context processor, as the edit link
   and the PM links need it.
5. A V3 stranger highlight in `_sg101.scss`, built into `main.min.css`.
6. Remove `@expectedFailure` from bio's `test_forum_post`.
7. Leave `display_post.html` unchanged.

## Dependencies
- Step 6: `display_post_v3.html`, `topic.html`, the card Sass, and
  `quick_reply_ajax` rendering the V3 card.

## Implementation Approach
1. Write the render tests first and watch them fail: for each item, a post
   and a viewer who should see it, and one who shouldn't. Viewers: anonymous,
   a member, the post's author, a moderator. Posts: an ordinary member's, and
   a stranger's. Add the browser test that `/forums/post/<id>/` for a post on
   page 2 scrolls that post into view.
2. Build the card, item by item, against `display_post.html`.
3. Add the stranger Sass and rebuild the CSS.
4. Check the card in a browser on dev, at 360 and 1280, as a member and a
   moderator, on a topic that has a stranger's post, a signature, an edit and
   an attachment, if dev has one.
5. Run `make test-browser`, the full suite, then the deprecation gate, one at
   a time.
6. Mutation-check: drop each role condition in turn (show delete to a member,
   stranger tools on one's own post, the email link despite `hide_email`) and
   remove the `p<id>` anchor. Each is caught by its test. Restore, and confirm
   the files are byte-identical.

## Acceptance Criteria

1. **Every R14 item renders for the right viewers**
   - Given a topic with an ordinary member's post and a stranger's post
   - When an anonymous visitor, a member, the author and a moderator each view it
   - Then each item in the table appears for the viewers it names, and is absent for the others

2. **Permalinks land on the post**
   - Given a post on the second page of a topic
   - When a browser opens `/forums/post/<id>/`
   - Then it ends on page 2 with that post in the viewport

3. **Tools carry the post id**
   - Given a card with flag and delete
   - When it is rendered
   - Then each is a `button` with `data-post-id` equal to the post's id, and the card has the element `post-<id>`

4. **Quick reply returns the complete card**
   - Given a moderator who quick-replies
   - When the reply is accepted
   - Then the returned card has the edit link, delete, and the IP link

5. **bio's email test passes for real**
   - Given the card's email link
   - When the suite runs
   - Then `test_forum_post` passes with no `expectedFailure` decorator

6. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Medium
- **Labels**: forums, templates, V3 design, Sass, permissions
- **Required Skills**: Django templates and template tags, Foundation 6, Playwright for Python
