"""
This file contains various helper utility functions for the messages
application.

"""


def reply_subject(subject):
    """
    Builds a subject line for a reply.
    If the subject already starts with Re: then return the subject.
    Otherwise, prepend Re: to the subject and return it.
    """
    if subject.startswith('Re: '):
        return subject
    return 'Re: ' + subject
