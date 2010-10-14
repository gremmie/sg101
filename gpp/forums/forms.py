"""
Forms for the forums application.
"""
from django import forms
from django.conf import settings

from forums.models import Forum
from forums.models import Topic
from forums.models import Post
from forums.attachments import AttachmentProcessor


class NewPostForm(forms.Form):
    """Form for creating a new post."""
    body = forms.CharField(label='', 
            widget=forms.Textarea(attrs={'class': 'markItUp smileyTarget'}))
    topic_id = forms.IntegerField(widget=forms.HiddenInput)
    topic = None

    class Media:
        css = {
            'all': (settings.GPP_THIRD_PARTY_CSS['markitup'] +
                settings.GPP_THIRD_PARTY_CSS['jquery-ui']),
        }
        js = (settings.GPP_THIRD_PARTY_JS['markitup'] + 
                settings.GPP_THIRD_PARTY_JS['jquery-ui'] +
                ('js/forums.js', ))

    def __init__(self, *args, **kwargs):
        super(NewPostForm, self).__init__(*args, **kwargs)
        attachments = args[0].getlist('attachment') if len(args) else []
        self.attach_proc = AttachmentProcessor(attachments)

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
        self.attach_proc.save_attachments(post)
        return post


class NewTopicForm(forms.Form):
    """
    Form for creating a new topic and 1st post to that topic.
    Superusers and moderators can also create the topic as a sticky or initially
    locked.
    """
    name = forms.CharField(label='Subject', max_length=255,
            widget=forms.TextInput(attrs={'size': 64}))
    body = forms.CharField(label='', 
            widget=forms.Textarea(attrs={'class': 'markItUp smileyTarget'}))
    user = None
    forum = None
    has_mod_fields = False

    class Media:
        css = {
            'all': (settings.GPP_THIRD_PARTY_CSS['markitup'] +
                settings.GPP_THIRD_PARTY_CSS['jquery-ui']),
        }
        js = (settings.GPP_THIRD_PARTY_JS['markitup'] + 
                settings.GPP_THIRD_PARTY_JS['jquery-ui'] +
                ('js/forums.js', ))

    def __init__(self, user, forum, *args, **kwargs):
        super(NewTopicForm, self).__init__(*args, **kwargs)
        self.user = user
        self.forum = forum

        if user.is_superuser or user in forum.moderators.all():
            self.fields['sticky'] = forms.BooleanField(required=False)
            self.fields['locked'] = forms.BooleanField(required=False)
            self.has_mod_fields = True

        attachments = args[0].getlist('attachment') if len(args) else []
        self.attach_proc = AttachmentProcessor(attachments)

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

        self.attach_proc.save_attachments(post)

        return topic


class PostForm(forms.ModelForm):
    """
    Form for editing an existing post or a new, non-quick post.
    """
    body = forms.CharField(label='', 
            widget=forms.Textarea(attrs={'class': 'markItUp smileyTarget'}))

    class Meta:
        model = Post
        fields = ('body', )

    class Media:
        css = {
            'all': (settings.GPP_THIRD_PARTY_CSS['markitup'] +
                settings.GPP_THIRD_PARTY_CSS['jquery-ui']),
        }
        js = (settings.GPP_THIRD_PARTY_JS['markitup'] + 
                settings.GPP_THIRD_PARTY_JS['jquery-ui'] +
                ('js/forums.js', ))


class MoveTopicForm(forms.Form):
    """
    Form for a moderator to move a topic to a forum.
    """
    forums = forms.ModelChoiceField(label='Move to forum', 
          queryset=Forum.objects.none())

    def __init__(self, user, *args, **kwargs):
        hide_label = kwargs.pop('hide_label', False) 
        required = kwargs.pop('required', True)
        super(MoveTopicForm, self).__init__(*args, **kwargs)
        self.fields['forums'].queryset = \
            Forum.objects.forums_for_user(user).order_by('name')
        if hide_label:
            self.fields['forums'].label = ''
        self.fields['forums'].required = required


class SplitTopicForm(forms.Form):
    """
    Form for a moderator to split posts from a topic to a new topic.
    """
    name = forms.CharField(label='New topic title', max_length=255,
            widget=forms.TextInput(attrs={'size': 64}))
    forums = forms.ModelChoiceField(label='Forum for new topic', 
          queryset=Forum.objects.none())
    post_ids = []
    split_at = False

    def __init__(self, user, *args, **kwargs):
        super(SplitTopicForm, self).__init__(*args, **kwargs)
        self.fields['forums'].queryset = \
            Forum.objects.forums_for_user(user).order_by('name')

    def clean(self):
        self.post_ids = self.data.getlist('post_ids')
        if len(self.post_ids) == 0:
            raise forms.ValidationError('Please select some posts')

        self.split_at = 'split-at' in self.data
        if self.split_at and len(self.post_ids) > 1:
            raise forms.ValidationError('Please select only one post to split the topic at')

        return self.cleaned_data
