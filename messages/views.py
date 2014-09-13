"""
Views for the messages application.

"""
import datetime

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages as django_messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.db.models import Q
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.conf import settings

from messages.models import Flag, Message, Options
from messages.forms import OptionsForm, ComposeForm, ReportForm
from messages.utils import reply_subject
from messages import MSG_BOX_LIMIT
from core.functions import email_admins, quote_message, send_mail


MSGS_PER_PAGE = 20      # message pagination value
PM_EMAIL_MAX = 100      # max messages we will send via email

REPORT_SUBJECT = 'A user has flagged a private message'
REPORT_MSG = """Hello,

A user has flagged a private message for review.
"""


def _quota_check(box_name, count, request):
    """
    Checks the message box count against MSG_BOX_LIMIT.
    Emits a message to the user if the quota is exceeded.

    Returns the percent used as an integer between 0-100.

    """
    if count >= MSG_BOX_LIMIT:
        django_messages.warning(request,
            "Your %s is full. Please delete some messages." % box_name)

    return 100 * count / MSG_BOX_LIMIT


def _get_page(request, qs):
    """Paginates the given queryset and returns a page object"""
    paginator = Paginator(qs, MSGS_PER_PAGE)
    try:
        page = paginator.page(request.GET.get('page', '1'))
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page


@login_required
def inbox(request):

    msg_list = Message.objects.inbox(request.user)
    msg_count = msg_list.count()
    pct_used = _quota_check('inbox', msg_count, request)

    page = _get_page(request, msg_list)

    return render(request, 'messages/inbox.html', {
        'tab': 'inbox',
        'page': page,
        'inbox_pct': pct_used,
        'outbox_pct': None,
        })


@login_required
def outbox(request):

    msg_list = Message.objects.outbox(request.user)
    msg_count = msg_list.count()
    pct_used = _quota_check('outbox', msg_count, request)

    page = _get_page(request, msg_list)

    return render(request, 'messages/outbox.html', {
        'tab': 'outbox',
        'page': page,
        'inbox_pct': None,
        'outbox_pct': pct_used,
        })


@login_required
def trash(request):

    msg_list = Message.objects.trash(request.user)

    page = _get_page(request, msg_list)

    return render(request, 'messages/trash.html', {
        'tab': 'trash',
        'page': page,
        'inbox_pct': None,
        'outbox_pct': None,
        })


@login_required
def options(request):
    """
    This view handles the displaying and changing of private message options.

    """
    if request.method == 'POST':
        options = Options.objects.for_user(request.user)
        form = OptionsForm(request.POST, instance=options, prefix='opts')
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Options saved.')
            return redirect('messages-options')
    else:
        options = Options.objects.for_user(request.user)
        form = OptionsForm(instance=options, prefix='opts')

    return render(request, 'messages/options.html', {
        'tab': 'options',
        'form': form,
        })


@login_required
def compose(request):
    """
    Process or prepare the compose form to create a new private message.

    """
    if request.method == 'POST':
        compose_form = ComposeForm(request.user, request.POST)
        if compose_form.is_valid():
            compose_form.save()
            django_messages.success(request, 'Message sent.')
            compose_form = ComposeForm(request.user)
    else:
        receiver = request.GET.get('to')
        if receiver:
            form_data = {'receiver': receiver}
            compose_form = ComposeForm(request.user, initial=form_data)
        else:
            compose_form = ComposeForm(request.user)

        _quota_check('outbox', Message.objects.outbox(request.user).count(), request)

    return render(request, 'messages/compose.html', {
        'tab': 'compose',
        'compose_form': compose_form,
        })


@login_required
def view(request, msg_id):
    """
    This view function displays a private message for reading to the user. If
    the user is a recipient of the message, a reply can be composed and sent.

    """
    msg = get_object_or_404(Message.objects.select_related(), pk=msg_id)

    if request.method == 'POST':
        form = ComposeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Reply sent.')
            return redirect('messages-inbox')
    else:
        if msg.sender != request.user and msg.receiver != request.user:
            django_messages.error(request,
                    "You don't have permission to read that message.")
            return redirect('messages-inbox')

        initial_data = {
            'receiver': msg.sender.username,
            'subject': reply_subject(msg.subject),
            'message': quote_message(msg.sender.username, msg.message),
            'parent_id': msg.pk,
        }

        if msg.receiver == request.user:
            if msg.read_date is None:
                msg.read_date = datetime.datetime.now()
                msg.save()
        else:
            initial_data['receiver'] = msg.receiver.username

        form = ComposeForm(request.user, initial=initial_data)

    try:
        msg_flag = msg.flag
    except Flag.DoesNotExist:
        msg_flag = None

    return render(request, 'messages/view_message.html', {
        'msg': msg,
        'form': form,
        'msg_flag': msg_flag,
        })


