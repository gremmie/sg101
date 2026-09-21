#!/usr/bin/env python3
"""Fetch DMARC aggregate reports out of Gmail into a local directory.

Reports are published to two `rua` destinations. Cloudflare's copy keeps the
totals but not the detail; the copy delivered to `admin@surfguitar101.com` is
forwarded to Gmail and is the only one carrying reporter identity, Report-IDs,
`envelope_to` and the per-source rows. Saving it by hand is what lost two of the
four reports filed for the 2026-09-07 window. This does that step instead.

Unlike `dmarc_report.py` -- written for the Python 3.4 on the old host -- this
runs on the Mac and targets 3.12+. jaguar is being decommissioned; do not port
the sibling's no-f-strings style over here.

    python3 tools/dmarc_fetch.py                 # since the corpus, minus a margin
    python3 tools/dmarc_fetch.py --dry-run -v    # decide nothing, explain everything
    python3 tools/dmarc_fetch.py --all           # the whole reporting era
    python3 tools/dmarc_fetch.py --since 2026-09-01 --dir /tmp/replay

Reads the App Password from the login keychain, so no secret lands in a file or
in the environment:

    security add-generic-password -a you@gmail.com -s dmarc-fetch -w

Omitting the value after `-w` makes it prompt, keeping it out of shell history.

The mailbox is only ever opened read-only and bodies are fetched with
BODY.PEEK, so nothing here can mark, move or delete mail. That matters more than
it looks: reading the spam folder by hand once removed a message from it.
"""
import argparse
import email
import email.policy
import gzip
import hashlib
import imaplib
import io
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

IMAP_HOST = 'imap.gmail.com'
KEYCHAIN_SERVICE = 'dmarc-fetch'
DEFAULT_DIR = Path.home() / 'dmarc'

# How far back to look before the newest window already held. Reports arrive
# late -- Microsoft's 09-07 report landed four days after the window closed --
# so the corpus edge is not the arrival edge.
LOOKBACK_DAYS = 14

# Pause for confirmation above this many messages, when run interactively.
CONFIRM_ABOVE = 500

# RFC 7489 7.2.1.1 specifies this subject format. It is a SHOULD, so it is a
# default to be audited, never an assumption. See --audit.
SUBJECT_TERM = 'Report Domain'

# Hard floor on every search. The modernization project began 2026-07-04 and the
# `_dmarc` record was not published until mid-August, so no aggregate report for
# this domain can predate it -- the earliest window in the corpus begins
# 2026-08-22, 49 days later. This is what stops `--all` meaning "download the
# entire mailbox". Moving it earlier is a deliberate edit, not a flag, because
# the only thing earlier than this floor is mail that cannot be a report.
EARLIEST = datetime(2026, 7, 4, tzinfo=timezone.utc)

# Gmail's folder names are localized; find them by RFC 6154 special-use flag and
# fall back to the English names only if the server offers no flags at all.
SPECIAL_USE = {'all': '\\All', 'spam': '\\Junk', 'trash': '\\Trash'}
FALLBACK_FOLDERS = {'all': '[Gmail]/All Mail', 'spam': '[Gmail]/Spam',
                    'trash': '[Gmail]/Trash'}

MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


def imap_date(when: datetime) -> str:
    """IMAP SEARCH wants DD-Mon-YYYY with an English month, whatever the locale."""
    return '%02d-%s-%d' % (when.day, MONTHS[when.month - 1], when.year)


def keychain_password(account: str, service: str) -> str:
    """Read the App Password from the login keychain.

    The first read from a new binary raises the usual macOS prompt. That is the
    intended friction: this is a full mail credential, not a scoped one.
    """
    proc = subprocess.run(
        ['security', 'find-generic-password', '-a', account, '-s', service, '-w'],
        capture_output=True, text=True)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or 'not found'
        raise SystemExit(
            'No keychain entry for account %r service %r (%s).\n'
            'Add one with:\n'
            '    security add-generic-password -a %s -s %s -w'
            % (account, service, detail, account, service))
    return proc.stdout.strip()


