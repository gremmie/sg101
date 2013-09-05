"""
Views for the comments application.

"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.db.models import get_model
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.html import escape
from django.views.decorators.http import require_POST

from core.functions import email_admins
from core.markup import site_markup
from comments.forms import CommentForm
from comments.models import Comment
from comments.models import CommentFlag
import antispam
import antispam.utils


@login_required
@require_POST
def post_comment(request):
    """
    This function handles the posting of comments. If successful, returns
    the comment text as the response. This function is meant to be the target
    of an AJAX post.
    """
    # Look up the object we're trying to comment about
    ctype = request.POST.get('content_type', None)
    object_pk = request.POST.get('object_pk', None)
    if ctype is None or object_pk is None:
        return HttpResponseBadRequest('Missing content_type or object_pk field.')

    try:
        model = get_model(*ctype.split('.', 1))
        target = model.objects.get(pk=object_pk)
    except TypeError:
        return HttpResponseBadRequest(
            "Invalid content_type value: %r" % escape(ctype))
    except AttributeError:
        return HttpResponseBadRequest(
            "The given content-type %r does not resolve to a valid model." % \
                escape(ctype))
    except ObjectDoesNotExist:
        return HttpResponseBadRequest(
            "No object matching content-type %r and object PK %r exists." % \
                (escape(ctype), escape(object_pk)))

    # Can we comment on the target object?
    if hasattr(target, 'can_comment_on'):
        if callable(target.can_comment_on):
            can_comment_on = target.can_comment_on()
        else:
            can_comment_on = target.can_comment_on
    else:
        can_comment_on = True

    if not can_comment_on:
        return HttpResponseForbidden('Cannot comment on this item.')

    # Check form validity

    form = CommentForm(target, request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('Invalid comment; missing parameters?')

    comment = form.get_comment_object(request.user, request.META.get("REMOTE_ADDR", None))

    # Check for spam

    if antispam.utils.spam_check(request, comment.comment):
        return HttpResponseForbidden(antispam.BUSTED_MESSAGE)

    comment.save()

    # return the rendered comment
    return render_to_response('comments/comment.html', {
        'comment': comment,
        },
        context_instance = RequestContext(request))


@require_POST
def flag_comment(request):
    """
    This function handles the flagging of comments by users. This function should
    be the target of an AJAX post.
    """
    if not request.user.is_authenticated():
        return HttpResponse('Please login or register to flag a comment.')

    id = request.POST.get('id', None)
    if id is None:
        return HttpResponseBadRequest('No id')

    try:
        comment = Comment.objects.get(pk=id)
    except Comment.DoesNotExist:
        return HttpResponseBadRequest('No comment with id %s' % id)

    flag = CommentFlag(user=request.user, comment=comment)
    flag.save()
    email_admins('A Comment Has Been Flagged', """Hello,

A user has flagged a comment for review.
""")
    return HttpResponse('The comment was flagged. A moderator will review the comment shortly. ' \
            'Thanks for helping to improve the discussions on this site.')


@require_POST
def markdown_preview(request):
    """
    This function should be the target of an AJAX POST. It takes the 'data' parameter
    from the POST parameters and returns a rendered HTML page from the data, which
    is assumed to be in markdown format. The HTML page is suitable for the preview
    function for a javascript editor such as markItUp.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden('This service is only available to logged in users.')

    data = request.POST.get('data', None)
    if data is None:
        return HttpResponseBadRequest('No data')

    return render_to_response('comments/markdown_preview.html', {
        'data': site_markup(data),
        },
        context_instance = RequestContext(request))
