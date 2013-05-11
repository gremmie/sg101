"""Views for the IRC application"""

from django.shortcuts import render

from irc.channel import get_users


def view(request):
   nicks = get_users()
   return render(request, 'irc/view.html', {'nicks': nicks})
