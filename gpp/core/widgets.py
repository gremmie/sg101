"""
Various useful widgets for the GPP application.
"""

from django import forms
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings


class AutoCompleteUserInput(forms.TextInput):

    def render(self, name, value, attrs=None):
        url = reverse('core-ajax_users')
        output = super(AutoCompleteUserInput, self).render(name, value, attrs)
        return output + mark_safe(u"""\
<script type="text/javascript">
$(function() {
    var cache = {};
    var cacheSize = 0;
    $("#id_%s").autocomplete({
        delay: 400,
        minLength: 2,
        source: function(request, response) {
            if (cache[request.term]) {
               response(cache[request.term]);
               return;
            }
            $.ajax({
                url: "%s",
                type: "GET",
                data: {
                    q: request.term,
                    limit: 10
                },
                dataType: "json",
                success: function(data, textStatus) {
                    if (cacheSize >= 16) {
                       cache = {};
                       cacheSize = 0;
                    }
                    cache[request.term] = data;
                    ++cacheSize;
                    response(data);
                },
                error: function(xhr, textStatus, ex) {
                    alert('Oops, an error occurred. ' + xhr.statusText + ' - ' +
                      xhr.responseText);
                }
            });
        }
    });
});
</script>""" % (name, url))

