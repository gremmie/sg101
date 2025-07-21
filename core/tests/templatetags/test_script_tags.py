"""
Unit tests for the core script_tags.

"""
from django.template import Context, Template
from django.test import TestCase


class ScriptTagsTestCase(TestCase):
    TEMPLATE = Template(
        "{% load script_tags %}{% script_tags 'jquery jquery-ui markitup' %}")

    def test_script_tags(self):
        # Just making sure nothing blows up.
        self.TEMPLATE.render(Context({}))


class CssTagsTestCase(TestCase):
    TEMPLATE = Template(
        "{% load script_tags %}{% css_tags 'jquery-ui markitup' %}")

    def test_css_tags(self):
        # Just making sure nothing blows up.
        self.TEMPLATE.render(Context({}))


class JsTagsTestCase(TestCase):
    TEMPLATE = Template(
        "{% load script_tags %}{% js_tags 'jquery jquery-ui markitup tiny_mce' %}")

    def test_js_tags(self):
        # Just making sure nothing blows up.
        self.TEMPLATE.render(Context({}))
