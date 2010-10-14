"""
This module contains a class for handling attachments on forum posts.
"""
from oembed.models import Oembed
from forums.models import Attachment


class AttachmentProcessor(object):
    """
    This class is aggregated by various form classes to handle
    attachments on forum posts. New posts can receive attachments and edited
    posts can have their attachments replaced, augmented, or deleted.

    """
    def __init__(self, ids):
        """
        This class is constructed with a list of Oembed ids. We retrieve the
        actual Oembed objects associated with these keys for use in subsequent
        operations.
        
        """
        # ensure all ids are integers
        self.pks = []
        for pk in ids:
            try:
                pk = int(pk)
            except ValueError:
                continue
            self.pks.append(pk)

        self.embeds = []
        if self.pks:
            self.embeds = Oembed.objects.in_bulk(self.pks)

    def save_attachments(self, post):
        """
        Create and save attachments to the supplied post object.
        Any existing attachments on the post are removed first.

        """
        post.attachments.clear()

        for n, pk in enumerate(self.pks):
            attachment = Attachment(post=post, embed=self.embeds[pk], order=n)
            attachment.save()