@login_required
@require_POST
def bulk(request):
    """
    Perform bulk action on a list of PMs.

    """
    pm_ids = request.POST.getlist('pm_ids')

    # Figure out what action to perform
    action = None
    action_val = request.POST.get('action', '')
    if action_val.startswith('Delete'):
        action = _delete_pms
    elif action_val.startswith('Email'):
        action = _email_pms

    if pm_ids and action:
        action(request, pm_ids)

    # Figure out where to redirect to
    src = request.POST.get('src', 'inbox')
    try:
        page = int(request.POST.get('page', '1'))
    except ValueError:
        page = 1

    view_name = 'messages-inbox' if src == 'inbox' else 'messages-outbox'
    url = reverse(view_name) + '?page={}'.format(page)
    return redirect(url)


def _delete_pms(request, pm_ids):
    """
    Process the request to delete the list of PM ids by user.

    Returns the number of PM's deleted.

    """
    user = request.user
    msgs = Message.objects.filter(id__in=pm_ids)
    now = datetime.datetime.now()

    count = 0
    for msg in msgs:
        if msg.sender == user:
            if msg.receiver_delete_date is not None or msg.read_date is None:
                # Both parties deleted the message or receiver hasn't read it
                # yet, we can delete it now
                msg.delete()
            else:
                # receiver still has PM in their inbox
                msg.sender_delete_date = now
                msg.save()
            count += 1
        elif msg.receiver == user:
            if msg.sender_delete_date is not None:
                # both parties deleted the message, we can delete it now
                msg.delete()
            else:
                # sender still has PM in their inbox
                msg.receiver_delete_date = now
                msg.save()
            count += 1

    msg = '{} message{} deleted.'.format(count, '' if count == 1 else 's')
    if count > 0:
        django_messages.success(request, msg)
    else:
        django_messages.error(request, msg)


def _undelete_pms(user, msg_ids):
    """
    Attempts to "undelete" the messages given by the msg_ids list.
    This will only succeed if the user is either the sender or receiver.

    Returns the number of PM's undeleted.

    """
    msgs = Message.objects.filter(id__in=msg_ids)
    count = 0
    for msg in msgs:
        if msg.sender == user:
            msg.sender_delete_date = None
            msg.save()
            count += 1
        elif msg.receiver == user:
            msg.receiver_delete_date = None
            msg.save()
            count += 1
    return count


@login_required
@require_POST
def undelete(request):
    """
    Undeletes the requested PM's. The user must be either a sender or receiver for
    this to work.

    """
    pm_ids = request.POST.getlist('pm_ids')
    if pm_ids:
        count = _undelete_pms(request.user, pm_ids)
        msg = '{} message{} undeleted.'.format(count, '' if count == 1 else 's')
        django_messages.success(request, msg)

    # Figure out where to redirect to
    try:
        page = int(request.POST.get('page', '1'))
    except ValueError:
        page = 1

    url = reverse('messages-trash') + '?page={}'.format(page)
    return redirect(url)


@login_required
def report(request, msg_id):
    """This view is for reporting a PM as spam or abuse.

    """
    msg = get_object_or_404(Message.objects.select_related(), pk=msg_id)
    if msg.receiver != request.user:
        django_messages.error(request, "You can't report this message.")
        return redirect('messages-inbox')
    try:
        msg.flag
    except Flag.DoesNotExist:
        pass
    else:
        django_messages.error(request, "This message has already been reported.")
        return redirect('messages-inbox')

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            flag = form.save(commit=False)
            flag.message = msg
            flag.save()
            email_admins(REPORT_SUBJECT, REPORT_MSG)
            django_messages.success(request,
                    'Message reported. An admin will be notified. Thank you.')
            return redirect('messages-inbox')
    else:
        form = ReportForm()

    return render(request, 'messages/report_message.html', {
        'msg': msg,
        'form': form,
        })


def _email_pms(request, msg_ids):
    """
    Attempts to email the messages given by the msg_ids list to the user.
    This will only succeed if the user is either the sender or receiver.

    Returns the number of PM's sent.

    """
    # Does the user have an email address?
    user = request.user
    email_addr = user.email
    if not email_addr:
        return 0

    msgs = Message.objects.filter(
            Q(sender=user) | Q(receiver=user),
            id__in=msg_ids).order_by('pk')[:PM_EMAIL_MAX]

    count = len(msgs)
    if count == 0:
        return 0

    site = Site.objects.get_current()
    admin_email = settings.ADMINS[0][1]

    subject = 'Private messages from {} - {}'.format(site.domain,
            msgs[0].subject)
    if count > 1:
        subject += ' (et al.)'
    from_email = '{}@{}'.format(settings.GPP_NO_REPLY_EMAIL, site.domain)
    msg_body = render_to_string('messages/pm_email.txt', {
                    'site': site,
                    'user': user,
                    'msgs': msgs,
                    'admin_email': admin_email,
                })
    send_mail(subject, msg_body, from_email, [email_addr], defer=False)

    msg = '{} message{} sent to email.'.format(count, '' if count == 1 else 's')
    if count > 0:
        django_messages.success(request, msg)
    else:
        django_messages.error(request, msg)
