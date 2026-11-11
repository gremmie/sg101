"""Tests for the forums' template tags."""
import re

from django.contrib.auth.models import User
from django.http import QueryDict
from django.template import Context, Template
from django.test import TestCase

from forums.forms import NewPostForm, PostForm
from forums.models import Attachment, Forum
from forums.tests.test_moderation import add_post, make_topic
from oembed.models import Oembed


def make_embed(name):
    return Oembed.objects.create(
        url='https://www.youtube.com/watch?v=%s' % name,
        type=Oembed.VIDEO, title=name, width=480, height=270,
        html='<iframe width="480" height="270" title="%s"></iframe>' % name)


class PostAttachmentsTestCase(TestCase):
    """The attachment list a posting form arrives with."""
    fixtures = ['forums.json']

    def setUp(self):
        # Created a then b, so b has the higher id: an order that follows the
        # ids is not the order asked for.
        self.a = make_embed('first')
        self.b = make_embed('second')

    def render(self, form):
        template = Template('{% load forum_tags %}{% post_attachments form %}')
        return template.render(Context({'form': form}))

    def entries(self, rendered):
        """The (embed title, attachment id) of each entry, in page order."""
        return re.findall(
            r'<div class="forum-attachment"><iframe [^>]*title="(\w+)"></iframe></div>'
            r'\s*<button [^>]*class="[^"]*attachment-remove[^"]*"[^>]*>\s*Remove\s*</button>'
            r'\s*<input type="hidden" name="attachment" value="(\d+)"',
            rendered)

    def test_a_new_form_has_an_empty_list(self):
        rendered = self.render(NewPostForm())
        self.assertRegex(rendered, r'<div [^>]*data-attachments[^>]*>\s*</div>')
        self.assertEqual(self.entries(rendered), [])

    def test_a_posted_form_lists_its_known_ids_in_posted_order(self):
        data = QueryDict(mutable=True)
        data.setlist('attachment', [str(self.b.pk), '999999', str(self.a.pk)])
        data['topic_id'] = '1'
        rendered = self.render(NewPostForm(data))
        self.assertEqual(self.entries(rendered),
                         [('second', str(self.b.pk)), ('first', str(self.a.pk))])

    def test_an_edit_form_lists_the_posts_attachments_in_their_order(self):
        user = User.objects.create_user('pjmoto', '', 'pw')
        topic = make_topic(Forum.objects.get(slug='shallow-end'), user)
        post = add_post(topic, user)
        # Saved in neither id order nor embed order.
        Attachment.objects.create(post=post, embed=self.a, order=1)
        Attachment.objects.create(post=post, embed=self.b, order=0)
        rendered = self.render(PostForm(instance=post))
        self.assertEqual(self.entries(rendered),
                         [('second', str(self.b.pk)), ('first', str(self.a.pk))])

    def test_a_posted_edit_form_lists_what_was_posted_not_what_was_saved(self):
        # Re-shown after an error: the member had removed a video.
        user = User.objects.create_user('pjmoto', '', 'pw')
        topic = make_topic(Forum.objects.get(slug='shallow-end'), user)
        post = add_post(topic, user)
        Attachment.objects.create(post=post, embed=self.a, order=0)
        Attachment.objects.create(post=post, embed=self.b, order=1)
        data = QueryDict(mutable=True)
        data.setlist('attachment', [str(self.b.pk)])
        rendered = self.render(PostForm(data, instance=post))
        self.assertEqual(self.entries(rendered), [('second', str(self.b.pk))])
