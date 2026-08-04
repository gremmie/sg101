"""
Signals for the forums application.

"""
import django.dispatch


# This signal is sent when a topic has had its textual content (title) changed.
# The provided arguments are: 
#   sender - the topic model instance 
#   created - True if the topic is new, False if updated

topic_content_update = django.dispatch.Signal()

# This signal is sent when a post has had its textual content (body) changed.
# The provided arguments are: 
#   sender - the post model instance 
#   created - True if the post is new, False if updated

post_content_update = django.dispatch.Signal()


def notify_new_topic(topic):
    """
    Sends the topic_content_update signal for a new topic instance.

    """
    topic_content_update.send_robust(topic, created=True)


def notify_updated_topic(topic):
    """
    Sends the topic_content_update signal for an updated topic instance.

    """
    topic_content_update.send_robust(topic, created=False)


def notify_new_post(post):
    """
    Sends the post_content_update signal for a new post instance.

    """
    post_content_update.send_robust(post, created=True)


def notify_updated_post(post):
    """
    Sends the post_content_update signal for an updated post instance.

    """
    post_content_update.send_robust(post, created=False)
