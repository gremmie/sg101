#!/usr/bin/env python3
"""Summarize DMARC aggregate reports from a maildir.

Reports arrive as gzipped or zipped XML attached to mail from the receiver.
This prints who reported, over what window, and one row per sending source
with its alignment results -- which is the part no dashboard shows, because
the reporter's identity lives in <report_metadata><org_name>.

The receiving domain is not in the report at all. It appears only in the
filename, so it is printed when the file still carries its original name and
omitted when it does not, rather than guessed.

Written for the Python 3.4 on the old host: no f-strings, no subprocess.run,
no os.scandir.

    python3 tools/dmarc_report.py                     # default maildir
    python3 tools/dmarc_report.py --dir /path/to/dir  # maildir or flat
    python3 tools/dmarc_report.py --file anything     # mail, .gz, .zip or .xml

Both flags take whatever you have: a raw message copied off the mail spool, or
the report attachment already extracted. The kind is detected from the bytes,
not the extension, so a file renamed in transit still works.
"""
import argparse
import datetime
import email
import gzip
import io
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

DEFAULT_MAILDIR = '/home/dmarc/mail'


def _stamp(value):
    """Epoch seconds to a readable UTC stamp."""
    try:
        moment = datetime.datetime.fromtimestamp(int(value),
                                                 datetime.timezone.utc)
    except (TypeError, ValueError):
        return str(value)
    return moment.strftime('%Y-%m-%d %H:%M:%SZ')


def _unqualify(root):
    """Drop XML namespaces from every tag in a parsed report.

    The original schema is namespace-free; the 2.0 schema puts the whole
    document in `urn:ietf:params:xml:ns:dmarc-2.0`. An unqualified find() then
    matches nothing, which yields a report that parses, prints '?' for its
    metadata and claims zero messages -- a well-formed reading of a report that
    was never read. Stripping the namespace keeps one set of paths working for
    both, and prefixed documents come out the same way.
    """
    for node in root.iter():
        if node.tag.startswith('{'):
            node.tag = node.tag.split('}', 1)[1]
    return root


def _text(node, path, default=''):
    if node is None:
        return default
    found = node.find(path)
    if found is None or found.text is None:
        return default
    return found.text.strip()


def decompress(payload, filename):
    """Return XML bytes from a report attachment, whatever its wrapper."""
    name = (filename or '').lower()
    if name.endswith('.zip') or payload[:2] == b'PK':
        archive = zipfile.ZipFile(io.BytesIO(payload))
        names = archive.namelist()
        if not names:
            raise ValueError('empty zip')
        return archive.read(names[0])
    if name.endswith('.gz') or payload[:2] == b'\x1f\x8b':
        return gzip.GzipFile(fileobj=io.BytesIO(payload)).read()
    return payload


def reports_in_bytes(raw, label=''):
    """Yield report XML from whatever this is: XML, an archive, or mail."""
    if raw[:2] == b'PK' or raw[:2] == b'\x1f\x8b':
        yield decompress(raw, label)
        return
    stripped = raw.lstrip()
    if stripped[:5] == b'<?xml' or stripped[:9] == b'<feedback':
        yield raw
        return
    for xml_bytes in reports_in_message(raw):
        yield xml_bytes


def reports_in_message(raw):
    """Yield XML bytes for every report attached to one mail message."""
    message = email.message_from_bytes(raw)
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        filename = part.get_filename() or ''
        ctype = part.get_content_type()
        looks_like_report = (
            filename.lower().endswith(('.zip', '.gz', '.xml'))
            or ctype in ('application/zip', 'application/gzip',
                         'application/x-gzip', 'application/octet-stream',
                         'text/xml', 'application/xml'))
        if not looks_like_report:
            continue
        try:
            yield decompress(payload, filename)
        except Exception as exc:                      # noqa: BLE001
            sys.stderr.write('  ! could not decompress %s: %s\n'
                             % (filename or ctype, exc))


def receiver_name(filename):
    """Return the receiver field of an aggregate report's filename.

    Reports are named `receiver!policy-domain!begin!end[!unique].ext`, and that
    filename is the only place the receiving side is written down: the body
    names the reporting organization, which is not the same thing. Yahoo files
    one report per hosted domain -- att.net, cox.net and yahoo.com arrive with
    identical <org_name>, differing only here.

    Returns '' for a name that does not follow the convention. A maildir
    delivery ID is the case that matters: it carries no receiver at all, and a
    reading must be able to tell that from one that does.
    """
    parts = os.path.basename(filename).split('!')
    if len(parts) < 4:
        return ''
    # The timestamps are what identify the convention; the last one carries
    # the extension, so compare only up to it.
    if not (parts[2].isdigit() and parts[3].split('.')[0].isdigit()):
        return ''
    return parts[0]


