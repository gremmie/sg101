"""
Tests that routine site activity queues only the reindexing it needs.

The receivers reindex on every post_save of a searchable model, so a view that
saves one to bump a counter queues a task that rewrites a row with the text it
already had. These drive the real views and count what reaches the queue: a
test that saved the model directly would only restate what the receivers do.

"""
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from forums.models import Topic
from search.tasks import reindex_document
from search.tests.test_documents import DocumentTestCase


class SavePathTestCase(DocumentTestCase):

    def setUp(self):
        super().setUp()
        self.client.login(username='kahuna', password='pw')

    def queued_reindexes(self, callbacks):
        """The (model, pk) pairs the captured callbacks would reindex."""
        queued = []
        for callback in callbacks:
            if getattr(callback, 'func', None) == reindex_document.delay:
                content_type_id, object_id = callback.args
                model = ContentType.objects.get_for_id(
                        content_type_id).model_class()
                queued.append((model, object_id))
        return queued

    def test_viewing_a_topic_queues_no_reindex(self):
        with self.captureOnCommitCallbacks() as callbacks:
            response = self.client.get(self.topic.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.queued_reindexes(callbacks), [])

    def test_viewing_a_topic_still_counts_the_view(self):
        self.client.get(self.topic.get_absolute_url())
        self.client.get(self.topic.get_absolute_url())

        self.topic.refresh_from_db()
        self.assertEqual(self.topic.view_count, 2)

    def test_a_reply_queues_only_the_new_post(self):
        with self.captureOnCommitCallbacks() as callbacks:
            response = self.client.post(reverse('forums-quick_reply'), {
                    'topic_id': self.topic.pk,
                    'body': 'Try a blackface amp.'})

        self.assertEqual(response.status_code, 200)
        reply = self.topic.posts.latest('pk')
        self.assertEqual(self.queued_reindexes(callbacks),
                         [(type(reply), reply.pk)])

    def test_a_reply_still_updates_the_topic_and_post_count(self):
        self.client.post(reverse('forums-quick_reply'), {
                'topic_id': self.topic.pk,
                'body': 'Try a blackface amp.'})

        self.topic.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.topic.post_count, 2)
        self.assertEqual(self.topic.last_post,
                         self.topic.posts.latest('pk'))
        self.assertEqual(self.profile.forum_post_count, 1)

    def test_visiting_a_link_queues_no_reindex(self):
        with self.captureOnCommitCallbacks() as callbacks:
            response = self.client.post(
                    reverse('weblinks-visit', args=[self.link.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.queued_reindexes(callbacks), [])

    def test_visiting_a_link_still_counts_the_hit(self):
        self.client.post(reverse('weblinks-visit', args=[self.link.pk]))

        self.link.refresh_from_db()
        self.assertEqual(self.link.hits, 1)

    def test_requesting_a_download_queues_no_reindex(self):
        with self.captureOnCommitCallbacks() as callbacks:
            response = self.client.post(
                    reverse('downloads-request_download'),
                    {'id': self.download.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.queued_reindexes(callbacks), [])

    def test_requesting_a_download_still_counts_the_hit(self):
        self.client.post(reverse('downloads-request_download'),
                         {'id': self.download.pk})

        self.download.refresh_from_db()
        self.assertEqual(self.download.hits, 1)

    def test_logging_in_queues_no_reindex(self):
        self.client.logout()

        with self.captureOnCommitCallbacks() as callbacks:
            response = self.client.post(reverse('accounts-login'), {
                    'username': 'kahuna', 'password': 'pw'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.queued_reindexes(callbacks), [])
