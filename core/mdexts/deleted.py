"""
A python-markdown extension to add support for <del>.
The Markdown syntax is ---this is deleted text---.

"""
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor


DEL_RE = r'(---)(.*?)---'

# Where the pattern runs in the inline pass. Markdown ships `not_strong` at 70
# and `em_strong` at 60, so 65 is the slot the pre-3.0 registration named as
# '>not_strong'.
#
# The band that matters is wider than that one number, and was measured against
# real posts rather than reasoned from the priority list: anything in 61..119
# renders the archive identically. Above `autolink` (120) the pattern strikes
# through URLs that contain two runs of three hyphens and corrupts their href;
# at or below `em_strong` (60) the emphasis processors claim the hyphens first.
DEL_PRIORITY = 65


class DelExtension(Extension):
    """An extension that adds ---struck text--- to Markdown."""

    def extendMarkdown(self, md):
        md.inlinePatterns.register(SimpleTagInlineProcessor(DEL_RE, 'del'),
                                   'del', DEL_PRIORITY)


def makeExtension(**kwargs):
    return DelExtension(**kwargs)
