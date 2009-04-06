"""
Views for the bio application.
"""

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from bio.models import UserProfile
from bio.forms import UploadAvatarForm
from bio.forms import EditUserForm
from bio.forms import EditUserProfileForm
from core.paginator import DiggPaginator

#######################################################################

def get_profile(user):
    try:
        profile = user.get_profile()
    except:
        profile = UserProfile()
        profile.user = user
    return profile

#######################################################################

def member_list(request, type='user', page=1):
    if type == 'user':
        users = auth.models.User.objects.all().order_by('username')
    else:
        users = auth.models.User.objects.all().order_by('date_joined')

    paginator = DiggPaginator(users, 10, body=5, tail=3, margin=3, padding=2)
    try:
        the_page = paginator.page(int(page))
    except InvalidPage:
        raise Http404

    return render_to_response('bio/members.html', {
        'page': the_page,
        'type': type,
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def my_profile(request):
    profile = get_profile(request.user)

    return render_to_response('bio/view_profile.html', {
        'subject': request.user, 
        'profile': profile, 
        'hide_email': False,
        'this_is_me': True,
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def view_profile(request, username):

    user = get_object_or_404(auth.models.User, username = username)
    if user == request.user:
        return HttpResponseRedirect(reverse('bio.views.my_profile'))

    profile = get_profile(user)

    # work around MySQL's handling of Boolean
    hide_email = bool(profile.hide_email)
    
    return render_to_response('bio/view_profile.html', {
        'subject': user, 
        'profile': profile, 
        'hide_email': hide_email,
        'this_is_me': False,
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def edit_profile(request):
    if request.method == 'POST':
        if request.POST.get('submit_button', 'Cancel') == 'Cancel':
            return HttpResponseRedirect(reverse('bio.views.my_profile'))
        profile = get_profile(request.user)
        user_form = EditUserForm(request.POST, instance=request.user)
        profile_form = EditUserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
            return HttpResponseRedirect(reverse('bio.views.my_profile'))
    else:
        profile = get_profile(request.user)
        user_form = EditUserForm(instance=request.user)
        profile_form = EditUserProfileForm(instance=profile)

    return render_to_response('bio/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
         }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def change_avatar(request):
    if request.method == 'POST':
        form = UploadAvatarForm(request.POST, request.FILES)
        if form.is_valid():
            profile = get_profile(request.user)
            file = form.get_file()
            if profile.avatar.name != '':
                profile.avatar.delete(save=False)
            if file is not None:
                profile.avatar.save(form.get_filename(), file, save=False)
            profile.save()

            request.user.message_set.create(message='Avatar updated.')
            return HttpResponseRedirect(reverse('bio-me'))
    else:
        form = UploadAvatarForm()

    return render_to_response('bio/avatar.html', {
        'form': form,
         }, 
        context_instance = RequestContext(request))


# vim: ts=4 sw=4
