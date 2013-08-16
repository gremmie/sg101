"""
This module contains decorators for the antispam application.

"""
from datetime import timedelta
import json
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

                # Figure out if the view succeeded; if it is a non-ajax view,
                # then success means a redirect is about to occur. If it is
                # an ajax view, we have to decode the json response.
                success = False
                if not request.is_ajax():
                    success = (response and response.has_header('location') and
                            response.status_code == 302)
                elif response:
                    json_resp = json.loads(response.content)
                    success = json_resp['success']

                if not success:
                    try:
                        blocked = rate_limiter.incr()
                    except RateLimiterUnavailable:
                        blocked = False

                    if blocked:
                        return render(request, 'antispam/blocked.html', status=403)

            return response

        return wrapped
    return decorator
