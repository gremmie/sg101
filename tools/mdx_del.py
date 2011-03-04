"""
A python-markdown extension to add support for <del>.
The Markdown syntax is --this is deleted text--.

"""
import markdown


DEL_RE = r'(--)(.*?)--'

class DelExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        del_tag = markdown.inlinepatterns.SimpleTagPattern(DEL_RE, 'del')
        md.inlinePatterns.add('del', del_tag, '>not_strong')


def makeExtension(configs=None):
    return DelExtension(configs)
