"""Views for the messages application"""

import datetime
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.decorators.http import require_POST

from messages.models import Message
from messages.models import Options
from messages.forms import ComposeForm
from messages.forms import OptionsForm
from messages.utils import reply_subject
from messages.utils import quote_message


BOX_MAP = {
    'inbox': 'messages-inbox',
    'outbox': 'messages-outbox',
    'trash': 'messages-trash',
}


def box_redirect(request):
    """
    Determines which box to redirect to by looking for a GET or
    POST parameter.
    """
    if request.method == 'GET':
        box = request.GET.get('box', 'inbox')
    else:
        box = request.POST.get('box', 'inbox')
    if BOX_MAP.has_key(box):
        url = reverse(BOX_MAP[box])
    else:
        url = reverse(BOX_MAP['inbox'])
    return HttpResponseRedirect(url)


@login_required
def inbox(request):
    """Displays the inbox for the user making the request."""
    msgs = Message.objects.inbox(request.user)
    return render_to_response('messages/inbox.html', {
        'msgs': msgs,
        }, 
        context_instance = RequestContext(request))


@login_required
def outbox(request):
    """Displays the outbox for the user making the request."""
    msgs = Message.objects.outbox(request.user)
    return render_to_response('messages/outbox.html', {
        'msgs': msgs,
        }, 
        context_instance = RequestContext(request))


@login_required
def trash(request):
    """Displays the trash for the user making the request."""
    msgs = Message.objects.trash(request.user)
    return render_to_response('messages/trash.html', {
        'msgs': msgs,
        }, 
        context_instance = RequestContext(request))


@login_required
def view(request, msg_id):
    """
    View a given message. Only the sender or receiver can see
    the message.
    """
    msg = get_object_or_404(Message, pk=msg_id)
    if msg.sender != request.user and msg.receiver != request.user:
        raise Http404

    if msg.receiver == request.user and msg.read_date is None:
        msg.read_date = datetime.datetime.now()
        msg.save()

    box = request.GET.get('box', None)

    return render_to_response('messages/view.html', {
        'box': box,
        'msg': msg,
        'is_deleted': msg.is_deleted(request.user),
        }, 
        context_instance = RequestContext(request))


@login_required
def reply(request, msg_id):
    """
    Process or prepare the compose form in order to reply
    to a given message.
    """
    msg = get_object_or_404(Message, pk=msg_id)

    if request.method == "POST":
        if request.POST.get('submit_button', 'Cancel') == 'Cancel':
            return box_redirect(request)
        compose_form = ComposeForm(request.user, request.POST)
        if compose_form.is_valid():
            compose_form.save(sender=request.user, parent_msg=msg)
            messages.success(request, 'Reply sent.')
            return box_redirect(request)
    else:
        if msg.receiver == request.user:
            receiver_name = msg.sender.username
        else:
            # replying to message in outbox
            receiver_name = msg.receiver.username

        form_data = {
            'receiver': receiver_name,
            'subject': reply_subject(msg.subject),
            'message': quote_message(msg.sender, msg.send_date, msg.message),
            'box': request.GET.get('box', 'inbox'),
        }

        compose_form = ComposeForm(request.user, initial=form_data)

    return render_to_response('messages/compose.html', {
        'compose_form': compose_form,
        }, 
        context_instance = RequestContext(request))


@login_required
def compose(request, receiver=None):
    """
    Process or prepare the compose form in order to create
    a new message.
    """
    if request.method == "POST":
        if request.POST.get('submit_button', 'Cancel') == 'Cancel':
            return HttpResponseRedirect(reverse('messages-inbox'))
        compose_form = ComposeForm(request.user, request.POST)
        if compose_form.is_valid():
            compose_form.save(sender=request.user)
            messages.success(request, 'Message sent.')
            return HttpResponseRedirect(reverse('messages-inbox'))
    else:
        if receiver is not None:
            form_data = {
                'receiver': receiver,
            }
            compose_form = ComposeForm(request.user, initial=form_data)
        else:
            compose_form = ComposeForm(request.user)

    return render_to_response('messages/compose.html', {
        'compose_form': compose_form,
        }, 
        context_instance = RequestContext(request))


@login_required
@require_POST
def delete(request, msg_id):
    """
    Deletes a given message. The user must be either the sender or
    receiver for this to succeed.
    """
    msg = get_object_or_404(Message, pk=msg_id)
    if msg.sender == request.user:
        msg.sender_delete_date = datetime.datetime.now()
    elif msg.receiver == request.user:
        msg.receiver_delete_date = datetime.datetime.now()
    else:
        raise Http404
    msg.save()
    messages.success(request, 'Message sent to trash.')

    return box_redirect(request)


@login_required
def delete_bulk(request):
    """
    Deletes messages in bulk. The message ID's to be deleted are expected
    to be in the delete POST array. The user must be either the sender
    or receiver for this to succeed.
    """
    if request.method == "POST":
        delete_ids = request.POST.getlist('delete_ids')
        try:
            delete_ids = [int(id) for id in delete_ids]
        except ValueError:
            raise Http404
        msgs = Message.objects.filter(id__in = delete_ids)
        now = datetime.datetime.now()
        for msg in msgs:
            if msg.sender == request.user:
                msg.sender_delete_date = now
                msg.save()
            elif msg.receiver == request.user:
                msg.receiver_delete_date = now
                msg.save()
        messages.success(request, 'Messages sent to the trash.')

    return box_redirect(request)


@login_required
@require_POST
def undelete(request, msg_id):
    """
    Undeletes a given message. The user must be either the sender or
    receiver for this to succeed.
    """
    msg = get_object_or_404(Message, pk=msg_id)
    if msg.sender == request.user:
        msg.sender_delete_date = None
    elif msg.receiver == request.user:
        msg.receiver_delete_date = None
    else:
        raise Http404
    msg.save()
    messages.success(request, 'Message retrieved from the trash.')

    return box_redirect(request)


@login_required
def undelete_bulk(request):
    """
    Undeletes messages in bulk. The message ID's to be deleted are expected
    to be in the delete POST array. The user must be either the sender
    or receiver for this to succeed.
    """
    if request.method == "POST":
        undelete_ids = request.POST.getlist('undelete_ids')
        try:
            undelete_ids = [int(id) for id in undelete_ids]
        except ValueError:
            raise Http404
        msgs = Message.objects.filter(id__in = undelete_ids)
        for msg in msgs:
            if msg.sender == request.user:
                msg.sender_delete_date = None
                msg.save()
            elif msg.receiver == request.user:
                msg.receiver_delete_date = None
                msg.save()
        messages.success(request, 'Messages retrieved from the trash.')

    return box_redirect(request)


@login_required
def options(request):
    """
    View to display/change user options.
    """
    if request.method == "POST":
        if request.POST.get('submit_button', 'Cancel') == 'Cancel':
            return HttpResponseRedirect(reverse('messages-inbox'))
        options = Options.objects.for_user(request.user)
        form = OptionsForm(request.POST, instance=options)
        if form.is_valid():
            form.save()
            messages.success(request, 'Options saved.')
            return HttpResponseRedirect(reverse('messages-inbox'))
    else:
        try:
            options = Options.objects.for_user(request.user)
        except:
            options = Options()
            options.user = request.user
            options.save()

        form = OptionsForm(instance=options)

    return render_to_response('messages/options.html', {
        'form': form,
        }, 
        context_instance = RequestContext(request))

