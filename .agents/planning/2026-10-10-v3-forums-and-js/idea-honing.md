# Idea honing

Requirements clarification, one question at a time.

## Q1. What does "modernize the site JavaScript" (#18) mean to you?

The answer decides how big #18 is and whether it has to come before the forum
work. Possible meanings, from smallest to largest:

- **A. Tidy what's there.** Keep jQuery and Foundation 6.3.1's JavaScript, but
  move to one jQuery version, serve it locally instead of from Google's CDN,
  and drop jQuery UI and markItUp once the forums no longer need them.

  **Corrected 2026-10-15:** the vendored JavaScript is Foundation **6.2.0** (hash-matched to its release); only the Sass is 6.3.1. See `STATUS.md`, step 3 task 01.
- **B. No jQuery in new code.** New and rewritten code (the post box, the
  forums) is plain modern JavaScript. jQuery stays only for as long as
  Foundation's JavaScript needs it.
- **C. No jQuery at all.** Replace Foundation's JavaScript (dropdowns, modals,
  the off-canvas menu) as well, which means upgrading Foundation or replacing
  it.
- **D. Something else**, for example a build step, modules, or TypeScript.

**Answer:** **B. No jQuery in new code.** New and rewritten code, including the post box
and the forums, is plain modern JavaScript. jQuery stays only as long as
Foundation's JavaScript needs it. Removing jQuery entirely (C) is deferred, to
be revisited later. It would most likely mean moving off Foundation, not
upgrading it. (Brian, 2026-10-10)

## Q2. Does all JavaScript stay unbundled, or does the site get a build step?

Today every script is a plain file served as-is, and `sg101/` already uses npm,
but only to compile Sass. Possible approaches:

- **A. No build step.** Plain files, with native ES modules
  (`<script type="module">`) where sharing code helps. Nothing to compile or
  commit.
- **B. A bundler (for example esbuild), with output committed**, the way
  `main.min.css` is. This allows npm packages and minification, but adds a
  second build artifact that can go stale, and deploys don't build.
- **C. A bundler run at image build time.** This needs Node in the Docker
  build.

**Answer:** **A. No build step.** Plain files served as-is, using native ES modules
(`<script type="module">`) where sharing code helps. (Brian, 2026-10-10)

## Q3. How should smileys work in the V3 post box (#9)?

How it works today: smiley codes such as `:)` become images at render time
(`SmilifyMarkdown` in `core/markup.py`), so posts written in the V3 post box
already display smileys. Only a way to *insert* them is missing. The old
markItUp editor shows the 20 main smileys inline. A "more smileys" link opens a
jQuery UI dialog, which fetches the 65 extras from `/smiley/farm/extra/`.
Clicking one appends its code to the textarea. (Counts are from the dev
database.)

Possible approaches:

- **A. A toolbar button that opens a Foundation reveal (modal).** It shows all
  smileys, with the main set first, and clicking one inserts its code at the
  cursor.
- **B. Same as A, but the main 20 sit in a row under the textarea** and the
  modal holds only the extras, as the old editor does.
- **C. A dropdown palette from the toolbar** (Foundation dropdown pane)
  instead of a modal.

**Answer:** **A.** A toolbar button opens a Foundation reveal that shows all
smileys, the main set first. Clicking one inserts its code at the cursor.
(Brian, 2026-10-10)

## Q4. How should a batch of image uploads behave (#16)?

How it works today: the upload modal (`core/v3/post_box_modals.html`) takes one
file and posts it to `user_photos-upload_ajax_v3` with jQuery's `ajaxForm`. The
server resizes the image, stores it on S3, and returns its URL, and the post
box appends `![image](url)`. Uploads are rate-limited to 50 a day per user
(`USER_PHOTOS_RATE_LIMIT`). gunicorn kills a request after 30 s; Cloudflare
buffers the body first, but the resize and the S3 upload still run inside that
window.

Observed in passing: post_box.js's wiring is jQuery (`$`, `ajaxForm`,
`clearForm`), not just its helpers, so "mostly vanilla" in `rough-idea.md`
overstated it.

Possible approaches:

