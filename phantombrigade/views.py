"""
Views for the phantombrigade application.

The phantombrigade application doesn't have anything to do with SG101. It is
simply some useful web services that we provide to the gaming clan Phantom
Brigade. Rather than create a whole new website we just use the infrastructure
of SG101.

Current we provide a TeamSpeak 3 status view for the PhantomBrigade.us website.

"""
import json

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseServerError
import ts3


CACHE_KEY = 'phantombrigade-ts3-json'
CACHE_TIMEOUT = 2 * 60


def ts3_query(request):
    """
    Query the TeamSpeak3 server for status, and output a JSON representation.

    The JSON we return is targeted towards the jQuery plugin Dynatree
    http://code.google.com/p/dynatree/

    """
    # Do we have the result cached?
    result = cache.get(CACHE_KEY)
    if result:
        return HttpResponse(result, content_type='application/json')

    # Cache miss, go query the remote server

    try:
        svr = ts3.TS3Server(settings.PB_TS3_IP, settings.PB_TS3_PORT,
                settings.PB_TS3_VID)
    except ts3.ConnectionError:
        return HttpResponseServerError()

    response = svr.send_command('serverinfo')
    if response.response.get('msg') != 'ok':
        return HttpResponseServerError()
    svr_info = response.data[0]

    response = svr.send_command('channellist')
    if response.response.get('msg') != 'ok':
        return HttpResponseServerError()
    channel_list = response.data

    response = svr.send_command('clientlist')
    if response.response.get('msg') != 'ok':
        return HttpResponseServerError()
    client_list = response.data

    # Start building the channel / client tree.
    # We save tree nodes in a dictionary, keyed by their id so we can find them
    # later in order to support arbitrary channel hierarchies.
    channels = {}

    # Build the root, or channel 0
    channels[0] = {
        'title': svr_info['virtualserver_name'],
        'isFolder': True,
        'expand': True,
        'children': []
    }

    # Add the channels to our tree

    for channel in channel_list:
        node = {
            'title': channel['channel_name'],
            'isFolder': True,
            'expand': True,
            'children': []
        }
        parent = channels[int(channel['pid'])]
        parent['children'].append(node)
        channels[int(channel['cid'])] = node

    # Add the clients to the tree

    for client in client_list:
        if client['client_type'] == '0':
            node = {
                'title': client['client_nickname'],
                'icon': 'client.png'
            }
            channel = channels[int(client['cid'])]
            channel['children'].append(node)

    tree = [channels[0]]
    status = json.dumps(tree)

    cache.set(CACHE_KEY, status, CACHE_TIMEOUT)

    return HttpResponse(status, content_type='application/json')
