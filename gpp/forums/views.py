"""
Views for the forums application.
"""
from django.shortcuts import render_to_response
from django.template import RequestContext

from forums.models import Forum


def index(request):
    forums = Forum.objects.all().select_related()
    cats = {}
    for forum in forums:
        cat = cats.setdefault(forum.category.id, {
            'cat': forum.category,
            'forums': [],
            })
        cat['forums'].append(forum)

    cmpdef = lambda a, b: cmp(a['cat'].position, b['cat'].position)
    cats = sorted(cats.values(), cmpdef)

    return render_to_response('forums/index.html', {
        'cats': cats,
        },
        context_instance=RequestContext(request))

def forum_index(request, slug):
    pass
