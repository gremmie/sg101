#!/usr/bin/env python
# Copyright (C) 2021 by Brian Neal.

"""This file contains the main routine for the SG101 MP3 Comp Tool."""

import argparse
import eyed3
import json
import os.path
import re


DESC = """SG101 MP3 Comp Tool"""
TITLE_RE = re.compile(r'^(\d+)\s+-\s+(.+)"(.+)"$')

def process_mp3(mp3, args):
    title = mp3['fields']['title']
    print(f'Processing {title}...')
    m = TITLE_RE.match(title)
    track_num = int(m[1])
    artist = m[2].strip()
    title = m[3]
    filename = mp3['fields']['file'].split('/')[-1]
    filepath = os.path.join(args.mp3_dir, filename)

    mp3file = eyed3.load(filepath)
    if mp3file.tag is None:
        mp3file.tag = eyed3.id3.tag.Tag()
    mp3file.tag.clear()
    mp3file.tag.title = title
    mp3file.tag.artist = artist
    mp3file.tag.album  = args.album
    mp3file.tag.recording_date = args.recording_date
    mp3file.tag.track_num = track_num
    mp3file.tag.genre = 'Instrumental Rock'
    mp3file.tag.save()


def main(argv=None):
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument('json', metavar='JSON',
                        help='JSON file to control the tagging process')
    parser.add_argument('-d', '--mp3-dir', default='.',
                        help='directory to find MP3 files')
    parser.add_argument('-a', '--album',
                        default='SurfGuitar101.com 2021 MP3 Compilation',
                        help='album name tag value')
    parser.add_argument('-r', '--recording-date', default='2021',
                        help='recording date tag value')

    args = parser.parse_args(args=argv)

    with open(args.json, 'r') as fp:
        mp3data = json.load(fp)

    for mp3 in mp3data:
        process_mp3(mp3, args)

if __name__ == '__main__':
    main()
