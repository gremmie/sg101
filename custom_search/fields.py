"""Custom Haystack SearchFields."""

import haystack.fields


class MaxTermSizeCharField(haystack.fields.CharField):
    """A CharField that discards large terms when preparing the search index.

    Some backends (e.g. Xapian) throw errors when terms are bigger than some
    limit. This field omits the terms over a limit when preparing the data for
    the search index.

    The keyword argument max_term_size sets the maximum size of a whitespace
    delimited word/term. Terms over this size are not indexed. The default value
    is 64.
    """
    DEFAULT_MAX_TERM_SIZE = 64

    def __init__(self, *args, **kwargs):
        self.max_term_size = kwargs.pop('max_term_size', self.DEFAULT_MAX_TERM_SIZE)
        super(MaxTermSizeCharField, self).__init__(*args, **kwargs)

    def prepare(self, obj):
        text = super(MaxTermSizeCharField, self).prepare(obj)
        if text is None or self.max_term_size is None:
            return text

        terms = (term for term in text.split() if len(term) <= self.max_term_size)
        return u' '.join(terms)
