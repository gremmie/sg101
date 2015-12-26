"""Views for the antispam application."""

from django.shortcuts import render


def suspended(request):
    """This view checks the user's status for suspension and displays an
    appropriate message.
    """
    is_active = request.user.is_active

    return render(request, 'antispam/suspended.html', {
        'is_active': is_active,
        })
