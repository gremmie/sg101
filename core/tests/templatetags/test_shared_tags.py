"""
The header's and sidebar's tags render their V3 templates on any page.

Each tag loads one template, so a page needs to set nothing in its context to
get the markup that matches `v3/base.html`.
"""
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import TestCase


class SharedTagsTestCase(TestCase):

    TAGS = [
        ('contest_tags', 'latest_contests_block',
         'contests/v3/latest_contests_block_tag.html'),
        ('core_tags', 'birthday_block', 'core/v3/birthday_block.html'),
        ('countdown_tags', 'countdown_events', 'countdown/v3/countdown_tag.html'),
        ('donations_tags', 'monthly_goal', 'donations/v3/monthly_goal_tag.html'),
        ('messages_tags', 'unread_messages',
         'messages/v3/unread_messages_tag.html'),
        ('poll_tags', 'latest_poll_block', 'polls/v3/latest_poll_block_tag.html'),
        ('potd_tags', 'photo_of_the_day', 'potd/v3/potd_block.html'),
    ]

    def test_each_tag_renders_its_v3_template(self):
        for library, tag, template_name in self.TAGS:
            with self.subTest(tag=tag):
                template = Template('{%% load %s %%}{%% %s %%}' % (library, tag))
                with self.assertTemplateUsed(template_name):
                    template.render(Context({'user': AnonymousUser()}))
