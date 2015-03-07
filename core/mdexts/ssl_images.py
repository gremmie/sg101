"""
A python-markdown extension to turn <img> tags with http: source attributes into
<a> tags.
"""
from urlparse import urlparse

import markdown


class SslImagesTreeprocessor(markdown.treeprocessors.Treeprocessor):

    def run(self, root):
        for node in root.iter('img'):
            src = node.get('src')
            if src:
                url = urlparse(src)
                if url.scheme == 'http':
                    node.clear()
                    node.tag = 'a'
                    node.text = 'Click for image'
                    node.set('href', url.geturl())


class SslImagesExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        tree_proc = SslImagesTreeprocessor()
        md.treeprocessors.add('ssl_images', tree_proc, '>inline')
