"""
Characterization tests for forums permission gating.

These lock in the current behavior of who may post, edit, delete, and moderate
in the forums, so future changes surface any regression loudly. They drive the
real views through the test client and thereby exercise ``forums.permissions``
(can_access / can_post / can_moderate).

The fixture ``forums.json`` ships 14 public forums (no per-category access groups
and no moderator groups) plus an empty ``Forum Moderators`` group, so every test
that needs a restricted forum or a real moderator wires that up explicitly.
"""
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import TestCase

from forums.models import Forum, Post, Topic


LOGIN_PATH = reverse('accounts-login')


def make_topic(forum, user, locked=False, name='A test topic'):
    """Create a topic with a single first post via the ORM. Returns (topic, post)."""
    topic = Topic.objects.create(forum=forum, name=name, user=user, locked=locked)
    post = Post.objects.create(topic=topic, user=user, body='the first post')
    topic.last_post = post
    topic.save()
    return topic, post


def add_reply(topic, user, body='a reply'):
    """Append a (non-first) reply post to an existing topic."""
    post = Post.objects.create(topic=topic, user=user, body=body)
    topic.last_post = post
    topic.save()
    return post


class ForumPermissionsBase(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        # forums.permissions caches group membership in the default (LocMem)
        # cache, which persists across tests in a process; clear it so each test
        # starts from fresh group data.
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')

    def tearDown(self):
        cache.clear()


class AnonymousUserTests(ForumPermissionsBase):
    """An anonymous visitor may read but never write."""

    def test_login_required_views_redirect_to_login(self):
        author = User.objects.create_user('author', '', 'pw')
        topic, post = make_topic(self.forum, author)

        urls = [
            reverse('forums-new_topic', kwargs={'slug': self.forum.slug}),
            reverse('forums-new_post', kwargs={'topic_id': topic.id}),
            reverse('forums-edit_post', kwargs={'id': post.id}),
            reverse('forums-mod_topic_lock', args=[topic.id]),
            reverse('forums-mod_topic_stick', args=[topic.id]),
            reverse('forums-mod_topic_delete', args=[topic.id]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302,
                             msg='%s should redirect anonymous users' % url)
            self.assertTrue(response['Location'].startswith(LOGIN_PATH),
                            msg='%s should redirect to the login page' % url)

    def test_quick_reply_forbidden_for_anonymous(self):
        author = User.objects.create_user('author', '', 'pw')
        topic, post = make_topic(self.forum, author)

        response = self.client.post(reverse('forums-quick_reply'),
                                    {'body': 'hello', 'topic_id': topic.id})
        self.assertEqual(response.status_code, 403)

    def test_delete_post_forbidden_for_anonymous(self):
        author = User.objects.create_user('author', '', 'pw')
        topic, post = make_topic(self.forum, author)

        response = self.client.post(reverse('forums-delete_post'), {'id': post.id})
        self.assertEqual(response.status_code, 403)


class RegularMemberTests(ForumPermissionsBase):
    """An authenticated, non-privileged member: can post, can edit own posts,
    cannot edit/delete others' posts, cannot moderate, cannot post to a locked
    topic."""

    def setUp(self):
        super(RegularMemberTests, self).setUp()
        self.author = User.objects.create_user('author', '', 'pw')
        self.member = User.objects.create_user('member', '', 'pw')
        self.assertTrue(self.client.login(username='member', password='pw'))

    def test_member_can_edit_own_post(self):
        topic, first = make_topic(self.forum, self.member)
        reply = add_reply(topic, self.member, body='original body')

        response = self.client.post(reverse('forums-edit_post', kwargs={'id': reply.id}),
                                    {'body': 'edited body'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.get(pk=reply.id).body, 'edited body')

    def test_member_cannot_edit_others_post(self):
        topic, first = make_topic(self.forum, self.author)
        reply = add_reply(topic, self.author, body="author's words")

        get_resp = self.client.get(reverse('forums-edit_post', kwargs={'id': reply.id}))
        self.assertEqual(get_resp.status_code, 403)

        post_resp = self.client.post(reverse('forums-edit_post', kwargs={'id': reply.id}),
                                     {'body': 'tampered'})
        self.assertEqual(post_resp.status_code, 403)
        self.assertEqual(Post.objects.get(pk=reply.id).body, "author's words")

    def test_member_cannot_delete_post(self):
        topic, first = make_topic(self.forum, self.author)
        reply = add_reply(topic, self.author)

        response = self.client.post(reverse('forums-delete_post'), {'id': reply.id})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=reply.id).exists())

    def test_member_cannot_reply_to_locked_topic_via_quick_reply(self):
        topic, first = make_topic(self.forum, self.author, locked=True)

        response = self.client.post(reverse('forums-quick_reply'),
                                    {'body': 'sneak in', 'topic_id': topic.id})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(topic.posts.count(), 1)

    def test_member_new_post_to_locked_topic_is_refused(self):
        topic, first = make_topic(self.forum, self.author, locked=True)
        url = reverse('forums-new_post', kwargs={'topic_id': topic.id})

        # The page still renders (200) but signals can_post=False...
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        self.assertFalse(get_resp.context['can_post'])

        # ...and a POST creates no reply.
        self.client.post(url, {'body': 'sneak in'})
        self.assertEqual(topic.posts.count(), 1)

    def test_member_cannot_moderate(self):
        topic, first = make_topic(self.forum, self.author)
        for url in [reverse('forums-mod_topic_lock', args=[topic.id]),
                    reverse('forums-mod_topic_stick', args=[topic.id]),
                    reverse('forums-mod_topic_delete', args=[topic.id])]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403,
                             msg='%s should be forbidden to a regular member' % url)
        self.assertTrue(Topic.objects.filter(pk=topic.id).exists())


