"""
Tests for the views in the polls application.

"""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from polls.models import Poll, Choice


class PollHomeTest(TestCase):

    def setUp(self):
        now = timezone.now()
        Poll.objects.all().delete()

        past = now - datetime.timedelta(7)
        future = now + datetime.timedelta(7)

        Poll.objects.create(start_date=past,
                end_date=past,
                is_enabled=True,
                question='Old Poll')

        active = Poll.objects.create(start_date=past,
                end_date=future,
                is_enabled=True,
                question='Active Poll')

        Poll.objects.create(start_date=future,
                end_date=future,
                is_enabled=True,
                question='Future Poll')

        Poll.objects.create(start_date=past,
                end_date=future,
                is_enabled=False,
                question='Disabled Poll')

        self.choice1 = Choice.objects.create(poll=active, choice="Yes")
        self.choice2 = Choice.objects.create(poll=active, choice="Yes")

        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.assertTrue(self.client.login(username=self.username,
            password=self.pw))

    def tearDown(self):
        self.client.logout()

    def testHome(self):
        response = self.client.get(reverse('polls-main'))

        old = response.context['old_polls']
        self.assertEqual(len(old), 1)
        if old:
            self.assertEqual(old[0].question, 'Old Poll')

        current = response.context['current_polls']
        self.assertEqual(len(current), 1)
        if current:
            self.assertEqual(current[0].question, 'Active Poll')

        self.assertNotContains(response, 'Future Poll')
        self.assertNotContains(response, 'Disabled Poll')

    def testFuture(self):
        poll = Poll.objects.get(question='Future Poll')
        response = self.client.get(reverse('polls-detail', kwargs={'poll_id':
            poll.id}))
        self.assertEqual(response.status_code, 404)

    def testDisabled(self):
        poll = Poll.objects.get(question='Disabled Poll')
        response = self.client.get(reverse('polls-detail', kwargs={'poll_id':
            poll.id}))
        self.assertEqual(response.status_code, 404)

    def testOld(self):
        poll = Poll.objects.get(question='Old Poll')
        response = self.client.get(reverse('polls-detail', kwargs={'poll_id':
            poll.id}))
        self.assertEqual(response.status_code, 200)

    def testActive(self):
        poll = Poll.objects.get(question='Active Poll')
        response = self.client.get(reverse('polls-detail', kwargs={'poll_id':
            poll.id}))
        self.assertEqual(response.status_code, 200)

    def testVoteOld(self):
        poll = Poll.objects.get(question='Old Poll')
        response = self.client.get(reverse('polls-vote', kwargs={'poll_id':
            poll.id}), follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        if response.redirect_chain:
            self.assertEqual(
                    response.redirect_chain[0][0],
                    reverse('polls-detail', kwargs={'poll_id': poll.id}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)

    def testVoteActive(self):
        poll = Poll.objects.get(question='Active Poll')
        response = self.client.get(reverse('polls-vote', kwargs={'poll_id':
            poll.id}), follow=True)

        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)

    def testVoteFuture(self):
        poll = Poll.objects.get(question='Future Poll')
        response = self.client.get(reverse('polls-vote', kwargs={'poll_id':
            poll.id}), follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        if response.redirect_chain:
            self.assertEqual(
                    response.redirect_chain[0][0],
                    reverse('polls-detail', kwargs={'poll_id': poll.id}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 404)

    def testVoteDisabled(self):
        poll = Poll.objects.get(question='Disabled Poll')
        response = self.client.get(reverse('polls-vote', kwargs={'poll_id':
            poll.id}), follow=True)

        self.assertEqual(response.status_code, 404)

    def testVoteActivePost(self):
        self._voteTest()

    def testDeleteVote(self):
        poll = self._voteTest()

        response = self.client.post(
                reverse('polls-delete_vote'),
                {'poll_id': poll.id},
                follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        if response.redirect_chain:
            self.assertEqual(
                    response.redirect_chain[0][0],
                    reverse('polls-detail', kwargs={'poll_id': poll.id}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)

        choice = Choice.objects.get(pk=self.choice1.pk)
        self.assertEqual(choice.votes, 0)
        self.assertTrue(self.user not in choice.voters.all())

    def _voteTest(self):
        poll = Poll.objects.get(question='Active Poll')
        response = self.client.post(
                reverse('polls-vote', kwargs={'poll_id': poll.id}),
                {'choices': self.choice1.pk},
                follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        if response.redirect_chain:
            self.assertEqual(
                    response.redirect_chain[0][0],
                    reverse('polls-detail', kwargs={'poll_id': poll.id}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)

        choice = Choice.objects.get(pk=self.choice1.pk)
        self.assertEqual(choice.votes, 1)
        self.assertTrue(self.user in choice.voters.all())

        return poll
