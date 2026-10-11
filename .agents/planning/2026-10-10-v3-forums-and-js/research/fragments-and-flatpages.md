# Research topics 4 and 5: shared fragments, and flatpages

Researched 2026-10-10.

## Topic 4: the four shared fragments `v3-dev` converted

**Each is used only on the forums index**, so porting `v3-dev`'s versions
changes no other page.

| Fragment | Inclusion tag | Called from |
|---|---|---|
| `accounts/user_stats_tag.html` | `user_stats` (`accounts_tags.py`) | `forums/index.html` |
| `bio/member_flags_tag.html` | `member_flags` (`bio_tags.py`) | `accounts/user_stats_tag.html`, so the forums index |
| `core/max_users_tag.html` | `max_users` (`core_tags.py`) | `forums/index.html` |
| `core/whos_online_tag.html` | `whos_online` (`core_tags.py`) | `forums/index.html` |

Method: found each tag's function from its `@register.inclusion_tag`, then
grepped `sg101/templates` for `{% <tag>`.

## Topic 5: flatpages

**The flatpages app serves nothing. All five rows are shadowed by real URL
routes**, and `FlatpageFallbackMiddleware` only answers a 404.

| Path | Resolves to (dev, `django.urls.resolve`) | Status |
|---|---|---|
| `/about/` | `FixedView`, `about` | 200 |
| `/colophon/` | `FixedView`, `colophon` | 200 |
| `/policy/privacy/` | `FixedView`, `privacy` | 200 |
| `/policy/tos/` | `FixedView`, `tos` | 200 |
| `/store/` | `sg101.views`, `store` | 200 |

The rows are from the dev database, a copy of production. Nothing else
references flatpages: no `get_flatpages` tag, no links. The only code is the
admin customisation in `core/admin.py` and the two settings entries
(`INSTALLED_APPS`, `MIDDLEWARE`).

**So Q5's "flatpages go too if they turn out to be dead" applies:** remove
`django.contrib.flatpages` and its middleware, the admin class, and
`flatpages/default.html`, and archive the five rows first. Also check that
`django.contrib.sites` is still needed by something else before touching it.
Flatpages requires it, but so do other apps.

**Moved out of this project:** filed as GitHub issue #33 (2026-10-10), with
the steps and the deploy order.

## Found in passing: navigation tests that assume two base templates

`core/tests/test_navigation.py` and `gcalendar/tests/test_navigation.py` say
the site "runs two live designs and both need the link", and assert the menu
entries on both `base.html` and `v3/base.html`. Retiring `base.html` (Q10
step 8) has to change these tests too, not just delete the template.
