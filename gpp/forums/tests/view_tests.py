"""
Tests for the views in the forums application.

"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from forums.models import Forum, Topic, Post


class ForumPostTestCase(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.assertTrue(self.client.login(username=self.username,
            password=self.pw))

    def tearDown(self):
        self.client.logout()

    def testBasicForumsTest(self):

        forum_slug = 'shallow-end'
        topic_name = 'A test topic'
        topic_body = 'testing 1, 2, 3...'

        response = self.client.post(
                reverse('forums-new_topic', kwargs={'slug': forum_slug}),
                {'name': topic_name, 'body': topic_body},
                follow=True)

        self.assertEqual(len(response.redirect_chain), 1)

        if response.redirect_chain:
            self.assertEqual(response.redirect_chain[0][0],
                'http://testserver' + reverse('forums-new_topic_thanks',
                    kwargs={'tid': '1'}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)

        forum = Forum.objects.get(slug=forum_slug)
        try:
            topic = Topic.objects.get(pk=1)
        except Topic.DoesNotExist:
            self.fail("topic doesn't exist")

        self.assertEqual(topic.forum.pk, forum.pk)
        self.assertEqual(topic.user.pk, self.user.pk)
        self.assertEqual(topic.name, topic_name)
        self.assertEqual(topic.post_count, 1)

        post = topic.last_post
        self.failIf(post is None)

        if post:
            self.assertEqual(post.body, topic_body)
            self.assertEqual(post.user.pk, self.user.pk)

        # post to the thread
        response = self.client.get(
                reverse('forums-topic_index', kwargs={'id': '1'}))
        self.assertEqual(response.status_code, 200)

        post2_body = 'test quick post'
        response = self.client.post(
                reverse('forums-quick_reply'),
                {'body': post2_body, 'topic_id': 1})
        self.assertEqual(response.status_code, 200)
        try:
            topic = Topic.objects.get(pk=1)
        except Topic.DoesNotExist:
            self.fail("topic doesn't exist")

        post = topic.last_post
        self.failIf(post is None)
        if post:
            self.assertEqual(post.body, post2_body)
            self.assertEqual(post.user.pk, self.user.pk)
        self.assertEqual(topic.post_count, 2)

        # quote last post
        response = self.client.get(
                reverse('forums-new_post', kwargs={'topic_id': 1}),
                {'quote_id': 2})
        self.assertEqual(response.status_code, 200)

        post3_body = 'new post 3 content'
        response = self.client.post(
                reverse('forums-new_post', kwargs={'topic_id': 1}),
                {'body': post3_body, 'post_id': 2},
                follow=True)
        self.assertEqual(response.status_code, 200)
        try:
            topic = Topic.objects.get(pk=1)
        except Topic.DoesNotExist:
            self.fail("topic doesn't exist")

        post = topic.last_post
        self.failIf(post is None)
        if post:
            self.assertEqual(post.body, post3_body)
            self.assertEqual(post.user.pk, self.user.pk)
        self.assertEqual(topic.post_count, 3)

        # edit last post
        response = self.client.get(
                reverse('forums-edit_post', kwargs={'id': 3}))
        self.assertEqual(response.status_code, 200)

        post3_body = 'edited post 3 content'
        response = self.client.post(
                reverse('forums-edit_post', kwargs={'id': 3}),
                {'body': post3_body},
                follow=True)
        self.assertEqual(response.status_code, 200)
        try:
            topic = Topic.objects.get(pk=1)
        except Topic.DoesNotExist:
            self.fail("topic doesn't exist")

        post = topic.last_post
        self.failIf(post is None)
        if post:
            self.assertEqual(post.body, post3_body)
            self.assertEqual(post.user.pk, self.user.pk)
        self.assertEqual(topic.post_count, 3)

        profile = self.user.get_profile()
        self.assertEqual(profile.forum_post_count, 3)
