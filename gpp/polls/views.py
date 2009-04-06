"""Views for the polls application"""

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from polls.models import Poll
from polls.models import Choice
from polls.forms import VoteForm

#######################################################################

def poll_index(request):
   current_polls = Poll.objects.get_current_polls()
   old_polls = Poll.objects.get_old_polls()
   return render_to_response('polls/index.html', {
      'current_polls': current_polls, 
      'old_polls': old_polls, 
      },
      context_instance = RequestContext(request))

#######################################################################

def poll_detail(request, poll_id):
   poll = get_object_or_404(Poll, pk = poll_id)
   if not poll.is_enabled:
      raise Http404

   return render_to_response('polls/poll.html', {
      'poll': poll, 
      },
      context_instance = RequestContext(request))

#######################################################################

@login_required
def poll_vote(request, poll_id):
   poll = get_object_or_404(Poll, pk = poll_id)
   if not poll.is_enabled:
      raise Http404
   if not poll.is_open():
      return HttpResponseRedirect(reverse('polls.views.poll_results', args=[poll_id]))

   if request.method == "POST":
      vote_form = VoteForm(poll, request.POST)
      if vote_form.is_valid():
         choice_id = request.POST.get('choices', None)
         choice = get_object_or_404(Choice, pk = choice_id)
         choice.votes += 1
         choice.save()
         return HttpResponseRedirect(reverse('polls.views.poll_results', args=[poll_id]))
   
   vote_form = VoteForm(poll)

   return render_to_response('polls/poll_vote.html', {
      'poll': poll, 
      'vote_form': vote_form,
      },
      context_instance = RequestContext(request))

#######################################################################

def poll_results(request, poll_id):
   poll = get_object_or_404(Poll, pk = poll_id)
   total_votes, choices = poll.results()
   return render_to_response('polls/poll_results.html', {
      'poll': poll, 
      'total_votes': total_votes,
      'choices': choices,
      },
      context_instance = RequestContext(request))

#######################################################################
