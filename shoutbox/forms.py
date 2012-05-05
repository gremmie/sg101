"""
Forms for the Shoutbox application.
"""

import re
from django import forms

url_re = re.compile('('
   r'^https?://' # http:// or https://
   r'(?:(?:[A-Z0-9-]+\.)+[A-Z]{2,6}|' #domain...
   r'localhost|' #localhost...
   r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
   r'(?::\d+)?' # optional port
   r'(?:/?|/\S+))', re.IGNORECASE)


class ShoutBoxForm(forms.Form):
   msg = forms.CharField(label='', max_length=2048, required=True)

   def get_shout(self):
      msg = self.cleaned_data['msg']
      msg = re.sub(url_re, r'<a href="\1">URL</a>', msg)
      return msg

