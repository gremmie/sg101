"""
Views for the donations application.
"""
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404     # TODO: remove
from django.conf import settings
from django.contrib.sites.models import Site

from donations.models import Donation


def index(request):
    gross, net, donations = Donation.objects.monthly_stats()
    current_site = Site.objects.get_current()

    if settings.DEBUG:
        form_action = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
        business = settings.DONATIONS_BUSINESS_DEBUG
    else:
        form_action = 'https://www.paypal.com/cgi-bin/webscr'
        business = settings.DONATIONS_BUSINESS

    return render_to_response('donations/index.html', {
        'goal': settings.DONATIONS_GOAL,
        'gross': gross,
        'net': net,
        'left': settings.DONATIONS_GOAL - net,
        'donations': donations,
        'form_action': form_action,
        'business': business,
        'anonymous': settings.DONATIONS_ANON_NAME,
        'item_name': settings.DONATIONS_ITEM_NAME,
        'item_number': settings.DONATIONS_ITEM_NUM,
        'item_anon_number': settings.DONATIONS_ITEM_ANON_NUM,
        'domain': current_site.domain,
        },
        context_instance = RequestContext(request))


def ipn(request):
    raise Http404       #TODO


def thanks(request):
    raise Http404       #TODO
