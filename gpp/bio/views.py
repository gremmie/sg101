"""
Views for the bio application.
"""

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.contrib import auth
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.core.paginator import InvalidPage
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from elsewhere.models import SocialNetworkForm
from elsewhere.models import InstantMessengerForm
from elsewhere.models import WebsiteForm

from bio.models import UserProfile
from bio.models import UserProfileFlag
from bio.forms import UploadAvatarForm
from bio.forms import EditUserForm
from bio.forms import EditUserProfileForm
from core.paginator import DiggPaginator
from core.functions import email_admins

#######################################################################

@login_required
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

    # Attach user profiles to each post to avoid using get_user_profile() in
    # the template.
    users = set(user.id for user in the_page.object_list)

    profiles = UserProfile.objects.filter(user__id__in=users).select_related()
    user_profiles = dict((profile.user.id, profile) for profile in profiles)

    for user in the_page.object_list:
        user.user_profile = user_profiles[user.id]

    return render_to_response('bio/members.html', {
        'page': the_page,
        'type': type,
        }, 
        context_instance = RequestContext(request))

#######################################################################

@login_required
def my_profile(request):
    profile = request.user.get_profile()

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

    profile = user.get_profile()

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
        profile = request.user.get_profile()
        user_form = EditUserForm(request.POST, instance=request.user)
        profile_form = EditUserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
            return HttpResponseRedirect(reverse('bio.views.my_profile'))
    else:
        profile = request.user.get_profile()
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
            profile = request.user.get_profile()
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

#######################################################################

@require_POST
def flag_profile(request, profile_id):
    """
    This function handles the flagging of profiles by users. This function should
    be the target of an AJAX post.
    """
    if not request.user.is_authenticated():
        return HttpResponse('Please login or register to flag a profile.')

    try:
        profile = UserProfile.objects.get(pk=profile_id)
    except UserProfile.DoesNotExist:
        return HttpResponseBadRequest("That profile doesn't exist.")

    flag = UserProfileFlag(user=request.user, profile=profile)
    flag.save()
    email_admins('A Profile Has Been Flagged', """Hello,

A user has flagged a profile for review.
""")
    return HttpResponse('The profile was flagged. A moderator will review the' \
        ' profile shortly. Thanks for helping to improve the content on this ' \
        'site.')

#######################################################################

@login_required
def edit_elsewhere(request):
    im_id = 'id_im_%s'  # to prevent duplicate ID in HTML output
    if request.method == 'POST':
        new_data = request.POST.copy()

        # Add forms
        if new_data.get('sn-form') or new_data.get('im-form') or new_data.get('w-form'):

            if new_data.get('sn-form'):
                sn_form = SocialNetworkForm(new_data)
                im_form = InstantMessengerForm(auto_id=im_id)
                w_form = WebsiteForm()
                form = sn_form
            elif new_data.get('im-form'):
                sn_form = SocialNetworkForm()
                im_form = InstantMessengerForm(new_data, auto_id=im_id)
                w_form = WebsiteForm()
                form = im_form
            elif new_data.get('w-form'):
                sn_form = SocialNetworkForm()
                im_form = InstantMessengerForm(auto_id=im_id)
                w_form = WebsiteForm(new_data)
                form = w_form

            if form.is_valid():
                profile = form.save(commit=False)
                profile.user = request.user
                profile.save()
                return HttpResponseRedirect(request.path)

        # Delete forms
        elif new_data.get('delete-sn-form') or new_data.get('delete-im-form') or new_data.get('delete-w-form'):
            delete_id = request.POST['delete_id']

            if new_data.get('delete-sn-form'):
                request.user.social_network_profiles.get(id=delete_id).delete()
            elif new_data.get('delete-im-form'):
                request.user.instant_messenger_profiles.get(id=delete_id).delete()
            elif new_data.get('delete-w-form'):
                request.user.website_profiles.get(id=delete_id).delete()

            return HttpResponseRedirect(request.path)

        # WTF?
        else:
            return HttpResponseServerError

    else:
        # Create blank forms
        sn_form = SocialNetworkForm()
        im_form = InstantMessengerForm(auto_id=im_id)
        w_form = WebsiteForm()

    return render_to_response('bio/edit_elsewhere.html', {
        'sn_form': sn_form, 
        'im_form': im_form, 
        'w_form': w_form,
        }, 
        context_instance=RequestContext(request))

