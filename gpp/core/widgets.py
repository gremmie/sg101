"""
Various useful widgets for the GPP application.
"""

from django import forms
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings


class AutoCompleteUserInput(forms.TextInput):
    class Media:
        css = {
            'all': settings.GPP_THIRD_PARTY_CSS['jquery-autocomplete'],
        }
        js = settings.GPP_THIRD_PARTY_JS['jquery-autocomplete']

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
