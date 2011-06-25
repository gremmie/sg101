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
    current_polls = Poll.objects.get_current_polls()
    old_polls = Poll.objects.get_old_polls()
    return render(request, 'polls/index.html', {
        'current_polls': current_polls,
        'old_polls': old_polls,
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
