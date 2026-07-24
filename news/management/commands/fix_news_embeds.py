"""
Custom management command to find and fix the old YouTube <object> embeds in the
news stories.
"""
from __future__ import print_function

from urllib.parse import urlparse
from urllib.error import HTTPError

from django.core.management.base import BaseCommand
import lxml.html

from news.models import Story
from oembed.core import get_oembed


class Command(BaseCommand):
    help = "Rewrite news stories that have old flash YouTube embeds"

    def add_arguments(self, parser):
        parser.add_argument('-p', '--preview',
                    action='store_true',
                    default=False,
                    help="find and print old embeds but don't update")

    def handle(self, *args, **options):
        self.preview = options['preview']

        qs = Story.objects.all()
        for story in qs.iterator():
            self._process_story(story)

    def _process_story(self, story):
        r1 = self._process_html(story, 'short_text')
        r2 = self._process_html(story, 'long_text')
        r3 = self._process_html(story, 'admin_content')
        if not self.preview and (r1 or r2 or r3):
            print("Updating", story.title)
            story.save()

    def _process_html(self, story, field):
        html = getattr(story, field)
        s = html.strip()
        if not s:
            return False

        root = lxml.html.fragment_fromstring(s, create_parent=True)

        for iframe in root.iter('iframe'):
            src = iframe.get('src')
            if src and src.startswith('http:'):
                print("*" * 5, "iframe with http src -", story.title)

        for obj in root.iter('object'):
            if story.version != 0:
                print("*" * 5, story.title, "bad version!")
                continue
            for param in obj.iter('param'):
                value = param.get('value')
                if value and value.startswith('http'):
                    r = urlparse(value)
                    if (r.hostname != 'www.youtube.com' and
                        r.hostname != 'www.youtube-nocookie.com'):
                        print("Unknown source hostname:", r.hostname, ";", story.title)
                        continue
                    try:
                        new_embed = self._process_path(story, r.path)
                    except HTTPError as ex:
                        print("*" * 5, story.title, ex)
                        continue
                    if not new_embed:
                        continue
                    parent = obj.getparent()
                    new_child = lxml.html.fragment_fromstring(new_embed)
                    parent.replace(obj, new_child)
                    new_html = lxml.html.tostring(root)[5:-6]
                    if self.preview:
                        print(story.title)
                        print(new_html, "\n" * 3)
                        return False

                    setattr(story, field, new_html)
                    return True


    def _process_path(self, story, path):
        if path.startswith('/v/'):
            video_id = strip_query(path[3:])
            url = "https://www.youtube.com/watch?v={}".format(video_id)
        elif path.startswith('/p/'):
            playlist_id = strip_query(path[3:])
            url = "https://www.youtube.com/playlist?list=PL{}".format(playlist_id)
        else:
            print("Unknown YouTube path:", path, ";", story.title)
            return None

        oembed = get_oembed("http://www.youtube.com/oembed", url, scheme='https')
        return oembed['html']


def strip_query(path):
    n = path.find('&')
    if n != -1:
        return path[:n]
    return path