def is_feedback(blob: bytes) -> bool:
    """True if these bytes parse as a DMARC aggregate report.

    The root tag is the whole test. The 2.0 schema puts the document in a
    namespace, so compare the local name -- the same trap `_unqualify` exists
    for in the reporting tool, where a namespaced report parsed fine and read as
    zero messages.
    """
    try:
        root = ET.fromstring(blob)
    except ET.ParseError:
        return False
    return root.tag.split('}', 1)[-1] == 'feedback'


def looks_like_report(blob: bytes) -> bool:
    """Detect a report from the bytes, never from the sender or the extension.

    A sender allowlist is how a *new* reporter goes missing, and this corpus
    keeps gaining them -- `Enterprise Outlook` filed for the first time on
    2026-09-13, and Postmark is expected once outbound moves.
    """
    if blob[:2] == b'\x1f\x8b':
        try:
            return is_feedback(gzip.decompress(blob))
        except (OSError, EOFError):
            return False
    if blob[:2] == b'PK':
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as archive:
                return any(is_feedback(archive.read(n)) for n in archive.namelist())
        except (zipfile.BadZipFile, RuntimeError, KeyError):
            return False
    return is_feedback(blob)


def attachments(msg: email.message.Message):
    """Yield (filename, payload) for every leaf part, at any nesting depth.

    Cloudflare Email Routing forwards these, so a report can arrive wrapped in a
    message/rfc822 part rather than sitting at the top level. walk() descends
    into those; a scan of the top level alone would miss them.
    """
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get_content_type() == 'message/rfc822':
            continue
        try:
            payload = part.get_payload(decode=True)
        except Exception:
            continue
        if payload:
            yield part.get_filename(), payload


def safe_name(name: str | None) -> str | None:
    """Reduce an attachment name to a bare basename, or reject it.

    The name is load bearing and is never invented: the receiving domain appears
    nowhere in the report body, only here, which is why the reporting tool omits
    it rather than guessing when a file has been renamed.
    """
    if not name:
        return None
    name = os.path.basename(name.replace('\\', '/')).strip()
    if not name or name in ('.', '..') or name.startswith('.'):
        return None
    return name


def newest_window_end(directory: Path) -> int | None:
    """Latest window-end epoch across the corpus, read from the filenames.

    `receiver!domain!begin!end[!unique].ext` -- GMX appends a unique token, so
    take field 3 and stop at the first dot.
    """
    newest = 0
    for path in directory.glob('*!*!*'):
        fields = path.name.split('!')
        if len(fields) < 4:
            continue
        end = fields[3].split('.', 1)[0]
        if end.isdigit():
            newest = max(newest, int(end))
    return newest or None


def resolve_since(directory: Path, args) -> str:
    """Work out the SEARCH floor. Stateless, and never unbounded.

    A high-water mark stored on disk would skip exactly the batch this tool
    exists to recover, so the window is re-derived from the corpus every run. A
    month between runs costs nothing.

    Every path is clamped to EARLIEST. `--all` means "the whole reporting era",
    not "the whole mailbox".
    """
    floor = EARLIEST
    if args.all:
        chosen = EARLIEST
    elif args.since:
        try:
            chosen = datetime.strptime(args.since, '%Y-%m-%d').replace(
                tzinfo=timezone.utc)
        except ValueError:
            raise SystemExit('--since wants YYYY-MM-DD, got %r' % args.since)
    else:
        newest = newest_window_end(directory)
        if newest is None:
            raise SystemExit(
                '%s holds no reports to date from -- pass --since YYYY-MM-DD '
                'or --all.' % directory)
        chosen = (datetime.fromtimestamp(newest, timezone.utc)
                  - timedelta(days=LOOKBACK_DAYS))
    if chosen < floor:
        if args.since:
            print('Note: --since %s is before the first possible report; '
                  'using %s.' % (args.since, imap_date(floor)))
        chosen = floor
    return imap_date(chosen)


