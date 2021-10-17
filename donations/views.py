"""
Views for the donations application.
"""
import urllib2
import decimal
import datetime
import logging

from django.shortcuts import render
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView


from donations.models import Donation

PP_DATE_FMT = '%H:%M:%S %b %d, %Y'

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


def verify_request(params):
    """
    Send the parameters back to Paypal and return the response string.
    """
    # If we are doing localhost-type unit tests, just return whatever
    # the test wants us to...
    if hasattr(settings, 'DONATIONS_DEBUG_VERIFY_RESPONSE'):
        return settings.DONATIONS_DEBUG_VERIFY_RESPONSE

    req = urllib2.Request(paypal_params()[0], params)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    try:
        response = urllib2.urlopen(req)
    except urllib2.URLError as ex:
        logging.exception('IPN: exception verifying IPN: %s', ex)
        return None

    return response.read()


def index(request):
    gross, net, donations = Donation.objects.monthly_stats()
    goal = settings.DONATIONS_GOAL
    current_site = Site.objects.get_current()
    form_action, business = paypal_params()

    pct = max(0, min(100, int(net / goal * 100)))

    return render(request, 'donations/index.html', {
        'goal': goal,
        'gross': gross,
        'net': net,
        'left': settings.DONATIONS_GOAL - net,
        'pct': pct,
        'donations': donations,
        'form_action': form_action,
        'business': business[0],
        'anonymous': settings.DONATIONS_ANON_NAME,
        'item_name': settings.DONATIONS_ITEM_NAME,
        'item_number': settings.DONATIONS_ITEM_NUM,
        'item_anon_number': settings.DONATIONS_ITEM_ANON_NUM,
        'domain': current_site.domain,
        'V3_DESIGN': True,
        })


class ThanksView(TemplateView):
    template_name = 'donations/thanks.html'

    def get_context_data(self, **kwargs):
        context = super(ThanksView, self).get_context_data(**kwargs)
        context['V3_DESIGN'] = True
        return context


@csrf_exempt
def ipn(request):
    """
    This function is the IPN listener and handles the IPN POST from Paypal.
    The algorithm here roughly follows the outline described in chapter 2
    of Paypal's IPNGuide.pdf "Implementing an IPN Listener".

    """
    # Log some info about this IPN event
    ip = request.META.get('REMOTE_ADDR', '?')
    parameters = request.POST.copy()
    logging.info('IPN from %s; post data: %s', ip, parameters.urlencode())

    # Now we follow the instructions in chapter 2 of the Paypal IPNGuide.pdf.
    # Create a request that contains exactly the same IPN variables and values in
    # the same order, preceded with cmd=_notify-validate
    parameters['cmd']='_notify-validate'

    # Post the request back to Paypal (either to the sandbox or the real deal),
    # and read the response:
    status = verify_request(parameters.urlencode())
    if status != 'VERIFIED':
        logging.warning('IPN: Payapl did not verify; status was %s', status)
        return HttpResponse()

    # Response was VERIFIED; act on this if it is a Completed donation, 
    # otherwise don't handle it (we are just a donations application. Here
    # is where we could be expanded to be a more general payment processor).

    payment_status = parameters.get('payment_status')
    if payment_status != 'Completed':
        logging.info('IPN: payment_status is %s; we are done.', payment_status)
        return HttpResponse()

    # Is this a donation to the site?
    item_number = parameters.get('item_number')
    if (item_number == settings.DONATIONS_ITEM_NUM or
        item_number == settings.DONATIONS_ITEM_ANON_NUM):
        process_donation(item_number, parameters)
    else:
        logging.info('IPN: not a donation; done.')

    return HttpResponse()


def process_donation(item_number, params):
    """
    A few validity and duplicate checks are made on the donation params.
    If everything is ok, construct a donation object from the parameters and
    store it in the database.

    """
    # Has this transaction been processed before?
    txn_id = params.get('txn_id')
    if txn_id is None:
        logging.error('IPN: missing txn_id')
        return

    try:
        donation = Donation.objects.get(txn_id__exact=txn_id)
    except Donation.DoesNotExist:
        pass
    else:
        logging.warning('IPN: duplicate txn_id')
        return      # no exception, this is a duplicate

    # Is the email address ours?
    business = params.get('business')
    if business not in paypal_params()[1]:
        logging.warning('IPN: invalid business: %s', business)
        return

    # is this a payment received?
    txn_type = params.get('txn_type')
    if txn_type != 'web_accept':
        logging.warning('IPN: invalid txn_type: %s', txn_type)
        return

    # Looks like a donation, save it to the database.
    # Determine which user this came from, if any.
    # The username is stored in the custom field if the user was logged in when
    # the donation was made.
    user = None
    if 'custom' in params and params['custom']:
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
        logging.error('IPN: invalid/missing mc_gross or mc_fee')
        return

    payment_date = params.get('payment_date')
    if payment_date is None:
        logging.error('IPN: missing payment_date')
        return

    # strip off the timezone
    payment_date = payment_date[:-4]
    try:
        payment_date = datetime.datetime.strptime(payment_date, PP_DATE_FMT)
    except ValueError:
        logging.error('IPN: invalid payment_date "%s"', params['payment_date'])
        return

    try:
        donation = Donation(
            user=user,
            is_anonymous=is_anonymous,
            test_ipn=test_ipn,
            txn_id=txn_id,
            txn_type=txn_type,
            first_name=first_name,
            last_name=last_name,
            payer_email=payer_email,
            payer_id=payer_id,
            memo=memo,
            payer_status=payer_status,
            mc_gross=mc_gross,
            mc_fee=mc_fee,
            payment_date=payment_date)
    except:
        logging.exception('IPN: exception during donation creation')
    else:
        donation.save()
        logging.info('IPN: donation saved')
