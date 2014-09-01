"""
Views for the messages application.

"""
import datetime
import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect

from messages.models import Message, Options
from messages.forms import OptionsForm, ComposeForm
from messages.utils import reply_subject
from messages import MSG_BOX_LIMIT
from core.functions import quote_message


MSGS_PER_PAGE = 20      # message pagination value

# This must match the jQuery UI tab control
TAB_INDICES = {
    'inbox': 0,
    'compose': 1,
    'outbox': 2,
    'trash': 3,
    'options': 4,
}


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
    if request.method == 'POST':
        form = ComposeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Reply sent.')
            return redirect('messages-inbox')
    else:
        msg = get_object_or_404(Message.objects.select_related(), pk=msg_id)
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

    return render(request, 'messages/view_message.html', {
        'msg': msg,
        'form': form,
        })


def _delete_pms(user, pm_ids):
    """
    Process the request to delete the list of PM ids by user.

    """
    msgs = Message.objects.filter(id__in=pm_ids)
    now = datetime.datetime.now()

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
        elif msg.receiver == user:
            if msg.sender_delete_date is not None:
                # both parties deleted the message, we can delete it now
                msg.delete()
            else:
                # sender still has PM in their inbox
                msg.receiver_delete_date = now
                msg.save()


@login_required
@require_POST
def delete(request):
    """
    Deletes the requested PM's. The user must be either a sender or receiver for
    this to work.

    """
    pm_ids = request.POST.getlist('pm_ids')
    if pm_ids:
        _delete_pms(request.user, pm_ids)

    # Figure out where to redirect to
    src = request.POST.get('src', 'inbox')
    try:
        page = int(request.POST.get('page', '1'))
    except ValueError:
        page = 1

    view_name = 'messages-inbox' if src == inbox else 'messages-outbox'
    url = reverse(view_name) + '?page={}'.format(page)
    return redirect(url)


def _undelete_msgs(user, msg_ids):
    """
    Attempts to "undelete" the messages given by the msg_ids list.
    This will only succeed if the user is either the sender or receiver.

    """
    msg_ids = _only_integers(msg_ids)
    msgs = Message.objects.filter(id__in=msg_ids)
    for msg in msgs:
        if msg.sender == user:
            msg.sender_delete_date = None
            msg.save()
        elif msg.receiver == user:
            msg.receiver_delete_date = None
            msg.save()


def bulk(request):
    """
    This view processes messages in bulk. Arrays of message ids are expected in
    the POST query dict: inbox_ids and outbox_ids will be deleted; trash_ids will
    be undeleted.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    delete_ids = []
    if 'inbox_ids' in request.POST:
        delete_ids.extend(request.POST.getlist('inbox_ids'))
    if 'outbox_ids' in request.POST:
        delete_ids.extend(request.POST.getlist('outbox_ids'))

    if len(delete_ids):
        _delete_msgs(request.user, delete_ids)

    if 'trash_ids' in request.POST:
        _undelete_msgs(request.user, request.POST.getlist('trash_ids'))

    return HttpResponse('');
