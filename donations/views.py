"""
Views for the donations application.
"""
import decimal
import datetime
import logging
from zoneinfo import ZoneInfo

import requests

from django.shortcuts import render
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView


from core.functions import email_admins
from donations.models import Donation

PP_DATE_FMT = '%H:%M:%S %b %d, %Y'

# Paypal reports payment_date as a Pacific wall clock with the zone as a
# trailing abbreviation. An abbreviation does not identify a zone on its own --
# PST is also Philippine Standard Time, sixteen hours the other way -- so these
# two are recognised because Paypal is known to report from Pacific, and any
# other is refused rather than guessed at. The offset comes from the date, not
# from the abbreviation, so a summer reading lands at -07:00 with no branch.
PP_TIME_ZONE = ZoneInfo('America/Los_Angeles')

# Which pass through an ambiguous wall clock the reading is. It matters for one
# hour a year: when the clocks go back, 01:30 happens twice and only the
# abbreviation can say which is meant. fold=1 is the second pass, standard time.
PP_ZONE_FOLD = {'PST': 1, 'PDT': 0}

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
    debug_response = getattr(settings, 'DONATIONS_DEBUG_VERIFY_RESPONSE', None)
    if debug_response is not None:
        return debug_response

    try:
        response = requests.post(
            paypal_params()[0],
            data=params,
            headers={'Content-type': 'application/x-www-form-urlencoded'},
            timeout=20)
        response.raise_for_status()
    except requests.RequestException as ex:
        logging.exception('IPN: exception verifying IPN: %s', ex)
        return None

    return response.text


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


def parse_payment_date(value):
    """
    Turn Paypal's payment_date into an aware datetime.

    Raises ValueError if the clock cannot be read, or if the zone is not one
    Paypal reports from -- the caller treats that as a refusal, since a wrong
    guess here is silently wrong data rather than a visible failure.
    """
    parts = value.rsplit(None, 1)
    if len(parts) != 2:
        raise ValueError('no timezone in payment_date "%s"' % value)

    clock, zone = parts
    if zone not in PP_ZONE_FOLD:
        raise ValueError('unexpected timezone "%s" in payment_date "%s"'
                         % (zone, value))

    naive = datetime.datetime.strptime(clock, PP_DATE_FMT)
    return naive.replace(tzinfo=PP_TIME_ZONE, fold=PP_ZONE_FOLD[zone])


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
            user = User.objects.get(username__iexact=params['custom'])
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
    except (KeyError, decimal.InvalidOperation):
        logging.error('IPN: invalid/missing mc_gross or mc_fee')
        return

    payment_date = params.get('payment_date')
    if payment_date is None:
        logging.error('IPN: missing payment_date')
        return

    try:
        payment_date = parse_payment_date(payment_date)
    except ValueError as error:
        # The listener answers Paypal 200 whatever happens here, so Paypal will
        # not retry and this donation has no second chance to be recorded. A log
        # line would be found only by someone already looking.
        logging.error('IPN: %s', error)
        email_admins('Donation IPN refused',
                     'A donation could not be recorded and Paypal will not '
                     'send it again:\n\n%s' % error)
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
