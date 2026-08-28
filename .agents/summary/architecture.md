# Architecture

**Generated 2026-08-27.**

## Runtime shape

```mermaid
graph TB
    B[Browser] --> CF[Cloudflare<br/>DNS, CDN, TLS, WAF]
    CF --> AP[Apache + mod_wsgi<br/>mod_remoteip rewrites REMOTE_ADDR]
    AP --> DJ[Django 5.2 / Python 3.12]
    DJ --> PG[(PostgreSQL 16<br/>relational + full-text search)]
    DJ --> RD[(Redis<br/>cache, Celery broker, Who's Online)]
    DJ --> S3[Amazon S3<br/>user photos]
    DJ --> PM[Postmark<br/>transactional email]
    CE[Celery worker] --> PG
    CE --> RD
    BT[Celery beat] --> RD
    DJ -. enqueue .-> RD
    RD -. consume .-> CE
```

**`mod_remoteip` is load-bearing and easy to miss.** Every `REMOTE_ADDR` reader
in the codebase — `antispam`, `accounts`, `forums`, `comments`, `downloads`,
`donations` — is correct only because Apache rewrites it from `CF-Connecting-IP`
for Cloudflare's ranges. Nothing in the repo performs that rewrite and Django
does not do it itself. `core.functions.get_ip` documents this deliberately and
reads `REMOTE_ADDR` only, never `X-Forwarded-For`, which any client can forge.

## Dependency direction

```mermaid
graph LR
    CORE[core<br/>depends on nothing in-repo]
    FEATS[feature apps<br/>forums, news, downloads, ...]
    SEARCH[search]
    ANTI[antispam]
    FEATS --> CORE
    SEARCH --> CORE
    ANTI --> CORE
    SEARCH -. signals .-> FEATS
    FEATS -. spam checks .-> ANTI
```

`core` is the shared kernel: importable by anything, importing nothing from the
repo. Treat that as an invariant — it is what keeps the app graph acyclic.

**`antispam` has two shapes inside it.** `antispam/utils.py` reaches into `bio`,
`comments`, `forums` and `user_photos`, so importing it drags four app graphs
along. `antispam/decorators.py` and `antispam/turnstile.py` are deliberately
narrow — stdlib and settings only — so form modules can use them without that.
Follow the narrow shape when adding something with callers in several apps.

## Search

Native PostgreSQL full-text search, built in Step 12 to replace a
Xapian/Haystack stack that had been disabled for years and was removed wholesale
in Step 4.

```mermaid
graph LR
    M[Model save/delete] --> SIG[search/receivers.py]
    SIG --> T[Celery task]
    T --> IDX[search/indexer.py]
    IDX --> DOC[(SearchDocument<br/>tsvector)]
    Q[search/query.py] --> DOC
    REC[search/reconcile.py<br/>weekly sweep] --> DOC
```

Eight document types over one index. Maintenance is incremental via signals
through Celery, and a weekly sweep reconciles drift rather than assuming the
signals never miss.

## Settings

```mermaid
graph TD
    BASE[base.py<br/>everything shared] --> LOCAL[local.py]
    BASE --> DOCKER[docker.py]
    BASE --> DTEST[docker_test.py]
    BASE --> PROD[production.py]
    BASE --> TEST[test.py]
    DBH[databases.py<br/>shared helper] -.-> BASE
```

**12-factor since Step 3.** Every setting reads the environment through
`django-environ`. `.env` is git-ignored and loaded by Compose via `env_file:`;
`.env.example` is committed and is what CI seeds itself from. **There is no
`secrets.json`** — retired in Step 3, and any doc mentioning it is stale.

`manage.py` defaults to `sg101.settings.local`.

## Content rendering

Markdown renders **at save time**, not per request, into a sibling field:
`UserProfile.profile_text` → `profile_html`, `Post.body` → `html`. Changing how
a field renders therefore needs a data migration to re-render existing rows — a
template change alone will not do it. Rendering lives in `core/markup.py`.

## Moderation

`downloads`, `weblinks` and `news` use **split models rather than a boolean
flag**: a `*Base` model subclassed into a `Pending*` model and the live public
model (`DownloadBase` → `PendingDownload` / `Download`), each with its own
manager. Extend that pattern rather than adding an `is_approved` field.
