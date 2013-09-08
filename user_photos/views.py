"""Views for the user_photos application."""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from user_photos.forms import UploadForm


@login_required
def upload(request):
    """This view function receives an uploaded image file from a user.
    The photo will be resized if necessary and a thumbnail image will be
    created. The image and thumbnail will then be uploaded to the Amazon
    S3 service for storage.

    TODO: rate limiting
          pass off the processing to a celery task
          ajax version of this view

    """
    form = None
    uploads_enabled = settings.USER_PHOTO_ENABLED

    if uploads_enabled:
        if request.method == 'POST':
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                #TODO
                print "**************", request.FILES['image_file']
                pass
        else:
            form = UploadForm()

    return render(request, 'user_photos/upload_form.html', {
        'enabled': uploads_enabled,
        'form': form,
        },
        status=200 if uploads_enabled else 503)
