"""
Views for the contests application.

"""
import json

from django.http import (HttpResponse, HttpResponseForbidden,
        HttpResponseBadRequest)
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from contests.models import Contest


class ContestListView(ListView):
    context_object_name = 'contests'
    queryset=Contest.public_objects.all()

    def get_context_data(self, **kwargs):
        context = super(ContestListView, self).get_context_data(**kwargs)
        context['V3_DESIGN'] = True
        return context


class ContestDetailView(DetailView):
    context_object_name = 'contest'
    queryset=Contest.public_objects.all().prefetch_related('winners')

    def get_context_data(self, **kwargs):
        context = super(ContestDetailView, self).get_context_data(**kwargs)
        context['V3_DESIGN'] = True
        return context


@require_POST
def enter(request):
    """
    This view is an AJAX view that is used to enter or withdraw a user from a
    given contest. This function toggles the user's entered state in the
    contest.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden("Please login first")

    contest_id = request.POST.get('contest_id')
    if not contest_id:
        return HttpResponseBadRequest("Missing contest_id")

    contest = get_object_or_404(Contest, pk=contest_id)
    if not contest.can_enter():
        return HttpResponseForbidden("Contest is over")

    # Toggle the user's state in the contest

    result = {}
    if request.user in contest.contestants.all():
        contest.contestants.remove(request.user)
        result['entered'] = False
        result['msg'] = 'You have been withdrawn from this contest.'
    else:
        contest.contestants.add(request.user)
        result['entered'] = True
        result['msg'] = 'You have been entered into this contest!'

    json_result = json.dumps(result)
    return HttpResponse(json_result, content_type='application/json')
