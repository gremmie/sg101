"""
Common utility/helper code for the news app.

"""
from django.contrib.contenttypes.models import ContentType

from comments.models import Comment
from tagging.models import TaggedItem
from news.models import Story


def attach_extra_attrs(stories):
    """
    For each story in the input stories list, attach 2 new attributes:
    tag_list and comment_count. The tags and comment count info is pulled from
    the database in bulk. This saves database queries when lots of news
    stories are displayed at once. For best results, use ".defer('tags')"
    when retrieve the stories from the database.

    """
    stories_dict = dict((story.id, story) for story in stories)
    story_ids = stories_dict.keys()

    # Get all the tags out in one query
    ct = ContentType.objects.get_for_model(Story)
    tagged_items = TaggedItem.objects.filter(content_type=ct,
            object_id__in=story_ids).select_related('tag')

    for story in stories_dict.values():
        story.tag_list = []
        story.comment_count = 0

    # attach tags
    for item in tagged_items:
        stories_dict[item.object_id].tag_list.append(item.tag.name)

    # Now get all the comment counts out in one fell swoop

    story_ids = Comment.objects.filter(content_type=ct,
            object_id__in=story_ids).values_list('object_id', flat=True)

    # compute comment_count
    for story_id in story_ids:
        stories_dict[story_id].comment_count += 1
