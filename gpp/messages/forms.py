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
from core.functions import get_full_name
from core.widgets import AutoCompleteUserInput
from messages.models import Message
from messages.models import Options


class ComposeForm(forms.Form):
   """
   This form is used to compose private messages.
   """
   receiver = forms.CharField(label='To', 
         max_length=30,
         widget=AutoCompleteUserInput())
   subject = forms.CharField(max_length=120, widget=forms.TextInput(attrs={'size': 52}))
   message = forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 80}))
   attach_signature = forms.BooleanField(label='Attach Signature?', required=False)

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
      if self.user.username.lower() == receiver.lower():
         raise forms.ValidationError("You can't send a message to yourself.")
      return receiver

   def save(self, sender, parent_msg=None):
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
      new_msg.save()
      if parent_msg is not None:
         parent_msg.reply_date = new_msg.send_date
         parent_msg.save()

      receiver_opts = Options.objects.for_user(receiver)
      if receiver_opts.notify_email:
         notify_receiver(new_msg)

   class Media:
      css = {
         'all': settings.GPP_THIRD_PARTY_CSS['markitup'],
      }
      js = ('js/messages/compose.js', ) + settings.GPP_THIRD_PARTY_JS['markitup']


class OptionsForm(forms.ModelForm):
   class Meta:
      model = Options


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
