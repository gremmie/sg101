"""
Various useful widgets for the GPP application.
"""

from django import forms
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse


class AutoCompleteUserInput(forms.TextInput):
    class Media:
        css = {
            'all': ('js/jquery-autocomplete/jquery.autocomplete.css',)
        }
        js = (
            'js/jquery-autocomplete/lib/jquery.js',
            'js/jquery-autocomplete/lib/jquery.bgiframe.min.js',
            'js/jquery-autocomplete/lib/jquery.ajaxQueue.js',
            'js/jquery-autocomplete/jquery.autocomplete.js'
        )

    def render(self, name, value, attrs=None):
        url = reverse('messages-ajax_users')
        output = super(AutoCompleteUserInput, self).render(name, value, attrs)
        return output + mark_safe(u'''\
<script type="text/javascript">
jQuery("#id_%s").autocomplete("%s", {
    width: 150,
    max: 10,
    highlight: false,
    multiple: false,
    scroll: true,
    scrollHeight: 300,
    matchContains: true,
    autoFill: true,
});
</script>''' % (name, url))


# vim: ts=4 sw=4
