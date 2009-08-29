"""
Forms for the forums application.
"""
from django import forms

from forums.models import Topic
from forums.models import Post


class TopicForm(forms.ModelForm):
    """Form for creating a new topic."""
    
    class Meta:
        model = Topic
        fields = ('name', )


class PostForm(forms.ModelForm):
    """Form for creating a new post."""
    
    class Meta:
        model = Post
        fields = ('body', )


class NewTopicForm(forms.Form):
    """Form for creating a new topic and 1st post to that topic."""
    name = forms.CharField(label='Subject', max_length=255)
    body = forms.CharField(label='', widget=forms.Textarea)

    def save(self, forum, user, ip=None):
        """
        Creates the new Topic and first Post from the form data and supplied
        forum and user objects.
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
