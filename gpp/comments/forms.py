"""
Forms for the comments application.
"""
import datetime
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from comments.models import Comment

COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)

class CommentForm(forms.Form):
    comment = forms.CharField(label='',
            min_length=1, 
            max_length=COMMENT_MAX_LENGTH,
            widget=forms.Textarea)
    content_type = forms.CharField(widget=forms.HiddenInput)
    object_pk = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, target_object, data=None, initial=None):
        self.target_object = target_object
        if initial is None:
            initial = {}
        initial.update({
            'content_type': str(self.target_object._meta),
            'object_pk': str(self.target_object.pk),
            })
        super(CommentForm, self).__init__(data=data, initial=initial)

    def get_comment_object(self, user, ip_address):
        """
        Return a new (unsaved) comment object based on the information in this
        form. Assumes that the form is already validated and will throw a
        ValueError if not.
        """
        if not self.is_valid():
            raise ValueError("get_comment_object may only be called on valid forms")

        new = Comment(
            content_type = ContentType.objects.get_for_model(self.target_object),
            object_id = self.target_object.pk,
            user = user,
            comment = self.cleaned_data["comment"],
            ip_address = ip_address,
            is_public = True,
            is_removed = False,
        )

        # Check that this comment isn't duplicate. (Sometimes people post comments
        # twice by mistake.) If it is, fail silently by returning the old comment.
        today = datetime.date.today()
        possible_duplicates = Comment.objects.filter(
            content_type = new.content_type,
            object_id = new.object_id,
            user = new.user,
            creation_date__year = today.year,
            creation_date__month = today.month,
            creation_date__day = today.day,
        )
        for old in possible_duplicates:
            if old.comment == new.comment:
                return old

        return new

    class Media:
        css = {
            'all': settings.GPP_THIRD_PARTY_CSS['markitup'],
        }
        js = settings.GPP_THIRD_PARTY_JS['markitup'] + \
            ('js/comments.js', )
