# Rough idea

Finish the V3 design for the forums (GitHub #17). Before that, do the V3 post
editor work: smileys (#9) and multiple image uploads (#16). First, though,
decide which direction the site's JavaScript modernization (#18) takes, because
the order and approach of all four issues depend on each other.

## The issues

- **#9 Add smileys to the V3 post editor.** The V3 post editor (seen on news
  submissions) still needs smiley support. It will eventually be used in the
  forums.
- **#16 Support multiple image uploads in the V3 post editor.** Investigate
  supporting multiple image uploads in a forum post. Ideally the user can select
  several files and remove choices before clicking upload.
- **#17 Finish the forums V3 design.**
- **#18 Modernize the site JavaScript.**

## What was observed on 2026-10-10, before the PDD started

- **Two jQuery versions are loaded.** Old-design pages (`base.html`) load
  jQuery 1.11.1, jQuery UI 1.11 and markItUp through `script_tags`
  (`sg101/settings/base.py`). V3 pages (`v3/base.html`) load jQuery 2.2.4,
  what-input and Foundation 6.3.1's JavaScript. All the jQuery comes from
  Google's CDN.
- **Foundation 6.3.1's JavaScript requires jQuery.**
- **The V3 editor is `sg101/static/js/v3/post_box.js`.** It is 221 lines of
  mostly plain JavaScript, used by 12 templates.
- **Pages still on the old design:** forums (19 templates), shoutbox (3),
  ygroup (3), flatpages, and the old `home.html`.
- **The `v3-dev` branch is reference only.** It has 7 commits from 2017-02 to
  2017-08, touches 20 files, and merges mainline as of 2018-01. Since its merge
  base, `modernize` has changed 53 files under forums. Use it as reference
  material, not as something to rebase.
- **Proposed order:** settle the JS direction, then #9 and #16 as the first
  test of it, then #17, then whatever of #18 remains.

## Background from Brian, 2026-10-10

Years ago Brian started moving the site's theme from Blueprint CSS to the
Foundation framework, the modern choice at the time. The work happened on an hg
branch for V3 and was merged to mainline in chunks as each part was done, and
most of the site was converted. The forums were the last big piece. Personal
issues came up and his interests drifted, so the forums branch was never
finished. Now that he has Claude Code to help, he wants to finish them.

- **The Yahoo Group pages are finished.** The views render `ygroup/v3/*`.
  The three `ygroup/*.html` templates that still extend `base.html` look like
  leftovers that nothing renders (inferred from a grep, not verified).
- **The shoutbox was never converted, and the plan was to remove it.** It is not
  on the V3 base template. It is still installed, with its URLs mounted at
  `/shout/`.
- **Design intent: one shared "post box" for all user input.** That is largely
  done. What it lacks is smileys, which the old forums editor has.

### Corrections to the survey above

- The old `home.html` that extends `base.html` is
  `tools/ssg101/templates/home.html`, not part of the site. The site's
  `sg101/templates/home.html` already extends `v3/base.html`.
- `flatpages/default.html` extends `base.html`, and the flatpages app and its
  fallback middleware are still installed.
- "Too stale to rebase" overstated it. Since the merge base, `modernize`
  changed only 26 lines in the forum templates and `forums.js`. See
  `research/v3-dev-forums.md`.