- **A. One request per image, sent one after another.** The modal lists the
  chosen files with thumbnails and a remove button on each. Upload sends them
  in turn, each inserting its image code as it finishes. A failure is shown
  against that file, and the rest still go. The server needs no change.
  A cap of perhaps 10 per batch keeps one batch from using up the day's quota.
- **B. One request carrying every image.** This needs a new endpoint. A batch
  of large images risks the 30 s timeout, and it succeeds or fails as a whole.

**Answer:** **A, with a limit of 10 images per batch.** One request per image,
sent in turn. Each image's code is inserted as it finishes, and a failure is
shown against its file without stopping the rest. (Brian, 2026-10-10)

Brian asked whether the upload processing runs on Celery and so escapes the
30 s limit. **It does not.** `upload_ajax_v3` → `UploadForm.save()`
(`user_photos/forms.py`) writes a temp file, resizes it, makes a thumbnail,
puts both on S3 (`core/images/upload.py`), and saves the `Photo`, all inside
the request. Cloudflare's buffering covers only the body transfer. A keeps
each request to one image, which bounds it. **Not yet measured:** how long one
large image takes to process. That goes on the research list.

## Q5. Is removing the shoutbox, and retiring `base.html`, in scope?

The shoutbox appears only on `base.html`, so today it shows on the forum
pages and nowhere else. Converting the forums takes it off screen regardless.
Use, from the dev database (a copy of production, latest post 2026-10-07):

| Year | Shouts | Members shouting |
|---|---|---|
| 2011 | 500 | 123 |
| 2015 | 181 | 54 |
| 2018 | 36 | 16 |
| 2022 | 18 | 14 |
| 2025 | 9 | 9 |
| 2026 | 8 | 6 |

Once the forums are converted, `base.html` has one remaining user,
`flatpages/default.html`. The five flatpage rows (`/about/`, `/colophon/`,
the two policies, `/store/`) look superseded by the `fixed` and `store` apps,
but that is unverified.

Possible scopes:

