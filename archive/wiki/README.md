# The SurfGuitar101 wiki, shelved

`wiki.surfguitar101.com` ran [MoinMoin](https://moinmo.in/) 1.9 on the old host
from 2013. This is its content, captured **2026-09-04** so the Django side of the
integration could be removed without losing anything.

**The wiki is still running on jaguar as of this capture** and stays up until the
site's cutover, when `wiki.surfguitar101.com` becomes a redirect to the main site. Nothing here is live: it is a shelf copy, not a
replacement. If a new wiki is ever stood up, this is what feeds it.

## What is here

| Directory | What it is | Use it for |
|---|---|---|
| `markdown/` | 30 pages as Markdown, real nested paths | reading now; importing into a future wiki |
| `moinmoin/` | the original MoinMoin markup, **all 261 revisions** | the source of truth when a conversion looks wrong |
| `html/` | MoinMoin's own rendering of each page | settling "what did this actually look like" |
| `attachments/` | the 4 uploaded files | the images the pages reference |
| `mirrored/` | 11 images the pages hotlinked from elsewhere, copied here | so the archive does not rot on someone else's schedule |
| `static/` | MoinMoin's smiley, the one theme asset a page uses | keeping the archive self-contained |
| `MANIFEST.json` | page, revision number, size and SHA-256 of each page's markup | proving the capture is complete and current |

**`moinmoin/` is authoritative.** Everything else is derived from it. Page
directory names there keep MoinMoin's encoding, where `(2f)` is `/` — so
`BandDatabase(2f)TheRevomatics` is the page `BandDatabase/TheRevomatics`.

## How it was made

The markup came off jaguar's filesystem. The HTML was rendered by MoinMoin itself,
because it is the only thing that correctly parses its own dialect, and then
converted to Markdown — rather than by writing a MoinMoin parser, which is how a
table quietly loses a row.

**The HTML was fetched from the origin on jaguar, not through Cloudflare.** Fetched
over the public hostname, Cloudflare's email obfuscation rewrites every address on
the page into a `/cdn-cgi/l/email-protection` link — 61 occurrences across all 30
pages, and `info@therevomatics.com` and its like are simply gone from the result.
An archive taken the obvious way would have baked that in permanently.

Internal links were rewritten to relative `.md` paths so the archive stands alone
once the wiki's hostname stops resolving. All 54 of them resolve.

## Hotlinked images: 16 of them, checked one by one

The pages embed 16 images from other people's servers. Every URL was requested and
its content type checked, because a `200` can still be a parked domain:

| State | Count | Which |
|---|---|---|
| still serving an image | 11 | 7 Google Photos (the IRC screenshots), 2 from surfguitar101.com, 1 themadeira.net, 1 site icon pair |
| gone | 5 | MySpace CDN (403), `fennerphotography.com` (unreachable), `userserve-ak.last.fm` (unreachable), `therevomatics.com` (404), `satanspilgrims.com` (200 but serves HTML, not the image) |

**The 11 live ones are now mirrored** into `mirrored/` (808 KB) and the Markdown
points at the local copies. They were working when this was taken and would have
rotted on someone else's schedule; nine of the eleven were Brian's own content
anyway. They are kept separate from `attachments/` on purpose — an attachment was
uploaded *to* the wiki, a mirror was pulled *from* somewhere else, and conflating
the two would misrepresent where the file came from.

**The 5 dead ones stay as off-site links**, pointing where they always pointed.
There is nothing to mirror, and rewriting them would hide that the image is gone.
One of the five was recovered by other means — see below.

### One dead hotlink was recovered, and the wiki's own edit-log is what found it

`BandDatabase/TheRevomatics` hotlinked a photo from `therevomatics.com` that now
404s. The page also had a 6.7 MB attachment, `TheRevomatics.jpg`, that **none of its
62 revisions ever referenced** — it looked like junk. The edit-log says otherwise:

    2017-08-31 01:33:21Z  SAVE    192.0.2.2
    2017-08-31 01:35:55Z  ATTNEW  192.0.2.2  TheRevomatics.jpg

The same editor uploaded the photo 154 seconds after their last edit and never
linked it in, because the hotlink still worked in 2017. Its EXIF copyright is Joe
Weigel, one of the guitarists the page lists.

**So this archive holds the only surviving copy of the image that page was meant to
show**, and `markdown/` now displays it in place of the dead hotlink. The markup
under `moinmoin/` is untouched and still carries the original link.

## Other things worth knowing

- **One MoinMoin markup error, faithfully reproduced.** `ReverbFaq` contains a
  literal `[[...|[1]]]` where a footnote was meant. MoinMoin did not render it
  either — the archive shows the page as it actually appeared.
- **Links to pages that were never created are plain text now.** MoinMoin rendered
  those as "create this page" links; as archive links they would simply be broken,
  and the words — band names, mostly — are the part worth keeping.
- Every local link resolves: **73 page links and 16 images, zero broken.** The only
  images still pointing off-site are the four that are dead and unrecoverable.

## Checking the capture is still current

The wiki stays readable until jaguar goes away, so in principle a page could change
after this capture. Nothing has been edited since **2022-06-07**, but before the
host is destroyed, confirm rather than assume — compare each page's current
revision against `MANIFEST.json`:

    ssh brian@jaguar 'cd /svr/moin/sg101_wiki/moin_cfg/data/pages &&
      for p in $(find . -maxdepth 2 -name current | sed "s#/current##"); do
        echo "$(basename $p) $(cat $p/current)"; done | sort'

Any revision number higher than the manifest's means that page was edited and this
archive needs re-taking.

## Scale, for context

The wiki's data directory was 1.7 GB, but 1.5 GB of that was `event-log` — an
append-only record of page views, overwhelmingly from bots hammering
`action=newaccount`. Of 8,670 page directories, **30 held any content**; the rest
were empty shells from MoinMoin's shipped help system.