def summarize(xml_bytes, source=''):
    root = _unqualify(ET.fromstring(xml_bytes))
    meta = root.find('report_metadata')
    policy = root.find('policy_published')
    date_range = meta.find('date_range') if meta is not None else None

    print('=' * 78)
    if source:
        print('File     : %s' % os.path.basename(source))
        receiver = receiver_name(source)
        # Printed next to the reporter rather than instead of it, because the
        # two differ for a provider that files per hosted domain and reading
        # one as the other undercounts receivers.
        if receiver:
            print('Receiver : %s' % receiver)
    print('Reporter : %s   <%s>' % (_text(meta, 'org_name', '?'),
                                    _text(meta, 'email')))
    print('Report ID: %s' % _text(meta, 'report_id', '?'))
    if date_range is not None:
        print('Window   : %s  ->  %s' % (_stamp(_text(date_range, 'begin')),
                                         _stamp(_text(date_range, 'end'))))
    # Absent tags print as '-' rather than as the value a receiver would
    # default them to. The report says what the receiver parsed, so filling a
    # default in here makes a tag nobody published indistinguishable from one
    # that was -- and 'pct' is absent by design under the 2.0 schema, which
    # drops it.
    print('Policy   : domain=%s p=%s sp=%s adkim=%s aspf=%s pct=%s' % (
        _text(policy, 'domain', '?'), _text(policy, 'p', '?'),
        _text(policy, 'sp', '-'), _text(policy, 'adkim', '-'),
        _text(policy, 'aspf', '-'), _text(policy, 'pct', '-')))

    total = 0
    failing = 0
    print('')
    print('  %-16s %6s  %-11s %-8s %-8s  %s'
          % ('source IP', 'count', 'disposition', 'SPF', 'DKIM', 'auth detail'))
    for record in root.findall('record'):
        row = record.find('row')
        evaluated = row.find('policy_evaluated') if row is not None else None
        count = int(_text(row, 'count', '0') or 0)
        spf = _text(evaluated, 'spf', '?')
        dkim = _text(evaluated, 'dkim', '?')
        total += count
        if spf != 'pass' and dkim != 'pass':
            failing += count

        detail = []
        auth = record.find('auth_results')
        if auth is not None:
            for spf_node in auth.findall('spf'):
                # scope says which identity SPF was evaluated against: 'mfrom'
                # for the envelope sender, 'helo' when there is no usable one --
                # a bounce or other null-sender message. Without it, a domain
                # that happens to be a subdomain cannot be told apart from a
                # HELO fallback, and the difference decides which mail a DKIM
                # failure belongs to. Optional in the schema, so it may be
                # absent; say so rather than guessing.
                scope = _text(spf_node, 'scope') or '?'
                detail.append('spf:%s=%s/%s' % (_text(spf_node, 'domain', '?'),
                                                _text(spf_node, 'result', '?'),
                                                scope))
            for dkim_node in auth.findall('dkim'):
                detail.append('dkim:%s=%s' % (_text(dkim_node, 'domain', '?'),
                                              _text(dkim_node, 'result', '?')))

        print('  %-16s %6d  %-11s %-8s %-8s  %s' % (
            _text(row, 'source_ip', '?'), count,
            _text(evaluated, 'disposition', '?'), spf, dkim,
            ' '.join(detail)))

    print('')
    print('  %d messages, %d aligned on neither mechanism' % (total, failing))
    return total, failing


def maildir_files(path):
    found = []
    subdirs = [os.path.join(path, sub) for sub in ('new', 'cur')]
    # A maildir if it has new/ or cur/; otherwise take the directory as it is,
    # which is what a few files copied off the server look like.
    if not any(os.path.isdir(d) for d in subdirs):
        subdirs = [path]
    for directory in subdirs:
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            full = os.path.join(directory, name)
            if os.path.isfile(full):
                found.append(full)
    return found


def describe(raw):
    """Return (from, subject) for a file, for listing one that held no report.

    Headers fold across lines, so each is collapsed onto one line to keep the
    listing aligned.
    """
    try:
        message = email.message_from_bytes(raw)
    except Exception:                                 # noqa: BLE001
        return '', ''
    return (' '.join(message.get('From', '').split()),
            ' '.join(message.get('Subject', '').split()))


def scan(paths):
    """Summarize every report in `paths`.

    Returns the report count and a list of (path, (from, subject)) for the
    files that carried none, so the caller can account for every file it read.
    A file that cannot be parsed is named on stderr and counted among them
    rather than ending the run, since the rest of the maildir is still worth
    reading.
    """
    reports = 0
    barren = []
    for path in paths:
        with open(path, 'rb') as handle:
            raw = handle.read()
        found = 0
        try:
            for xml_bytes in reports_in_bytes(raw, path):
                summarize(xml_bytes, path)
                found += 1
        except Exception as exc:                      # noqa: BLE001
            sys.stderr.write('  ! %s: %s\n'
                             % (os.path.basename(path), exc))
        if not found:
            barren.append((path, describe(raw)))
        reports += found
    return reports, barren


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', default=DEFAULT_MAILDIR,
                        help='maildir holding the report mail (default: %s)'
                             % DEFAULT_MAILDIR)
    parser.add_argument('--file', action='append', default=[],
                        help='a report file instead: .xml, .gz or .zip')
    args = parser.parse_args()

    if args.file:
        paths = args.file
    else:
        paths = maildir_files(args.dir)
        if not paths:
            print('No mail in %s' % args.dir)
            return 0

    reports, barren = scan(paths)

    # Always reconcile files read against reports found: this maildir also
    # receives the site's error mail, so a file holding no report is routine
    # and must be named rather than silently dropped -- otherwise a report
    # that failed to parse is indistinguishable from one that never arrived.
    print('=' * 78)
    print('%d file(s) read, %d report(s).' % (len(paths), reports))
    if barren:
        print('%d file(s) carried no report:' % len(barren))
        for path, (sender, subject) in barren:
            print('  %s' % os.path.basename(path))
            if sender:
                print('      from    %s' % sender)
            if subject:
                print('      subject %s' % subject)
    return 0


if __name__ == '__main__':
    sys.exit(main())