class SuperuserTests(ForumPermissionsBase):
    """A superuser bypasses every forum permission check."""

    def setUp(self):
        super(SuperuserTests, self).setUp()
        self.author = User.objects.create_user('author', '', 'pw')
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))

    def test_superuser_can_edit_any_post(self):
        topic, first = make_topic(self.forum, self.author)
        reply = add_reply(topic, self.author, body='original')

        self.client.post(reverse('forums-edit_post', kwargs={'id': reply.id}),
                         {'body': 'moderated'}, follow=True)
        self.assertEqual(Post.objects.get(pk=reply.id).body, 'moderated')

    def test_superuser_can_delete_post(self):
        topic, first = make_topic(self.forum, self.author)
        reply = add_reply(topic, self.author)

        response = self.client.post(reverse('forums-delete_post'), {'id': reply.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(pk=reply.id).exists())

    def test_superuser_can_lock_topic(self):
        topic, first = make_topic(self.forum, self.author)
        self.assertFalse(topic.locked)

        response = self.client.get(reverse('forums-mod_topic_lock', args=[topic.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Topic.objects.get(pk=topic.id).locked)


class GroupModeratorTests(ForumPermissionsBase):
    """A non-superuser gains moderator rights by belonging to a group that is
    listed among a forum's moderators (this is the can_moderate group logic)."""

    def setUp(self):
        super(GroupModeratorTests, self).setUp()
        self.author = User.objects.create_user('author', '', 'pw')
        self.mod = User.objects.create_user('mod', '', 'pw')
        mod_group = Group.objects.get(name='Forum Moderators')
        self.mod.groups.add(mod_group)
        self.forum.moderators.add(mod_group)
        self.assertTrue(self.client.login(username='mod', password='pw'))

    def test_group_moderator_can_lock_topic(self):
        topic, first = make_topic(self.forum, self.author)

        response = self.client.get(reverse('forums-mod_topic_lock', args=[topic.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Topic.objects.get(pk=topic.id).locked)

    def test_group_moderator_can_delete_others_post(self):
        topic, first = make_topic(self.forum, self.author)
        reply = add_reply(topic, self.author)

        response = self.client.post(reverse('forums-delete_post'), {'id': reply.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(pk=reply.id).exists())


class PrivateCategoryTests(ForumPermissionsBase):
    """A category with assigned groups is private: only members of those groups
    (or superusers) can access its forums (the can_access group logic)."""

    def setUp(self):
        super(PrivateCategoryTests, self).setUp()
        self.secret_group = Group.objects.create(name='Inner Circle')
        # Lock down the forum's category to the secret group.
        self.forum.category.groups.add(self.secret_group)

    def test_non_member_cannot_start_topic_in_private_forum(self):
        User.objects.create_user('outsider', '', 'pw')
        self.assertTrue(self.client.login(username='outsider', password='pw'))

        url = reverse('forums-new_topic', kwargs={'slug': self.forum.slug})
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_group_member_can_reach_private_forum(self):
        insider = User.objects.create_user('insider', '', 'pw')
        insider.groups.add(self.secret_group)
        self.assertTrue(self.client.login(username='insider', password='pw'))

        url = reverse('forums-new_topic', kwargs={'slug': self.forum.slug})
        self.assertEqual(self.client.get(url).status_code, 200)