def list_folders(conn: imaplib.IMAP4_SSL, wanted: list[str]) -> list[str]:
    """Find the mailboxes to scan by special-use flag.

    INBOX alone would reproduce the gap being fixed, and at least one
    report-adjacent message has been found in spam.
    """
    typ, data = conn.list()
    if typ != 'OK':
        return [FALLBACK_FOLDERS[w] for w in wanted]
    flags_wanted = {SPECIAL_USE[w] for w in wanted}
    found = []
    for line in data:
        if isinstance(line, bytes):
            line = line.decode('utf-8', 'replace')
        match = re.match(r'\((?P<flags>[^)]*)\)\s+"[^"]*"\s+(?P<name>.+)', line)
        if not match:
            continue
        flags = set(match.group('flags').split())
        if not flags & flags_wanted:
            continue
        name = match.group('name').strip()
        if name.startswith('"') and name.endswith('"'):
            name = name[1:-1]
        found.append(name)
    return found or [FALLBACK_FOLDERS[w] for w in wanted]


def gmail_query(subject: str | None) -> str:
    """The server-side narrowing.

    `has:attachment` alone cannot miss a report, since every report is an
    attachment. Adding the RFC 7489 subject is much narrower and much cheaper --
    and it *can* miss, because that subject format is a SHOULD. `--audit`
    measures the difference instead of assuming it away.
    """
    terms = ['has:attachment']
    if subject:
        terms.append('subject:\\"%s\\"' % subject)
    return ' '.join(terms)


def search(conn: imaplib.IMAP4_SSL, since: str | None,
           query: str) -> tuple[list[bytes], bool]:
    """UIDs of candidate messages, and whether the server narrowed the search.

    `X-GM-RAW` narrows server-side without naming a reporter, so the shape test
    still decides what counts. If the server has no Gmail extensions the
    fallback is every message in the window -- which the caller must be told
    about rather than discovering from the download size.
    """
    criteria = ['SINCE', since] if since else []
    try:
        typ, data = conn.uid('SEARCH', None,
                             *(criteria + ['X-GM-RAW', '"%s"' % query]))
        if typ == 'OK' and data and data[0] is not None:
            return data[0].split(), True
    except imaplib.IMAP4.error:
        pass
    typ, data = conn.uid('SEARCH', None, *(criteria or ['ALL']))
    if typ == 'OK' and data and data[0] is not None:
        return data[0].split(), False
    return [], False


def sizes(conn: imaplib.IMAP4_SSL, uids: list[bytes]) -> dict[bytes, int]:
    """RFC822.SIZE per UID, so a huge message is skipped before it is downloaded.

    Fails open: a UID whose size cannot be parsed is simply absent from the
    result and gets fetched. Missing a report to save bandwidth would defeat the
    point of the tool.
    """
    found: dict[bytes, int] = {}
    for start in range(0, len(uids), 500):
        chunk = b','.join(uids[start:start + 500])
        try:
            typ, data = conn.uid('FETCH', chunk, '(RFC822.SIZE)')
        except imaplib.IMAP4.error:
            continue
        if typ != 'OK':
            continue
        for item in data:
            if isinstance(item, tuple):
                item = item[0]
            if not isinstance(item, (bytes, bytearray)):
                continue
            uid = re.search(rb'UID (\d+)', bytes(item))
            size = re.search(rb'RFC822\.SIZE (\d+)', bytes(item))
            if uid and size:
                found[uid.group(1)] = int(size.group(1))
    return found


