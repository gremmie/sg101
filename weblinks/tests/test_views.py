"""
Characterization tests for the weblinks views.

The weblinks directory is public to browse (unlike downloads). These cover the
browse/detail journeys, the visit (hit-count redirect), random link, the
report-broken-link AJAX endpoint, and the login-gated add form.
"""
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from weblinks.models import Category, FlaggedLink, Link, PendingLink


def make_link(user, category, title='A Link', url='http://example.com/', public=True):
    return Link.objects.create(category=category, title=title, url=url,
                               description='desc', user=user, is_public=public)


class WebLinkBrowseTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('member', '', 'pw')
        self.category = Category.objects.create(title='Bands', slug='bands')
        self.link = make_link(self.user, self.category, title='The Ventures')

    def test_index_renders(self):
        response = self.client.get(reverse('weblinks-main'))
        self.assertEqual(response.status_code, 200)

    def test_new_and_popular_render(self):
        for name in ('weblinks-new_links', 'weblinks-popular_links'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, msg=name)

    def test_view_links_lists_category(self):
        response = self.client.get(reverse('weblinks-view_links',
            kwargs={'slug': self.category.slug, 'sort': 'title'}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('The Ventures', response.content)

    def test_view_links_accepts_each_sort(self):
        for sort in ('title', 'date', 'hits'):
            response = self.client.get(reverse('weblinks-view_links',
                kwargs={'slug': self.category.slug, 'sort': sort}))
            self.assertEqual(response.status_code, 200, msg='sort=%s' % sort)

    def test_view_links_unknown_category_is_404(self):
        response = self.client.get(reverse('weblinks-view_links',
            kwargs={'slug': 'nope', 'sort': 'title'}))
        self.assertEqual(response.status_code, 404)

    def test_detail_renders_for_public(self):
        response = self.client.get(reverse('weblinks-link_detail', args=[self.link.id]))
        self.assertEqual(response.status_code, 200)

    def test_detail_404_for_non_public(self):
        hidden = make_link(self.user, self.category, title='Hidden',
                           url='http://example.com/hidden/', public=False)
        response = self.client.get(reverse('weblinks-link_detail', args=[hidden.id]))
        self.assertEqual(response.status_code, 404)


class WebLinkVisitTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('member', '', 'pw')
        self.category = Category.objects.create(title='Bands', slug='bands')
        self.link = make_link(self.user, self.category, url='http://ventures.example/')

    def test_visit_increments_hits_and_redirects(self):
        response = self.client.post(reverse('weblinks-visit', args=[self.link.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://ventures.example/')
        self.assertEqual(Link.objects.get(pk=self.link.id).hits, 1)

    def test_visit_requires_post(self):
        response = self.client.get(reverse('weblinks-visit', args=[self.link.id]))
        self.assertEqual(response.status_code, 405)

    def test_random_page_renders(self):
        response = self.client.get(reverse('weblinks-random_link'))
        self.assertEqual(response.status_code, 200)

    def test_random_post_redirects_to_a_link(self):
        response = self.client.post(reverse('weblinks-random_link'))
        self.assertEqual(response.status_code, 302)

    def test_random_post_with_no_links_is_404(self):
        Link.objects.all().delete()
        response = self.client.post(reverse('weblinks-random_link'))
        self.assertEqual(response.status_code, 404)


class WebLinkReportTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('member', '', 'pw')
        self.category = Category.objects.create(title='Bands', slug='bands')
        self.link = make_link(self.user, self.category)
        self.url = reverse('weblinks-report_link', args=[self.link.id])

    def test_report_requires_login(self):
        # Anonymous gets a friendly 200 message rather than a redirect/403.
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('login', response.content)
        self.assertFalse(FlaggedLink.objects.exists())

    def test_report_creates_flag(self):
        self.client.login(username='member', password='pw')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FlaggedLink.objects.filter(link=self.link, user=self.user).exists())

    def test_report_unknown_link_is_bad_request(self):
        self.client.login(username='member', password='pw')
        response = self.client.post(reverse('weblinks-report_link', args=[999999]))
        self.assertEqual(response.status_code, 400)


class WebLinkAddTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('member', '', 'pw')
        self.category = Category.objects.create(title='Bands', slug='bands')

    def test_add_requires_login(self):
        response = self.client.get(reverse('weblinks-add_link'))
        self.assertEqual(response.status_code, 302)

    def test_add_form_renders(self):
        self.client.login(username='member', password='pw')
        response = self.client.get(reverse('weblinks-add_link'))
        self.assertEqual(response.status_code, 200)

    def test_add_creates_pending_link(self):
        self.client.login(username='member', password='pw')
        response = self.client.post(reverse('weblinks-add_link'), {
            'category': self.category.id,
            'title': 'New Surf Site',
            'url': 'http://newsurf.example/',
            'description': 'a great site',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PendingLink.objects.filter(title='New Surf Site',
                                                   user=self.user).exists())

    def test_add_thanks_renders(self):
        self.client.login(username='member', password='pw')
        response = self.client.get(reverse('weblinks-add_thanks'))
        self.assertEqual(response.status_code, 200)
