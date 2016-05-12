"""
Views for the polls application.

"""
import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST
from django.db.models import F

from polls.models import Poll
from polls.models import Choice
from polls.forms import VoteForm

#######################################################################

def get_user_choice(user, poll):
    """
    Return the Choice object the given user voted for from the given poll,
    or None if no vote has been recorded (or the user is not authenticated.

    """
    user_choice = None
    if user.is_authenticated():
        user_choices = user.choice_set.filter(poll=poll)
        if user_choices:
            user_choice = user_choices[0]

    return user_choice

#######################################################################

def poll_index(request):

    # Do some stuff manually to avoid cascading hits to the database
    now = datetime.datetime.now()
    qs = Poll.objects.filter(is_enabled=True)
    poll_dict = {}
    current_polls = []
    old_polls = []
    for poll in qs:
        poll.total_votes_ = 0
        poll_dict[poll.pk] = poll
        if (poll.start_date <= now and
                (poll.end_date is None or poll.end_date >= now)):
            current_polls.append(poll)
        elif (poll.start_date < now and
                (poll.end_date is not None and poll.end_date < now)):
            old_polls.append(poll)

    for choice in Choice.objects.iterator():
        poll = poll_dict.get(choice.poll_id)
        if poll:
            poll.total_votes_ += choice.votes

    return render(request, 'polls/index.html', {
        'current_polls': current_polls,
        'old_polls': old_polls,
        'V3_DESIGN': True,
        })

#######################################################################

def poll_detail(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if not poll.is_enabled or poll.start_date > datetime.datetime.now():
        raise Http404

    total_votes, choices = poll.results()

    return render(request, 'polls/poll_detail.html', {
        'poll': poll,
        'total_votes': total_votes,
        'choices': choices,
        'user_choice': get_user_choice(request.user, poll),
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def poll_vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if not poll.is_enabled:
        raise Http404
    if not poll.is_open():
        return HttpResponseRedirect(reverse('polls-detail',
                                            kwargs={'poll_id': poll_id}))

    user_choice = get_user_choice(request.user, poll)

    if request.method == "POST":
        vote_form = VoteForm(poll, request.POST, user=request.user,
                             user_choice=user_choice)
        if vote_form.is_valid():
            vote_form.save()
            return HttpResponseRedirect(reverse('polls-detail',
                                                kwargs={'poll_id': poll_id}))
    else:
        vote_form = VoteForm(poll)

    return render(request, 'polls/poll_vote.html', {
        'poll': poll,
        'vote_form': vote_form,
        'user_choice': user_choice,
        'V3_DESIGN': True,
        })

#######################################################################

@require_POST
@login_required
def poll_delete_vote(request):
    poll = get_object_or_404(Poll, pk=request.POST.get('poll_id'))
    user_choice = get_user_choice(request.user, poll)
    if user_choice:
        Choice.objects.filter(id=user_choice.id).update(votes=F('votes') - 1)
        user_choice.voters.remove(request.user)

    return HttpResponseRedirect(reverse('polls-detail', kwargs={'poll_id': poll.id}))
