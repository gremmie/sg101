"""
Forms for the messages application.

"""
from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from core.functions import send_mail
from core.html import ImageCheckError
from core.html import image_check
from core.markup import site_markup
import messages
from messages.models import Flag, Message, Options


# Maximum size of a private message in characters
MESSAGE_MAX = getattr(settings, 'MESSAGES_MAX_SIZE', 8192)


class ComposeForm(forms.Form):
    """
    This form is used to compose private messages.
    """
    receiver = forms.CharField(label='To',
            max_length=30,
            widget=forms.TextInput(attrs={'class': 'sg101-user-autocomplete'}))
    subject = forms.CharField(max_length=120)
    message = forms.CharField(widget=forms.Textarea)
    attach_signature = forms.BooleanField(label='Attach Signature?', required=False)
    parent_id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    def __init__(self, user, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        self.user = user
        options = Options.objects.for_user(user)
        self.fields['attach_signature'].initial = options.attach_signature

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']
        try:
            self.rcvr_user = User.objects.get(username=receiver)
        except User.DoesNotExist:
            raise forms.ValidationError("That username does not exist.")
        if self.user == self.rcvr_user:
            raise forms.ValidationError("You can't send a message to yourself.")
        return receiver

    def clean_message(self):
        msg = self.cleaned_data['message'].strip()
        if len(msg) > MESSAGE_MAX:
            raise forms.ValidationError("Your message is too long. Please trim some text.")

        self.html = None
        if not msg:
            raise forms.ValidationError("Please enter a message.")

        self.html = site_markup(msg)
        try:
            image_check(self.html)
        except ImageCheckError as ex:
            raise forms.ValidationError(str(ex))

        return msg

    def clean(self):
        rcvr = self.cleaned_data.get('receiver')
        subject = self.cleaned_data.get('subject')
        message = self.cleaned_data.get('message')

        if rcvr and subject and message:
            # Can we send a message? Is our outbox full?

            count = Message.objects.outbox(self.user).count()
            if count >= messages.MSG_BOX_LIMIT:
                raise forms.ValidationError(
                        "Your outbox is full. Please delete some messages.")

            # Is the receiver's inbox full?
            count = Message.objects.inbox(self.rcvr_user).count()
            if count >= messages.MSG_BOX_LIMIT:
                raise forms.ValidationError(
                    "Sorry, %s's inbox is full. This message cannot be sent." %
                    self.rcvr_user.username)

        return self.cleaned_data

    def save(self, parent_msg=None):
        sender = self.user
        receiver = self.rcvr_user
        subject = self.cleaned_data['subject']
        message = self.cleaned_data['message']
        attach_signature = self.cleaned_data['attach_signature']

        new_msg = Message(
            sender=sender,
            receiver=receiver,
            subject=subject,
            message=message,
            signature_attached=attach_signature,
        )
        new_msg.save(html=self.html)

        # Update the parent message (if there is one)
        parent_id = self.cleaned_data['parent_id']
        if parent_id:
            try:
                parent_msg = Message.objects.get(pk=parent_id)
            except Message.DoesNotExist:
                parent_msg = None

            if parent_msg and parent_msg.receiver == self.user:
                parent_msg.reply_date = new_msg.send_date
                parent_msg.save()

        # Notify recipient
        receiver_opts = Options.objects.for_user(receiver)
        if receiver_opts.notify_email:
            notify_receiver(new_msg)


class OptionsForm(forms.ModelForm):
    class Meta:
        model = Options
        fields = ['attach_signature', 'notify_email']


class ReportForm(forms.ModelForm):
    class Meta:
        model = Flag
        fields = ['comments']
        labels = {'comments': ''}
        widgets = {
            'comments': forms.Textarea(attrs={
                'placeholder': 'Enter a comment for the admin (optional).'})
        }


def notify_receiver(new_msg):
    """
    This function creates the notification email to notify a user of
    a new private message.
    """
    site = Site.objects.get_current()

    email_body = render_to_string('messages/notification_email.txt', {
                'site': site,
                'msg': new_msg,
                'options_url': reverse('messages-options'),
            })

    subject = 'New private message for %s at %s' % (new_msg.receiver.username, site.name)
    from_email = settings.GPP_NO_REPLY_EMAIL + '@' + site.domain
    send_mail(subject, email_body, from_email, [new_msg.receiver.email])
