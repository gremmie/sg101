"""Views for the user_photos application."""
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponse, HttpResponseForbidden,
    HttpResponseNotAllowed)
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib import messages

from user_photos.forms import UploadForm
from user_photos.models import Photo
from user_photos.s3 import delete_photos


@login_required
def upload(request):
    """This view function receives an uploaded image file from a user.
    The photo will be resized if necessary and a thumbnail image will be
    created. The image and thumbnail will then be uploaded to the Amazon
    S3 service for storage.

    """
    form = None
    uploads_enabled = settings.USER_PHOTOS_ENABLED

    if uploads_enabled:
        if request.method == 'POST':
            form = UploadForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                photo = form.save()
                return redirect(photo)
        else:
            form = UploadForm(user=request.user)

    return render(request, 'user_photos/upload_form.html', {
        'enabled': uploads_enabled,
        'form': form,
        },
        status=200 if uploads_enabled else 503)


def upload_ajax(request):
    """This view is the ajax version of the upload function, above.

    We return a JSON object response to the client with the following name
    & value pairs:
            'success' : false for failure and true for success
            'msg' : string error message if success is false
            'url' : the image URL as a string if success

    If a non-200 status code is returned the response will simply be a text
    string error message.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden
    if not request.is_ajax() or request.method != 'POST':
        return HttpResponseNotAllowed

    ret = {'success': False, 'msg': '', 'url': ''}
    if settings.USER_PHOTOS_ENABLED:
        form = UploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            photo = form.save()
            ret['success'] = True
            ret['url'] = photo.url
        else:
            # gather form error messages
            errors = []
            non_field_errors = form.non_field_errors().as_text()
            if non_field_errors:
                errors.append(non_field_errors)
            for field_errors in form.errors.values():
                errors.append(field_errors.as_text())
            ret['msg'] = '\n'.join(errors)
    else:
        ret['msg'] = 'Photo uploads are temporarily disabled'

    return HttpResponse(json.dumps(ret), content_type='application/json')


class GalleryView(ListView):
    """A ListView for displaying a user's photos"""

    template_name = 'user_photos/gallery.html'
    context_object_name = 'photos'
    paginate_by = 50
    allow_empty = True

    def get_queryset(self):
        self.gallery_owner = get_object_or_404(get_user_model(),
                                    username=self.kwargs['username'])
        return Photo.objects.filter(user=self.gallery_owner).order_by('-upload_date')

    def get_context_data(self, **kwargs):
        context = super(GalleryView, self).get_context_data(**kwargs)
        context['gallery_owner'] = self.gallery_owner
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(GalleryView, self).dispatch(*args, **kwargs)


@login_required
@require_POST
def delete(request):
    """A view function to allow a user to delete their own photos."""

    ret_view, username = 'user_photos-gallery', request.user.username

    if not settings.USER_PHOTOS_ENABLED:
        messages.error(request, "This function is disabled temporarily")
        return redirect(ret_view, username)

    photo_ids = []
    for photo_id in request.POST.getlist('photo_id'):
        try:
            n = int(photo_id)
        except ValueError:
            continue
        photo_ids.append(n)

    count = 0
    if photo_ids:
        qs = Photo.objects.filter(user=request.user, pk__in=photo_ids)
        count = len(qs)
        if count:
            delete_photos(qs)
            qs.delete()

    msg = "{} photo{} deleted".format(count, '' if count == 1 else 's')
    messages.add_message(request,
            messages.SUCCESS if count > 0 else messages.WARNING,
            msg)

    return redirect(ret_view, username)
