"""
This module contains decorators for the antispam application.

"""
from datetime import timedelta
from functools import wraps

from django.shortcuts import render

from antispam.rate_limit import RateLimiter, RateLimiterUnavailable


def rate_limit(count=10, interval=timedelta(minutes=1),
        lockout=timedelta(hours=8)):

    def decorator(fn):

        @wraps(fn)
        def wrapped(request, *args, **kwargs):

            ip = request.META.get('REMOTE_ADDR')
            try:
                rate_limiter = RateLimiter(ip, count, interval, lockout)
                if rate_limiter.is_blocked():
                    return render(request, 'antispam/blocked.html', status=403)

            except RateLimiterUnavailable:
                # just call the function and return the result
                return fn(request, *args, **kwargs)

            response = fn(request, *args, **kwargs)

            if request.method == 'POST':
                success = (response and response.has_header('location') and
                        response.status_code == 302)
                try:
                    if not success and rate_limiter.incr():
                        return render(request, 'antispam/blocked.html', status=403)

                except RateLimiterUnavailable:
                    pass

            return response

        return wrapped
    return decorator
