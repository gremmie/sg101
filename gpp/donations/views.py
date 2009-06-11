"""
Views for the donations application.
"""
import urllib2
import decimal
import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.contrib.auth.models import User

from donations.models import Donation

PP_DATE_FMT = '%H:%M:%S %b %d, %Y PST'

def paypal_params():
    """
    This function returns a tuple where the 1st element is the Paypal
    URL and the 2nd element is the Paypal business email. This information
    depends on the setting DONATIONS_DEBUG.
    """
    if settings.DONATIONS_DEBUG:
        form_action = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
        business = settings.DONATIONS_BUSINESS_DEBUG
    else:
        form_action = 'https://www.paypal.com/cgi-bin/webscr'
        business = settings.DONATIONS_BUSINESS

    return form_action, business


def index(request):
    gross, net, donations = Donation.objects.monthly_stats()
    current_site = Site.objects.get_current()
    form_action, business = paypal_params()

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
    """
    This function is the IPN listener and handles the IPN POST from Paypal.

    TODO: Add logging.
    """
    parameters = None
    try:
        if request['payment_status'] == 'Completed':
            if request.POST:
              parameters = request.POST.copy()
            else:
              parameters = request.GET.copy()

        if parameters:
            parameters['cmd']='_notify-validate'
            req = urllib2.Request(paypal_params()[0], parameters.urlencode())
            req.add_header("Content-type", "application/x-www-form-urlencoded")
            response = urllib2.urlopen(req)
            status = response.read()
            if status != "VERIFIED":
                parameters = None

        if parameters:
            # is this a donation to the site?
            try:
                item_number = int(parameters['item_number'])
            except ValueError:
                pass
            else:
                if item_number == settings.DONATIONS_ITEM_NUM or \
                   item_number == settings.DONATIONS_ITEM_ANON_NUM:
                    process_donation(item_number, parameters)

            return HttpResponse("Ok")

    except Exception, e:
        # print "An exeption was caught: " + str(e)
        pass

    return HttpResponseServerError("Error")


def process_donation(item_number, params):
    """
    Constructs a donation object from the parameters and stores
    in the database.
    """
    # Has this transaction been processed before?
    if 'txn_id' not in params:
        return
    txn_id = params['txn_id']
    try:
        donation = Donation.objects.get(txn_id__exact=txn_id)
    except Donation.DoesNotExist:
        pass
    else:
        return      # no exception, this is a duplicate

    # Is the email address ours?
    business = params.get('business')
    if business != paypal_params()[1]:
        return

    # is this a payment received?
    txn_type = params.get('txn_type')
    if txn_type != 'web_accept':
        return

    # Looks like a donation, save it to the database.
    # Determine which user this came from, if any.
    # The username is stored in the custom field if the user was logged in when
    # the donation was made.
    user = None
    if 'custom' in params:
        try:
            user = User.objects.get(username__exact=params['custom'])
        except User.DoesNotExist:
            pass

    is_anonymous = item_number == settings.DONATIONS_ITEM_ANON_NUM
    test_ipn = params.get('test_ipn') == '1'

    first_name = params.get('first_name', '')
    last_name = params.get('last_name', '')
    payer_email = params.get('payer_email', '')
    payer_id = params.get('payer_id', '')
    memo = params.get('memo', '')
    payer_status = params.get('payer_status', '')

    try:
        mc_gross = decimal.Decimal(params['mc_gross'])
        mc_fee = decimal.Decimal(params['mc_fee'])
    except KeyError, decimal.InvalidOperation:
        return

    try:
        payment_date = datetime.datetime.strptime(params['payment_date'], 
                PP_DATE_FMT)
    except KeyError, ValueError:
        return

    donation = Donation(
        user=user,
        is_anonymous=is_anonymous,
        test_ipn=test_ipn,
        txn_id=txn_id,
        first_name=first_name,
        last_name=last_name,
        payer_email=payer_email,
        payer_id=payer_id,
        memo=memo,
        payer_status=payer_status,
        mc_gross=mc_gross,
        mc_fee=mc_fee,
        payment_date=payment_date)

    donation.save()