- **A. In scope.** Remove the shoutbox app (its data archived first, as the
  wiki's was) and flatpages if they are dead, then delete `base.html`, Blueprint
  CSS, jQuery 1.11, jQuery UI and markItUp.
- **B. Forums only.** Leave the shoutbox installed but invisible, and leave
  `base.html` for a later cleanup.

**Answer:** **A. In scope.** Remove the shoutbox (its data archived first) and
retire `base.html`, with Blueprint CSS, jQuery 1.11, jQuery UI and markItUp.
Flatpages go too if they turn out to be dead. (Brian, 2026-10-10)

**Correction (research, 2026-10-10):** jQuery UI doesn't go with `base.html`.
At least four V3 pages use it (datepicker on `bio/edit_profile` and
`gcalendar/event`; autocomplete on `bio/member_search` and
`messages/compose`). See `research/foundation-upgrade.md`. Blueprint, jQuery
1.11 and markItUp still go.

**Flatpages moved out of this project (Brian, 2026-10-10):** research topic 5
found the app serves nothing, so its removal is GitHub issue #33, which can
ship independently. Step 8 deletes `flatpages/default.html` only if #33
hasn't landed by then.

## Q6. Is the `v3-dev` look the target for the forums?

On `v3-dev` the topic page shows each post as a pair of Foundation cards: an
author card on the left (hidden on small screens, with the name moved into the
post header), the post on the right, alternating two colour schemes
(`sg101-card1`/`sg101-card2`). The index and forum pages are restyled tables.

Possible approaches:

- **A. Port `v3-dev` as it is, then finish it.** Its look is the target, and
  changes come from reviewing it running.
- **B. Port it, then review it in a browser before deciding.** Bring the
  three pages over and screenshot them at phone and desktop widths, then
  decide what to keep.
- **C. Start the design fresh**, using `v3-dev` only for reference.

**Answer:** **B.** Port the three `v3-dev` pages first and screenshot them at
phone and desktop widths. Brian reviews the look before the remaining pages are
built on it. (Brian, 2026-10-10)

## Q7. How do the converted forum pages reach production?

The editor work (#9, #16) changes pages that are already V3, so it can ship
whenever it's ready. The forum pages are the question. A member moves between
them in one visit (index → forum → topic → reply form), so a partial release
mixes the two designs within the forums.

Possible approaches:

- **A. Ship in coherent groups as they're done.** For example: the reading
  pages (index, forum, topic) with the three post forms; then the lists and
  message pages; then the moderator pages. This is how the rest of the site
  went V3, and members lived with mixed designs then.
- **B. Ship the forums all at once.** Work merges to `modernize` but the
  production deploy waits until every forum page is converted.
- **C. Behind a switch.** Both designs are live, chosen per user (staff
  first) or site-wide by a setting. This needs a second set of templates kept
  side by side until the switch is removed.

**Answer:** **A. Release in groups as each is done:** the reading pages and the
three post forms first, then the lists and message pages, then the moderator
pages. (Brian, 2026-10-10)

## Q8. Where does video embedding live?

The testers' report behind #9 (STATUS.md, 2026-10-04) asked for **emoji and
video-embed buttons** in the V3 editor. The issue's text mentions only smileys.

Today only forum posts can embed video. That works as a separate "Video
Attachments" area under the forum form (`forums.js`), not in the text. It
fetches the embed through `/oembed/fetch/` and saves it as an `Attachment`
row on the post (`forums/models.py`), shown under the body. News, comments and
messages have no video embedding; nothing in `core/markup.py` handles it.

Possible approaches:

- **A. Keep it forum-only.** Restyle the attachment area for V3 (`v3-dev`
  started this) and rewrite its JavaScript without jQuery.
- **B. Move it into the shared post box** as a toolbar button, so every post
  box can attach video. Each model that takes posts then needs somewhere to
  store attachments, or a different mechanism.
- **C. Keep forum-only for this project**, and open a separate issue for
  video in the post box everywhere.

**Answer:** **B, shown only on the forums.** A video toolbar button in the shared
post box, rendered only where the post box is used in the forums. News,
comments and messages are unchanged on this pass. This depends on the toolbar
still fitting on a phone. (Brian, 2026-10-10)

What that implies:

- **The toolbar's phone count goes from 5 to 7.** It has 12 buttons; 7 carry
  `hide-for-small-only`, leaving link, hot-link, upload, preview and help.
  Smileys (Q3) and video add two. At Foundation's default menu padding a
  button is roughly 50 px, so 7 is about 370 px against about 328 px usable on
  a 360 px phone. **That is estimated from defaults, not measured;** measure it
  in the Q6 screenshot pass. If it doesn't fit, tighten the padding or move a
  button to the hidden list.
- **The button attaches; it does not insert.** Forum video is stored as
  `Attachment` rows, not in the post's Markdown. The button opens a modal
  that adds to the attachment list under the post box, unlike its
  neighbours, which insert into the text.
- **The post box needs a way to know it is on the forums**, for example an
  argument to the `post_box` tag (`core/templatetags/core_tags.py`).

## Q9. How should the rewritten JavaScript be tested?

Today there are no JavaScript or browser tests. The Django suite covers views
and templates, and browser behaviour has been checked by hand (Claude in
Chrome, or Brian). This project rewrites most of the site's interactive code:
the post box, quick reply, flag and delete, video attachments, moderator bulk
actions.

Possible approaches:

- **A. Django tests plus manual browser checks**, as now. Each step's demo is
  a scripted check done by hand in a browser, recorded in the step's notes.
- **B. Add browser tests (Playwright for Python)** driving the real pages
  against Django's live server. They would run in the suite and in CI. This
  adds a dependency and browser binaries to the test image.
- **C. Unit tests for the JavaScript only** (e.g. Node's built-in test runner
  on the plain modules). This adds Node to CI, but not a browser.

**Answer:** **B, a small set of Playwright tests** (Playwright for Python against
Django's live server, in the suite and in CI) for the paths that fail
silently: quick reply, smiley insertion, a batch upload with one failure, and
adding a video. Everything else is checked by hand in a browser.
(Brian, 2026-10-10)

## Q10. What order should the work go in?

Proposed:

1. **Post box, rewritten without jQuery** (same behaviour), with the
   Playwright setup and its first test. This is the shared foundation, and it
   is used on 12 pages that are already V3.
2. **Smileys (#9)** in the post box. Ships.
3. **Multiple image uploads (#16).** Ships.
4. **Port the three `v3-dev` pages, then screenshots and review** (Q6),
   including measuring the phone toolbar (Q8).
5. **Finish the reading pages and the three post forms**, with the video
   button. First forum release.
6. **Lists and message pages.** Second release.
7. **Moderator pages.** Third release.
8. **Remove the shoutbox and retire `base.html`** (Q5).

An alternative is to put step 4 first, so the design review happens while the
editor work is under way.

**Answer:** **The proposed order, revised to move the confirmation pages into the
first release.** Those pages are where members land after acting on a
release-1 page (new topic, favorite, subscribe), so leaving them for later
would send members from the new design to the old on an ordinary visit.
(Brian, 2026-10-10)

1. Post box rewritten without jQuery, with the Playwright setup.
2. Smileys (#9). Ships.
3. Multiple image uploads (#16). Ships.
4. Port the three `v3-dev` pages; screenshot and review.
5. **First forum release.** Reading pages (forums index `index.html`, a
   forum's topic list `forum_index.html`, a topic `topic.html`, which also
   serves the `unread/`, `latest/` and `post/<id>/` redirects); the three post
   forms (new topic, reply, edit) with the video button; and the three
   confirmation pages (`new_topic_thanks`, `favorite_status`,
   `subscription_status`).
6. **Second release: list pages.** `topic_list.html` (unread, unanswered,
   active), `post_list.html` (my posts, a member's posts), and
   `manage_topics.html` (favorites, subscriptions).
7. **Third release: moderator pages.**
8. Remove the shoutbox and retire `base.html`.

## Q11. Which branches does the work happen on?

Raised by Brian on 2026-10-10 while discussing merging `modernize` into `main`.

**Answer: one short-lived branch per piece that ships, cut from `main` and
merged back when that piece is released.** Not directly on `main`, and not one
long-lived V3 branch. (Brian, 2026-10-10)

Why:

- **Not on `main`:** leopard deploys with a plain `git pull` of `main`. A
  half-finished release on `main` would ship with any unrelated fix deployed in
  the meantime.
- **Not one long branch:** `v3-dev` is the cautionary example. It sat apart
  from mainline from 2017 to 2018 and was never finished.

How:

- **One branch per Q10 step that ships** (names are placeholders):
  `post-box-vanilla` (1), `smileys` (2), `multi-upload` (3),
  `forums-v3-release-1` (4–5), `forums-v3-release-2` (6),
  `forums-v3-release-3` (7), `retire-base-html` (8). Steps 1–3 may share a
  branch if the editor work is released together.
- **A branch merges to `main` when it is deployed**, so `main` always matches
  what leopard should run. A branch that outlives a fix on `main` merges `main`
  in.
- **CI must test the feature branches.** It must run on pushes to any branch
  and on pull requests to `main`, not only on `modernize` as now.
- **This project's planning and status changes are committed on the step's
  branch** (`STATUS.md`, the plan, the task files), and reach `main` when the
  step deploys. `STATUS.md` cites commits and measurements of that branch's
  code, which `main` doesn't hold until then. Planning done between branches,
  before the next one is cut, goes on `main`. (Brian, 2026-10-14)

### Prerequisite: `modernize` becomes `main` (proposed, not yet approved)

jaguar is no blocker: it serves its own hg checkout on the hg `default` branch
and has been `OFFLINE` since the 2026-10-07 cutover. Git `main` deploys
nowhere. It holds one commit not on `modernize`, `e1d6aa8c` (2026-07-03, the
PayPal IPN curl workaround), which `modernize` supersedes with `requests` in
`donations/views.py`.

Proposed steps:

1. `git merge -s ours main` on `modernize`, then fast-forward `main`. No
   history is rewritten.
2. CI triggers changed as above, and `README.md` updated.
3. GitHub's default branch set to `main`. **A repository setting: confirm with
   Brian first.**
4. leopard's clone switched to `main`. **Brian runs it.**
5. `modernize` deleted afterwards, or kept for a while for old links.

## Q12. Stay on Foundation, or switch frameworks?

Raised by Brian on 2026-10-10. He likes how Foundation looks across the site,
but it was chosen eight years ago.

**Answer: stay on Foundation. A framework change is out of scope for this
project.** Upgrading within Foundation, from 6.3.1 to 6.9.0, is a research
question, not yet a decision. (Brian, 2026-10-10)

What was known when deciding (npm registry, read 2026-10-10):

- **Foundation is barely moving.** The latest release is **6.9.0
  (2024-09-27)**, after 6.8.0/6.8.1 (2023-08-18) and 6.7.5 (2022-07-12). The
  site is on 6.3.1 (2017). **Corrected 2026-10-15:** the vendored JavaScript is Foundation **6.2.0** (hash-matched to its release); only the Sass is 6.3.1. See `STATUS.md`, step 3 task 01.
- **6.9.0 still requires jQuery**: a `jquery >= 3.6.0` peer dependency. Under
  Q1, jQuery stays as long as Foundation does.
- **Bootstrap 5** (5.3.8) is maintained and has no jQuery.

Why stay:

- **About 60 V3 templates across 20 apps already use Foundation.** Switching
  would rewrite them to reach the look already in place.
- **#17 would otherwise wait on a framework migration.**
- **Nothing breaks if Foundation stops releasing.** The CSS is a committed
  build, and the Sass toolchain was fixed in September 2026 (`7f7bd3fa`).
- **Q1 and Q2 keep a later switch cheap.** New JavaScript doesn't use jQuery,
  has no build step, and touches Foundation's plugins only to open its modals.
  A future switch would mostly change class names in the markup.

If a switch is ever considered, the candidates were Bootstrap 5, Tailwind
(needs a CSS build step, and every template's classes rewritten), and plain
modern CSS with the site's own Sass.

Requirements clarification declared complete by Brian, 2026-10-10.

## Q13. Upgrade Foundation, or only jQuery?

Raised by Brian on 2026-10-10 after research topic 7
(`research/foundation-upgrade.md`): what does the Foundation upgrade actually
buy, newer jQuery?

**Answer: Foundation stays on 6.3.1. jQuery moves from 2.2.4 to 3.x as a step
in this project, served from the site instead of Google's CDN.**
(Brian, 2026-10-10)

Why:

- **jQuery 3 doesn't need the Foundation upgrade.** Foundation 6.3.1 declares
  `jquery >= 2.2.0` (`node_modules/foundation-sites/package.json`), which
  admits 3.x. That's declared, not yet tested in a browser. **Corrected
  2026-10-15:** that `package.json` is the npm package the Sass builds from.
  The JavaScript the site loads is 6.2.0's (`STATUS.md`, step 3 task 01).
- **Without jQuery 3, the Foundation upgrade buys little:** plugin bug fixes
  of no known effect here, fewer Sass deprecations that only matter after Dart
  Sass 2.0 or 3.0, and a smaller jump later.
- **It costs a whole-site screenshot review**, since 283 of 1,298 rules change,
  mostly menus, buttons and tables. It also adds 123 KB of JS against 104 KB
  today.

The jQuery 3 step: serve jQuery 3 locally; change `comments.js`'s `.size()` to
`.length`; check Foundation 6.3.1, jQuery Form (v20130916), jQuery UI 1.11
and jQuery Cycle 3.0.3 on jQuery 3. It is placed early, after the post box
rewrite. Research topic 8 covers the compatibility.

Still open from topic 7: **whether replacing jQuery UI** (the datepickers and
autocomplete on four V3 pages) is in this project.

**Correction (research topic 8, 2026-10-10):** the first reason above was
wrong in practice. Foundation 6.3.1's own code calls `$(window).load(fn)`,
which jQuery 3 removed. On bare jQuery 3 that throws on every page and stops
Reveal (no post box modal). A one-line patch to the vendored
`foundation.min.js` fixes it. jQuery UI 1.11's autocomplete also misplaces its
menu on jQuery 3, and 1.13.3 fixes that. With both, every page probed matched
2.2.4. **The decision stands; the jQuery 3 step grows by the patch and the
jQuery UI bump.** See `research/jquery3.md`.

**Correction (2026-10-15):** every "Foundation 6.3.1" in Q13 that means the
JavaScript should read 6.2.0. The vendored `foundation.min.js` is 6.2.0's
release, hash-matched; only the Sass is 6.3.1 (`STATUS.md`, step 3 task 01).
The decision stands: Foundation stays as it is, Sass and JavaScript both.
