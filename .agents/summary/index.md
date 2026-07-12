# SG101 Knowledge Base Index

This directory (`.agents/summary/`) contains generated documentation for
the **sg101** codebase (the Django app behind SurfGuitar101.com). It is
intended as the primary file an AI assistant loads into context before
answering questions about this repo — it summarizes what each other file
contains so you can decide which ones to actually read.

**Also see the root-level `AGENTS.md`** — a shorter, navigation-focused
version of this material meant to always be in context. This index and
its linked files go deeper.

## How to use this index

1. Read this file first.
2. Based on the question, open only the specific file(s) below that are
   relevant — you don't need to load all of them.
3. If the question is about a specific app (e.g. "how does the forums
   permission system work?"), start with [components.md](components.md)
   to confirm which app owns that behavior, then check
   [architecture.md](architecture.md) or [workflows.md](workflows.md)
   for the cross-cutting pattern it follows.

## Files in this knowledge base

| File | Contents | Read this when... |
|---|---|---|
| [codebase_info.md](codebase_info.md) | What the project is, language/framework versions, repo layout diagram, third-party service list | You need a first orientation to the whole codebase |
| [architecture.md](architecture.md) | Deployment topology diagram, settings module hierarchy (`base`/`local`/`production`/`test`), shared app conventions, cross-cutting design patterns (public/pending split, signal-driven decoupling, `core` as shared kernel), the `messages` app-label collision gotcha | You're changing settings, adding a new app, or need to understand *why* the code is structured the way it is |
| [components.md](components.md) | Every top-level app, grouped (platform/shared, community/content, media/surf-specific), with a one-paragraph description of each | You need to find which app owns a piece of functionality, or want a directory-by-directory tour |
| [interfaces.md](interfaces.md) | Root URL routing map, RSS feeds, full-text search endpoints, external service integrations (PayPal IPN, S3, Google Calendar OAuth2, oEmbed, reCAPTCHA, the wiki cookie bridge, fail2ban) | You're adding a route, integrating a new external service, or tracing an HTTP entry point |
| [data_models.md](data_models.md) | Forums ER diagram, `UserProfile` fields, the pending/public model-split pattern (`downloads`/`weblinks`/`news`), other notable models, the raw-text/rendered-HTML sibling-field pattern | You're adding/changing a model or writing a migration |
| [workflows.md](workflows.md) | Celery beat schedule, the two async mechanisms (Celery vs. `queued_search`) and how they relate, the search-indexing signal flow, moderation/pending-content flow, Who's-Online tracking, the wiki auth cookie sequence, PayPal donation flow, deployment via Fabric | You're debugging a background job, a search-indexing gap, or the deploy process |
| [dependencies.md](dependencies.md) | Every pinned dependency grouped by purpose, with special callout for the three VCS-pinned (non-PyPI) packages | You're upgrading a dependency or unsure what a third-party import is for |
| [review_notes.md](review_notes.md) | Known documentation gaps and consistency notes from generating this knowledge base | You suspect these docs might be incomplete or stale in a specific area |

## Example queries and where to look

- *"Where do I add a new page like /about?"* → [interfaces.md](interfaces.md) (root URL routing), then `sg101/urls.py` + `core/views.py` (`FixedView`) directly.
- *"How does content get moderated before going public?"* → [workflows.md](workflows.md) § Moderation, [data_models.md](data_models.md) § Pending/public pattern.
- *"Why isn't my new model showing up in search results?"* → [workflows.md](workflows.md) § Search indexing flow — check `custom_search/receivers.py`'s `signal_chain`.
- *"What needs to be in `secrets.json` to run this locally?"* → [architecture.md](architecture.md) § Settings module hierarchy.
- *"What does the `queues` package do and where does it come from?"* → [dependencies.md](dependencies.md) § Pinned VCS dependencies, [workflows.md](workflows.md) § Two async mechanisms.
