"""
Tests for legacy app functions.
"""

from django.test import TestCase

from legacy.phpbb import unphpbb
from legacy.html2md import MarkdownWriter

class UnPhpBbTest(TestCase):

    def test_unentities(self):
        s1 = "&quot;Look! No head!&quot; - Laika &amp; The Cosmonauts"
        s2 = unphpbb(s1)
        s3 = u'"Look! No head!" - Laika & The Cosmonauts'
        self.failUnlessEqual(s2, s3)

    def test_rem_uuid1(self):
        s1 = ("[url=http://www.thesurfites.com][color=black:3fdb565c83]"
                "T H E - S U R F I T E S[/color:3fdb565c83][/url]")
        s2 = unphpbb(s1)
        s3 = (u'[url=http://www.thesurfites.com][color=black]'
                'T H E - S U R F I T E S[/color][/url]')
        self.failUnlessEqual(s2, s3)


class Html2MdTest(TestCase):

    def test_sig1(self):
        s1 = """<p><a href="http://surfguitar101.com/modules.php?name=Web_Links&amp;l_op=visit&amp;lid=50">Pollo Del Mar</a><br />
<a href="http://tinyurl.com/yjfmspj">Frankie &amp; The Pool Boys</a><br />
<a href="http://tinyurl.com/cnr27t">PDM on FaceBook</a><br />
</p>"""
        md_writer = MarkdownWriter()
        md_writer.feed(s1)
        s2 = md_writer.markdown()
        s3 = u'[Pollo Del Mar](http://surfguitar101.com/modules.php?name=Web_Links&l_op=visit&lid=50)  \n\n[Frankie & The Pool Boys](http://tinyurl.com/yjfmspj)  \n\n[PDM on FaceBook](http://tinyurl.com/cnr27t)  \n\n'
        self.failUnlessEqual(s2, s3)
