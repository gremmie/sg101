"""
Views for the messages application.

"""
import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
import django.utils.simplejson as json

from messages.models import Message, Options
from messages.forms import OptionsForm, ComposeForm
from messages.utils import reply_subject, quote_message
from messages import MSG_BOX_LIMIT


MSGS_PER_PAGE = 20      # message pagination value

# This must match the jQuery UI tab control
TAB_INDICES = {
    'inbox': 0,
    'compose': 1,
    'outbox': 2,
    'trash': 3,
    'options': 4,
}


def _get_page(request):
    try:
        n = int(request.GET.get('page', '1'))
    except ValueError:
        n = 1
    return n


def _quota_check(box_name, count, request):
    """
    Checks the message box count against MSG_BOX_LIMIT.
    Emits a message to the user if the quota is exceeded.

    """
    if count >= MSG_BOX_LIMIT:
        django_messages.warning(request,
            "Your %s is full. Please delete some messages." % box_name)


@login_required
def index(request, tab=None):
    """
    This function displays the base tabbed private messages view.

    """
    tab_index = TAB_INDICES[tab] if tab else 0
    return render(request, 'messages/tabbed_base.html', {
        'tab': tab_index,
        'unread_count': Message.objects.unread_count(request.user),
        })


@login_required
def compose_to(request, receiver):
    """
    This function displays the base tabbed private messages view,
    and configures it to display the compose PM tab for the given
    receiver.

    """
    user = get_object_or_404(User, username=receiver)
    tab_index = TAB_INDICES['compose']
    return render(request, 'messages/tabbed_base.html', {
        'tab': tab_index,
        'receiver': receiver,
        'unread_count': Message.objects.unread_count(request.user),
        })


def inbox(request):
    """
    Returns the inbox for the user.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    msg_list = Message.objects.inbox(request.user)
    _quota_check('inbox', msg_list.count(), request)

    paginator = Paginator(msg_list, MSGS_PER_PAGE)
    try:
        msgs = paginator.page(_get_page(request))
    except EmptyPage, InvalidPage:
        msgs = paginator.page(paginator.num_pages)

    return render(request, 'messages/inbox_tab.html', {
        'msgs': msgs,
        'url': reverse('messages-inbox'),
        })


def outbox(request):
    """
    Returns the outbox for the user.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    msg_list = Message.objects.outbox(request.user)
    _quota_check('outbox', msg_list.count(), request)

    paginator = Paginator(msg_list, MSGS_PER_PAGE)
    try:
        msgs = paginator.page(_get_page(request))
    except EmptyPage, InvalidPage:
        msgs = paginator.page(paginator.num_pages)

    return render(request, 'messages/outbox_tab.html', {
        'msgs': msgs,
        'url': reverse('messages-outbox'),
        })


def trash(request):
    """
    Returns the trash for the user.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    msg_list = Message.objects.trash(request.user)
    paginator = Paginator(msg_list, MSGS_PER_PAGE)
    try:
        msgs = paginator.page(_get_page(request))
    except EmptyPage, InvalidPage:
        msgs = paginator.page(paginator.num_pages)

    return render(request, 'messages/trash_tab.html', {
        'msgs': msgs,
        'url': reverse('messages-trash'),
        })


def message(request):
    """
    This view function retrieves a message and returns it as a JSON object.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    msg_id = request.POST.get('msg_id')
    msg = get_object_or_404(Message.objects.select_related(), pk=msg_id)
    if msg.sender != request.user and msg.receiver != request.user:
        return HttpResponseForbidden()

    if msg.receiver == request.user and msg.read_date is None:
        msg.read_date = datetime.datetime.now()
        msg.save()

    msg_dict = dict(subject=msg.subject,
                    sender=msg.sender.username,
                    receiver=msg.receiver.username,
                    content=msg.html,
                    re_subject=reply_subject(msg.subject),
                    re_content=quote_message(msg.sender.username, msg.send_date,
                                             msg.message))

    result = json.dumps(msg_dict, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')


def options(request):
    """
    This view handles the displaying and changing of private message options.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    if request.method == "POST":
        options = Options.objects.for_user(request.user)
        form = OptionsForm(request.POST, instance=options, prefix='opts')
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Options saved.')
    else:
        options = Options.objects.for_user(request.user)
        form = OptionsForm(instance=options, prefix='opts')

    return render(request, 'messages/options_tab.html', {
        'form': form,
        })


def compose(request, receiver=None):
    """
    Process or prepare the compose form to create a new private message.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    if request.method == "POST":
        compose_form = ComposeForm(request.user, request.POST)

        # Is this a reply to another message?
        parent_msg_id = request.POST.get('reply_to')
        if parent_msg_id:
            parent_msg = get_object_or_404(Message, id=parent_msg_id)
            if (request.user != parent_msg.receiver and
                request.user != parent_msg.sender):
                return HttpResponseForbidden()
        else:
            parent_msg = None

        if compose_form.is_valid():
            compose_form.save(parent_msg=parent_msg)
            django_messages.success(request, 'Message sent.')
            compose_form = ComposeForm(request.user)
    else:
        if receiver is not None:
            form_data = {'receiver': receiver}
            compose_form = ComposeForm(request.user, initial=form_data)
        else:
            compose_form = ComposeForm(request.user)

        _quota_check('outbox', Message.objects.outbox(request.user).count(), request)

    return render(request, 'messages/compose_tab.html', {
        'compose_form': compose_form,
        })


def _only_integers(slist):
    """
    Accepts a list of strings. Returns a list of integers consisting of only
    those elements from the original list that could be converted to integers

    """
    result = []
    for s in slist:
        try:
            n = int(s)
        except ValueError:
            pass
        else:
            result.append(n)
    return result


def _delete_msgs(user, msg_ids):
    """
    Deletes the messages given by the list of msg_ids. For this to succeed, the
    user has to be either the sender or receiver on each message.

    """
    msg_ids = _only_integers(msg_ids)
    msgs = Message.objects.filter(id__in=msg_ids)

    for msg in msgs:
        if msg.sender == user:
            if (msg.receiver_delete_date is not None or
                    msg.read_date is None):
                # Both parties deleted the message or receiver hasn't read it
                # yet, we can delete it now
                msg.delete()
            else:
                # receiver still has it in inbox
                msg.sender_delete_date = datetime.datetime.now()
                msg.save()

        elif msg.receiver == user:
            if msg.sender_delete_date is not None:
                # both parties deleted the message, we can delete it now
                msg.delete()
            else:
                # sender still has it in the outbox
                msg.receiver_delete_date = datetime.datetime.now()
                msg.save()


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
