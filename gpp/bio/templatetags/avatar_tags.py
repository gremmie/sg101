"""
Template tags for the bio application. 
"""
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def avatar(user, align='bottom'):
   alt = user.username
   title = alt
   try:
      profile = user.get_profile()
   except:
      profile = None
   if profile is None or profile.avatar.name == '':
      url = settings.AVATAR_DEFAULT_URL
      width = settings.MAX_AVATAR_SIZE_PIXELS
      height = settings.MAX_AVATAR_SIZE_PIXELS
   else:
      url = profile.avatar.url
      width = profile.avatar.width
      height = profile.avatar.height

   style = ''
   if align == 'left':
      style = 'style="float:left;margin-right:3px;"'

   return u"""<img src="%s" alt="%s" title="%s" width="%s" height="%s" border="0" class="avatar" %s />""" % (
         url, alt, title, width, height, style)
