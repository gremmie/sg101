# Research plan

Topics raised during requirements clarification (`idea-honing.md`). Each gets
its own file in this directory when researched. Done so far:
`v3-dev-forums.md`, `upload-timing.md` (1), `playwright.md` (3),
`fragments-and-flatpages.md` (4, 5), `upload-error-message.md` (6),
`foundation-upgrade.md` (7), `jquery3.md` (8). **All topics done
2026-10-10.**

| # | Topic | Raised by | Question to answer |
|---|---|---|---|
| 1 | Upload timing **(done)** | Q4 | How long does one large phone photo take through `upload_ajax_v3`, end to end (resize, thumbnail, two S3 puts)? Is it well inside gunicorn's 30 s? |
| 2 | ~~jQuery after `base.html`~~ **superseded by Q13 and topic 8** | Q1, Q5 | Once `base.html` is retired, jQuery 2.2.4 from Google's CDN is the only copy left. Should it be served from the site, and at what version? Folded into topic 7 if the upgrade goes ahead. |
| 3 | Playwright in Docker and CI **(done)** | Q9 | What it adds to the test image and to the CI run; how it runs against Django's live server under `docker_test` settings. |
| 4 | Shared fragments **(done)** | `v3-dev-forums.md` | `v3-dev` converted `accounts/user_stats_tag`, `bio/member_flags_tag`, `core/max_users_tag` and `core/whos_online_tag`. Which other pages use them, and would porting change those pages? |
| 5 | Flatpages **(done)** | Q5 | Are the five flatpage rows (`/about/`, `/colophon/`, the two policies, `/store/`) served by the `fixed` and `store` apps instead, so the flatpages app can go? |
| 6 | Upload error message **(done)** | Q4 | `upload_ajax_v3` puts form errors under `msg`; `post_box.js` reads `error_msg`. Does a rejected upload (over quota, not an image) show an empty error? |
| 7 | Foundation 6.3.1 → 6.9.0 **(done; not upgrading, Q13)** | Q12 | What changed in 6.4–6.9 for the grid and components the site uses (float grid `row`/`columns`, cards, reveal, menus, dropdowns, off-canvas, callouts)? What breaks in the Sass build and the JS? What does it cost, and does it belong in this project or its own? It would bring jQuery to ≥ 3.6 (topic 2). |
| 8 | jQuery 3 compatibility **(done)** | Q13 | Do Foundation 6.3.1 (Reveal, Toggler, ResponsiveToggle/Menu, Drilldown, DropdownMenu, Orbit), jQuery Form v20130916, jQuery UI 1.11.0 and jQuery Cycle 3.0.3 work on jQuery 3.x? Which site scripts use APIs removed in 3.0? Which 3.x version, and is jQuery Migrate needed while checking? |
