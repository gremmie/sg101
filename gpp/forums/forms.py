"""
Forms for the forums application.
"""
from django import forms

from forums.models import Topic
from forums.models import Post


class PostForm(forms.Form):
    """Form for creating a new post."""
    body = forms.CharField(label='', widget=forms.Textarea)

    def save(self, topic, user, ip=None):
        """
        Creates a new post from the form data and supplied arguments.
        """
        post = Post(topic=topic, user=user, body=self.cleaned_data['body'],
                user_ip=user_ip)
        post.save()


class NewTopicForm(forms.Form):
    """Form for creating a new topic and 1st post to that topic."""
    name = forms.CharField(label='Subject', max_length=255)
    body = forms.CharField(label='', widget=forms.Textarea)

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

        return topic
