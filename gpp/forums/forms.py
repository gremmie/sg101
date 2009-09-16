"""
Forms for the forums application.
"""
from django import forms
from django.conf import settings

from forums.models import Topic
from forums.models import Post


def bump_post_count(user):
    """
    Increments the forum_post_count for the given user.
    """
    profile = user.get_profile()
    profile.forum_post_count += 1
    profile.save()


class PostForm(forms.Form):
    """Form for creating a new post."""
    body = forms.CharField(label='', widget=forms.Textarea)
    topic_id = forms.IntegerField(widget=forms.HiddenInput)
    topic = None

    class Media:
        css = {
            'all': settings.GPP_THIRD_PARTY_CSS['markitup'],
        }
        js = settings.GPP_THIRD_PARTY_JS['markitup'] + \
            ('js/forums.js', )

    def clean_topic_id(self):
        id = self.cleaned_data['topic_id']
        try:
            self.topic = Topic.objects.select_related().get(pk=id)
        except Topic.DoesNotExist:
            raise forms.ValidationError('invalid topic')
        return id 

    def save(self, user, ip=None):
        """
        Creates a new post from the form data and supplied arguments.
        """
        post = Post(topic=self.topic, user=user, body=self.cleaned_data['body'],
                user_ip=ip)
        post.save()
        bump_post_count(user)
        return post


class NewTopicForm(forms.Form):
    """
    Form for creating a new topic and 1st post to that topic.
    Superusers and moderators can also create the topic as a sticky or initially
    locked.
    """
    name = forms.CharField(label='Subject', max_length=255,
            widget=forms.TextInput(attrs={'size': 64}))
    body = forms.CharField(label='', widget=forms.Textarea)
    user = None
    forum = None
    has_mod_fields = False

    class Media:
        css = {
            'all': settings.GPP_THIRD_PARTY_CSS['markitup'],
        }
        js = settings.GPP_THIRD_PARTY_JS['markitup'] + \
            ('js/forums.js', )

    def __init__(self, user, forum, *args, **kwargs):
        super(NewTopicForm, self).__init__(*args, **kwargs)
        self.user = user
        self.forum = forum

        if user.is_superuser or user in forum.moderators.all():
            self.fields['sticky'] = forms.BooleanField(required=False)
            self.fields['locked'] = forms.BooleanField(required=False)
            self.has_mod_fields = True

    def save(self, ip=None):
        """
        Creates the new Topic and first Post from the form data and supplied
        arguments.
        """
        topic = Topic(forum=self.forum,
                name=self.cleaned_data['name'],
                user=self.user,
                sticky=self.has_mod_fields and self.cleaned_data['sticky'],
                locked=self.has_mod_fields and self.cleaned_data['locked'])
        topic.save()

        post = Post(topic=topic,
                user=self.user,
                body=self.cleaned_data['body'],
                user_ip=ip)
        post.save()

        bump_post_count(self.user)
        return topic