def fetch_body(conn: imaplib.IMAP4_SSL, uid: bytes) -> bytes | None:
    """BODY.PEEK so the message is never marked \\Seen, read-only or not."""
    typ, data = conn.uid('FETCH', uid, '(BODY.PEEK[])')
    if typ != 'OK' or not data:
        return None
    for chunk in data:
        if isinstance(chunk, tuple) and len(chunk) > 1:
            return chunk[1]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Fetch DMARC aggregate reports from Gmail into a directory.')
    parser.add_argument('-a', '--account', required=True,
                        help='Gmail address; also the keychain account')
    parser.add_argument('-d', '--dir', type=Path, default=DEFAULT_DIR,
                        help='destination directory (default: %s)' % DEFAULT_DIR)
    parser.add_argument('-s', '--service', default=KEYCHAIN_SERVICE,
                        help='keychain service name (default: %s)' % KEYCHAIN_SERVICE)
    parser.add_argument('--since', metavar='YYYY-MM-DD',
                        help='override the derived search floor')
    parser.add_argument('--all', action='store_true',
                        help='search the whole reporting era (from %s), '
                             'ignoring the corpus; never the whole mailbox'
                             % EARLIEST.date())
    parser.add_argument('--include-trash', action='store_true',
                        help='also scan the trash')
    parser.add_argument('--max-bytes', type=int, default=2 * 1024 * 1024,
                        metavar='N',
                        help='skip messages larger than N bytes without '
                             'downloading them (default 2MB, ~100x the largest '
                             'report mail seen; 0 disables)')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='do not pause before a large scan')
    parser.add_argument('--subject', default=SUBJECT_TERM, metavar='TEXT',
                        help='narrow the server-side search to this subject '
                             'text (default %r); pass an empty string to '
                             'search on attachments alone' % SUBJECT_TERM)
    parser.add_argument('--audit', action='store_true',
                        help='also run the broad attachment-only search and '
                             'report any report the subject filter would have '
                             'missed')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='report what would be written, write nothing')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    directory = args.dir.expanduser()
    if not directory.is_dir():
        raise SystemExit('Not a directory: %s' % directory)

    since = resolve_since(directory, args)
    password = keychain_password(args.account, args.service)

    wanted = ['all', 'spam'] + (['trash'] if args.include_trash else [])

    written: list[str] = []
    skipped = 0
    conflicts: list[str] = []
    unnamed: list[str] = []
    seen_this_run: set[str] = set()
    scanned = 0

    conn = imaplib.IMAP4_SSL(IMAP_HOST)
    try:
        conn.login(args.account, password)
        del password
        folders = list_folders(conn, wanted)
        print('Scanning %s since %s' % (', '.join(folders), since or 'the beginning'))

        # Survey first. A sweep with no date floor can be the whole mailbox, and
        # that should be a number on the screen before it is a download.
        plan: list[tuple[str, list[bytes]]] = []
        oversized = 0
        unnarrowed = []
        audit_extra: dict[str, list[bytes]] = {}
        for folder in folders:
            typ, _ = conn.select('"%s"' % folder, readonly=True)
            if typ != 'OK':
                print('  ! cannot open %s, skipping' % folder, file=sys.stderr)
                continue
            uids, narrowed = search(conn, since, gmail_query(args.subject))
            if not narrowed:
                unnarrowed.append(folder)
            if args.audit and narrowed and args.subject:
                broad, broad_ok = search(conn, since, gmail_query(None))
                if broad_ok:
                    audit_extra[folder] = [u for u in broad if u not in set(uids)]
            if args.max_bytes and uids:
                known = sizes(conn, uids)
                keep = [u for u in uids if known.get(u, 0) <= args.max_bytes]
                oversized += len(uids) - len(keep)
                uids = keep
            plan.append((folder, uids))
            print('  %s: %d message(s) to scan%s'
                  % (folder, len(uids), '' if narrowed else '  [NOT NARROWED]'))

        if unnarrowed:
            print('\nWARNING: this server did not support a has:attachment '
                  'search in %s,\n         so every message in the window will '
                  'be downloaded to be checked.' % ', '.join(unnarrowed))
        if oversized:
            print('Skipped %d message(s) over %d bytes without downloading them.'
                  % (oversized, args.max_bytes))

        total = sum(len(u) for _, u in plan)
        if total > CONFIRM_ABOVE and not args.yes and sys.stdin.isatty():
            answer = input('\nAbout to download %d messages. Continue? [y/N] '
                           % total)
            if answer.strip().lower() not in ('y', 'yes'):
                print('Stopped; nothing was downloaded.')
                return 0
        print()

        for folder, uids in plan:
            typ, _ = conn.select('"%s"' % folder, readonly=True)
            if typ != 'OK':
                continue
            for uid in uids:
                raw = fetch_body(conn, uid)
                if raw is None:
                    continue
                scanned += 1
                msg = email.message_from_bytes(raw, policy=email.policy.default)
                for name, payload in attachments(msg):
                    if not looks_like_report(payload):
                        continue
                    filename = safe_name(name)
                    if filename is None:
                        # Never invent a receiver field; make the gap loud instead.
                        digest = hashlib.sha256(payload).hexdigest()[:16]
                        filename = '_unnamed_%s.xml' % digest
                        unnamed.append(filename)
                    if filename in seen_this_run:
                        continue
                    seen_this_run.add(filename)
                    dest = directory / filename
                    if dest.exists():
                        if hashlib.sha256(dest.read_bytes()).digest() == \
                           hashlib.sha256(payload).digest():
                            skipped += 1
                            if args.verbose:
                                print('    = %s' % filename)
                        else:
                            conflicts.append(filename)
                        continue
                    if not args.dry_run:
                        dest.write_bytes(payload)
                    written.append(filename)
                    print('    + %s%s' % (filename, ' (dry run)' if args.dry_run else ''))
        if audit_extra:
            print()
            missed = []
            checked = 0
            for folder, uids in audit_extra.items():
                if not uids:
                    continue
                typ, _ = conn.select('"%s"' % folder, readonly=True)
                if typ != 'OK':
                    continue
                known = sizes(conn, uids) if args.max_bytes else {}
                for uid in uids:
                    if args.max_bytes and known.get(uid, 0) > args.max_bytes:
                        continue
                    raw = fetch_body(conn, uid)
                    if raw is None:
                        continue
                    checked += 1
                    msg = email.message_from_bytes(raw, policy=email.policy.default)
                    for name, payload in attachments(msg):
                        if looks_like_report(payload):
                            missed.append((folder, safe_name(name) or '?',
                                           str(msg.get('Subject', ''))[:60]))
                            break
            print('AUDIT: checked %d message(s) that have an attachment but do '
                  'not match subject %r.' % (checked, args.subject))
            if missed:
                print('       %d of them carry a DMARC report, so the subject '
                      'filter WOULD HAVE MISSED them:' % len(missed))
                for folder, name, subject in missed:
                    print('         %s  %s  [%s]' % (folder, name, subject))
                print('       Re-run without --subject, or widen it.')
            else:
                print('       None carried a report. On this mailbox and this '
                      'window the subject filter is lossless.')
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    print()
    print('Scanned %d message(s): %d new, %d already held, %d conflict(s).'
          % (scanned, len(written), skipped, len(conflicts)))
    if unnamed:
        print('WARNING: %d report(s) arrived without a usable filename. The '
              'receiving domain lives only in that name, so these read without '
              'one:' % len(unnamed))
        for name in unnamed:
            print('  %s' % name)
    if conflicts:
        print('WARNING: %d file(s) differ from the copy already held and were '
              'NOT overwritten. Reports are immutable, so this should not '
              'happen:' % len(conflicts))
        for name in conflicts:
            print('  %s' % name)
    total = sum(1 for p in directory.iterdir() if p.is_file() and not p.name.startswith('.'))
    print('%s now holds %d file(s).' % (directory, total))
    return 1 if conflicts else 0


if __name__ == '__main__':
    sys.exit(main())
