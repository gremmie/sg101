"""
Views for the bio application.

"""
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseServerError
from django.http import Http404
from django.core.paginator import InvalidPage
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from elsewhere.models import SocialNetworkForm
from elsewhere.models import InstantMessengerForm
from elsewhere.models import WebsiteForm

from bio.models import UserProfile
from bio.models import UserProfileFlag
from bio.models import BadgeOwnership
from bio.forms import UploadAvatarForm
from bio.forms import EditUserForm
from bio.forms import EditUserProfileForm
from bio.forms import SearchUsersForm
from bio.signals import notify_profile_content_update
from core.paginator import DiggPaginator
from core.functions import email_admins
from core.functions import get_page

#######################################################################

@login_required
def member_list(request, type='user'):
    """
    This view displays the member list. Only active members are displayed.
    """
    qs = User.objects.filter(is_active=True).select_related('profile')
    if type == 'user':
        qs = qs.order_by('username')
    else:
        qs = qs.order_by('date_joined')
    num_members = qs.count()

    paginator = DiggPaginator(qs, 20, body=5, tail=3, margin=3, padding=2)
    page = get_page(request.GET)
    try:
        the_page = paginator.page(page)
    except InvalidPage:
        raise Http404

    return render(request, 'bio/members.html', {
        'page': the_page,
        'type': type,
        'num_members': num_members,
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def my_profile(request):
    profile = request.user.profile
    badge_collection = BadgeOwnership.objects.filter(
            profile=profile).select_related("badge")

    return render(request, 'bio/view_profile.html', {
        'subject': request.user,
        'profile': profile,
        'hide_email': False,
        'this_is_me': True,
        'badge_collection': badge_collection,
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def view_profile(request, username):

    user = get_object_or_404(User.objects.select_related('profile'),
            username__iexact=username)
    if user == request.user:
        return redirect('bio-me')

    profile = user.profile
    hide_email = profile.hide_email

    badge_collection = BadgeOwnership.objects.filter(
            profile=profile).select_related("badge")

    return render(request, 'bio/view_profile.html', {
        'subject': user,
        'profile': profile,
        'hide_email': hide_email,
        'this_is_me': False,
        'badge_collection': badge_collection,
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def edit_profile(request):
    if request.method == 'POST':
        profile = request.user.profile
        user_form = EditUserForm(request.POST, instance=request.user)
        profile_form = EditUserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('bio-me')
    else:
        profile = request.user.profile
        user_form = EditUserForm(instance=request.user)
        profile_form = EditUserProfileForm(instance=profile)

    return render(request, 'bio/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'V3_DESIGN': True,
         })

#######################################################################

@login_required
def change_avatar(request):
    if request.method == 'POST':
        form = UploadAvatarForm(request.POST, request.FILES)
        if form.is_valid():
            # Update the profile with the new avatar
            profile = request.user.profile

            # First delete any old avatar file
            if profile.avatar.name != '':
                profile.avatar.delete(save=False)

            try:
                name, avatar = form.save()
            except IOError:
                messages.error(request, 'A file error occurred.')
                return redirect('bio-me')

            if avatar is not None:
                profile.avatar.save(name, avatar, save=False)
            profile.save()

            messages.success(request, 'Avatar updated')
            return redirect('bio-me')
    else:
        form = UploadAvatarForm()

    return render(request, 'bio/avatar.html', {
        'form': form,
        'V3_DESIGN': True,
         })

#######################################################################

@require_POST
def flag_profile(request, profile_id):
    """
    This function handles the flagging of profiles by users. This function should
    be the target of an AJAX post.
    """
    if not request.user.is_authenticated:
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
    return HttpResponse('The profile was flagged. A moderator will review the'
        ' profile shortly. Thanks for helping to improve the content on this '
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
                return redirect(request.path)

        # Delete forms
        elif new_data.get('delete-sn-form') or new_data.get('delete-im-form') or new_data.get('delete-w-form'):
            delete_id = request.POST['delete_id']

            update_occurred = True
            if new_data.get('delete-sn-form'):
                request.user.social_network_profiles.get(id=delete_id).delete()
            elif new_data.get('delete-im-form'):
                request.user.instant_messenger_profiles.get(id=delete_id).delete()
            elif new_data.get('delete-w-form'):
                request.user.website_profiles.get(id=delete_id).delete()
            else:
                update_occurred = False

            if update_occurred:
                notify_profile_content_update(request.user.profile)

            return redirect(request.path)

        # WTF?
        else:
            return HttpResponseServerError

    else:
        # Create blank forms
        sn_form = SocialNetworkForm()
        im_form = InstantMessengerForm(auto_id=im_id)
        w_form = WebsiteForm()

    return render(request, 'bio/edit_elsewhere.html', {
        'sn_form': sn_form,
        'im_form': im_form,
        'w_form': w_form,
        'V3_DESIGN': True,
        })

#######################################################################

@login_required
def member_search(request):
    data = request.GET if request.GET else None
    form = SearchUsersForm(data)
    if form.is_valid():
        username = form.cleaned_data['username']
        return redirect('bio-view_profile', username=username)

    return render(request, 'bio/member_search.html', {
        'form': form,
        'V3_DESIGN': True,
    })
