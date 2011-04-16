"""
This file contains various helper utility functions for the messages
application.
"""

from django.utils.text import wrap


def reply_subject(subject):
   """
   Builds a subject line for a reply.
   If the subject already starts with Re: then return the subject.
   Otherwise, prepend Re: to the subject and return it.
   """
   if subject.startswith('Re: '):
      return subject
   return 'Re: ' + subject


def quote_message(who, date, message):
   """
   Builds a message reply by quoting the existing message in a
   typical email-like fashion. The quoting is compatible with Markdown.
   """
   header = '> On %s, %s wrote:\n>\n' % (date.strftime('%a, %b %d %Y, %I:%M %p'), who)
   lines = wrap(message, 55).split('\n')
   for i, line in enumerate(lines):
      lines[i] = '> ' + line
   return header + '\n'.join(lines) + '\n\n'
