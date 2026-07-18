"""
Tests for the forums management commands that run unattended.

``forum_cleanup`` is fired on a schedule by ``core.tasks.cleanup`` (celery beat),
so a regression here is silent -- nothing exercises it interactively. It deletes
forum/topic last-visit bookkeeping records older than twice the unread THRESHOLD.
"""
import datetime

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

import forums.unread
from forums.models import (Category, Forum, ForumLastVisit, Topic,
                           TopicLastVisit)


NOW = datetime.datetime.now()


class ForumCleanupCommandTests(TestCase):

    def setUp(self):
        cat = Category.objects.create(name='Cat', slug='cat')
        self.forum = Forum.objects.create(category=cat, name='Forum', slug='forum')
        # last-visit records are unique per (user, forum) / (user, topic), so the
        # old and recent records below live on separate users.
        self.old_user = User.objects.create_user('old', '', 'pw')
        self.new_user = User.objects.create_user('new', '', 'pw')
        self.topic = Topic.objects.create(forum=self.forum, name='t',
                                          user=self.old_user)

        # The command's cutoff is now - THRESHOLD * 2.
        self.old = NOW - forums.unread.THRESHOLD * 2 - datetime.timedelta(days=1)
        self.recent = NOW - datetime.timedelta(days=1)

    def test_deletes_stale_records_and_keeps_recent_ones(self):
        ForumLastVisit.objects.create(user=self.old_user, forum=self.forum,
                                      begin_date=self.old, end_date=self.old)
        ForumLastVisit.objects.create(user=self.new_user, forum=self.forum,
                                      begin_date=self.recent, end_date=self.recent)
        TopicLastVisit.objects.create(user=self.old_user, topic=self.topic,
                                      last_visit=self.old)
        TopicLastVisit.objects.create(user=self.new_user, topic=self.topic,
                                      last_visit=self.recent)

        call_command('forum_cleanup')

        surviving_flv = ForumLastVisit.objects.all()
        self.assertEqual([flv.user_id for flv in surviving_flv],
                         [self.new_user.id])
        surviving_tlv = TopicLastVisit.objects.all()
        self.assertEqual([tlv.user_id for tlv in surviving_tlv],
                         [self.new_user.id])
