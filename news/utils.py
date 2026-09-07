"""
Common utility/helper code for the news app.

"""
from django.contrib.contenttypes.models import ContentType

from comments.models import Comment
from news.models import Story


def attach_extra_attrs(stories):
    """
    For each story in the input stories list, attach a comment_count attribute.
    The counts are pulled from the database in bulk. This saves database queries
    when lots of news stories are displayed at once.

    """
    stories_dict = dict((story.id, story) for story in stories)
    story_ids = stories_dict.keys()

    for story in stories_dict.values():
        if story.version == 0:
            story.comment_count = 0
        elif story.forums_topic:
            # for convenience/consistency with old models...
            story.comment_count = story.forums_comment_count()

    # Now get all the comment counts out in one fell swoop. This is only needed
    # for older news stories...

    story_ids = [pk for pk in story_ids if stories_dict[pk].version == 0]

    if story_ids:
        ct = ContentType.objects.get_for_model(Story)
        story_ids = Comment.objects.filter(content_type=ct,
                object_id__in=story_ids).values_list('object_id', flat=True)

        # compute comment_count
        for story_id in story_ids:
            stories_dict[story_id].comment_count += 1
