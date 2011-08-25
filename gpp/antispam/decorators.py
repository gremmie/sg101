"""
This module contains decorators for the antispam application.

"""
from datetime import timedelta
from functools import wraps

from django.shortcuts import render

from antispam.rate_limit import rate_check


def rate_limit(count=10, interval=timedelta(minutes=1),
        lockout=timedelta(hours=8)):

    def decorator(fn):

        @wraps(fn)
        def wrapped(request, *args, **kwargs):

            response = fn(request, *args, **kwargs)

            if request.method == 'POST':
                success = (response and response.has_header('location') and
                        response.status_code == 302)
                if not success:
                    ip = request.META.get('REMOTE_ADDR')
                    if rate_check(ip, count, interval, lockout):
                        return render(request, 'antispam/blocked.html', status=403)

            return response

        return wrapped
    return decorator
