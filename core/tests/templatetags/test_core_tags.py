"""
Unit tests for the core template tags.

"""
from datetime import date, datetime, timedelta
import os
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.http import QueryDict
from django.template import Context, Template
from django.test import TestCase
from mock import call, patch, Mock

from news.forms import AddNewsForm


class BoolIconTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% bool_icon my_flag %}')

    def test_renders_true(self):
        rendered = self.TEMPLATE.render(Context({'my_flag': True}))
        self.assertIn(
                '<img src="/static/icons/accept.png" alt="Yes" title="Yes" />',
                rendered)

    def test_renders_false(self):
        rendered = self.TEMPLATE.render(Context({'my_flag': False}))
        self.assertIn(
                '<img src="/static/icons/delete.png" alt="No" title="No" />',
                rendered)


class CommentDialogsTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% comment_dialogs %}')

    def test_renders_without_blowing_up(self):
        rendered = self.TEMPLATE.render(Context({}))


class MaxUsersTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% max_users %}')

    @patch('core.templatetags.core_tags.get_stats')
    def test_renders_empty_div_when_no_stats(self, mock_get_stats):
        mock_get_stats.return_value = None
        rendered = self.TEMPLATE.render(Context({}))
        rendered_no_ws = re.sub(r'\s', '', rendered)
        self.assertIn('<divid="max-users"></div>', rendered_no_ws)

    @patch('core.templatetags.core_tags.get_stats')
    def test_renders_with_status(self, mock_get_stats):
        mock_get_stats.return_value = Mock(max_users=42,
                                           max_users_date=datetime(2025, 6, 28))
        rendered = self.TEMPLATE.render(Context({}))
        self.assertIn(
                'The most registered users ever online was '
                '<strong>42</strong> on midnight Saturday, June 28, 2025.',
                rendered)


class WhosOnlineTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% whos_online %}')

    @patch('core.templatetags.core_tags.get_users_online')
    @patch('core.templatetags.core_tags.get_visitors_online')
    def test_renders_ok(self, mock_visitors, mock_users):
        mock_users.return_value = ['pj', 'eddie']
        mock_visitors.return_value = ['127.0.0.1']
        rendered = self.TEMPLATE.render(Context({}))
        self.assertIn(
            'There are 3 users online: 2 registered users and 1 guest.',
            rendered)
        self.assertIn(
            '<a href="/profile/view/eddie/" title="View profile for eddie">'
            'eddie</a>',
            rendered)
        self.assertIn(
            '<a href="/profile/view/pj/" title="View profile for pj">pj</a>',
            rendered)


class SocialSharingTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% social_sharing "Title" "Url" %}')

    @patch('core.templatetags.core_tags.Site.objects.get_current')
    def test_renders_ok(self, current_mock):
        site_mock = Mock()
        site_mock.configure_mock(name='Site', domain='site.com')
        current_mock.return_value = site_mock
        self.TEMPLATE.render(Context({}))

    @patch('core.templatetags.core_tags.Site.objects.get_current')
    def test_renders_ok_v3(self, current_mock):
        site_mock = Mock()
        site_mock.configure_mock(name='Site', domain='site.com')
        current_mock.return_value = site_mock
        self.TEMPLATE.render(Context({'V3_DESIGN': True}))


class OpenGraphMetaTagsTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% open_graph_meta_tags %}')

    @patch('core.templatetags.core_tags.Site.objects.get_current')
    def test_renders_site_tags(self, current_mock):
        site_mock = Mock()
        site_mock.configure_mock(name='Site', domain='site.com')
        current_mock.return_value = site_mock
        rendered = self.TEMPLATE.render(Context({}))

        expected = """
<meta property="og:title" content="Site" />

<meta property="og:type" content="website" />

<meta property="og:url" content="http://site.com" />

<meta property="og:description" content="The premier community website for friends and fans of instrumental surf music. We have forums, podcasts, surf music news, an event calendar, and much more! The surf is always up at SurfGuitar101.com!" />

<meta property="og:site_name" content="Site" />

<meta property="fb:admins" content="100001558124013" />

<meta property="og:image" content="http://surfguitar101.com/media/podcast/podcast_logo.jpg" />

"""
        self.assertEqual(rendered, expected)

    @patch('core.templatetags.core_tags.Site.objects.get_current')
    def test_renders_item(self, current_mock):
        site_mock = Mock()
        site_mock.configure_mock(name='Site', domain='site.com')
        current_mock.return_value = site_mock
        item = Mock()
        item.ogp_tags.return_value = {
            'og:title': 'My Item',
            'og:type': 'Article',
            'og:url': 'http://example.com/item.html',
            'og:description': 'Blah',
        }
        template = Template('{% load core_tags %}{% open_graph_meta_tags item %}')
        rendered = template.render(Context({'item': item}))

        # Python 3.7 dicts preserve insertion order, so the tags now render in the
        # order open_graph_meta_tags builds them (title, type, url, description,
        # site_name, fb:admins, image) rather than Python 2's hash order.
        expected = """
<meta property="og:title" content="My Item" />

<meta property="og:type" content="Article" />

<meta property="og:url" content="http://example.com/item.html" />

<meta property="og:description" content="Blah" />

<meta property="og:site_name" content="Site" />

<meta property="fb:admins" content="100001558124013" />

<meta property="og:image" content="http://surfguitar101.com/media/podcast/podcast_logo.jpg" />

"""
        self.assertEqual(rendered, expected)


class ElapsedFilterTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{{ some_date|elapsed }}')

    def test_renders_very_recent(self):
        some_date = datetime.now()
        rendered = self.TEMPLATE.render(Context({'some_date': some_date}))
        self.assertEqual(rendered, 'seconds ago')

    def test_renders_minutes_ago(self):
        some_date = datetime.now() - timedelta(minutes=5)
        rendered = self.TEMPLATE.render(Context({'some_date': some_date}))
        self.assertEqual(rendered, '5 minutes ago')

    def test_renders_hours_ago(self):
        some_date = datetime.now() - timedelta(hours=5)
        rendered = self.TEMPLATE.render(Context({'some_date': some_date}))
        self.assertEqual(rendered, '5 hours ago')

    def test_renders_days_ago(self):
        some_date = datetime.now() - timedelta(days=5)
        rendered = self.TEMPLATE.render(Context({'some_date': some_date}))
        self.assertEqual(rendered, '5 days ago')


class BirthdayBlockTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% birthday_block %}')

    def setUp(self):
        now = datetime.now()
        u1 = User.objects.create_user('paul', '', 'pw')
        u1.save()
        u1.profile.birthday = date(1946, now.month, 4)
        u1.profile.save()
        u2 = User.objects.create_user('eddie', '', 'pw')
        u2.save()
        u2.profile.birthday = date(
                1946, 1 if now.month == 12 else now.month + 1 , 17)
        u2.profile.save()

    def test_render(self):
        rendered = self.TEMPLATE.render(Context({}))
        self.assertIn('/profile/view/paul', rendered)
        self.assertNotIn('/profile/view/eddie', rendered)

    def test_render_v3(self):
        rendered = self.TEMPLATE.render(Context({'V3_DESIGN': True}))
        self.assertIn('/profile/view/paul', rendered)
        self.assertNotIn('/profile/view/eddie', rendered)


class EncodeParamsTestCase(TestCase):
    TEMPLATE = Template(
            '{% load core_tags %}{% encode_params qdict "a" "b" "c" %}')

    def test_render(self):
        params = 'a=1&a=2&b=foo&c=bar'
        qdict = QueryDict(params)
        rendered = self.TEMPLATE.render(Context({'qdict': qdict}))
        self.assertEqual(params, rendered)


class SlideshowImagesTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% slideshow_images %}')

    @patch('core.templatetags.core_tags.glob.glob')
    def test_render(self, mock_glob):
        mock_glob.return_value = ['a.jpg', 'b.jpg', 'c.jpg']
        rendered = self.TEMPLATE.render(Context({}))
        expected = """
   <img src="/media/slideshow/a.jpg" alt="Slideshow Image" />

   <img src="/media/slideshow/b.jpg" alt="Slideshow Image" />

   <img src="/media/slideshow/c.jpg" alt="Slideshow Image" />

"""
        self.assertEqual(rendered, expected)
        self.assertEqual(mock_glob.mock_calls, [
            call(os.path.join(settings.MEDIA_ROOT, 'slideshow', '*')),
        ])

    @patch('core.templatetags.core_tags.glob.glob')
    def test_render_more_than_5(self, mock_glob):
        mock_glob.return_value = ['{}.jpg'.format(x) for x in 'abcdef']
        rendered = self.TEMPLATE.render(Context({}))
        self.assertEqual(rendered.count('<img '), 5)


class PostBoxTestCase(TestCase):
    TEMPLATE = Template('{% load core_tags %}{% post_box form %}')

    def test_render(self):
        form = AddNewsForm()
        rendered = self.TEMPLATE.render(Context({'form': form}))
        self.assertIn('div class="v3-editor"', rendered)
