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
            self.topic = Topic.objects.get(pk=id)
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
    """Form for creating a new topic and 1st post to that topic."""
    name = forms.CharField(label='Subject', max_length=255,
            widget=forms.TextInput(attrs={'size': 64}))
    body = forms.CharField(label='', widget=forms.Textarea)

    class Media:
        css = {
            'all': settings.GPP_THIRD_PARTY_CSS['markitup'],
        }
        js = settings.GPP_THIRD_PARTY_JS['markitup'] + \
            ('js/forums.js', )

    def save(self, forum, user, ip=None):
        """
        Creates the new Topic and first Post from the form data and supplied
        arguments.
        """
        topic = Topic(forum=forum,
                name=self.cleaned_data['name'],
                user=user)
        topic.save()

        post = Post(topic=topic,
                user=user,
                body=self.cleaned_data['body'],
                user_ip=ip)
        post.save()

        bump_post_count(user)
        return topic
