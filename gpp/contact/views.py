# Create your views here.

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from contact.forms import ContactForm
from core.functions import get_full_name


def contact_form(request):
   if request.method == 'POST':
      form = ContactForm(request.POST)
      if form.is_valid():
         form.save()
         return HttpResponseRedirect(reverse('contact.views.contact_thanks'))
   else:
      initial_data = {}
      if request.user.is_authenticated():
         name = get_full_name(request.user)
         initial_data = {'name' : name, 'email' : request.user.email}

      form = ContactForm(initial = initial_data)

   return render_to_response('contact/contact_form.html', 
         {'form' : form}, 
         context_instance = RequestContext(request))


def contact_thanks(request):
   return render_to_response('contact/contact_thanks.html', 
         context_instance = RequestContext(request))
