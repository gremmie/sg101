"""
This file contains the automatic admin site definitions for the comment models.
"""
from django.contrib import admin
from comments.models import Comment
from comments.models import CommentFlag

import ftfy

import bio.badges



class CommentAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['content_type', 'object_id']}),
        ('Content', {'fields': ['user', 'comment']}),
        ('Metadata', {'fields': ['ip_address', 'is_public', 'is_removed']}),
    ]
    list_display = ['__str__', 'content_type', 'object_id', 'ip_address',
            'creation_date', 'is_public', 'not_removed']
    list_filter = ['creation_date', 'is_public', 'is_removed']
    date_hierarchy = 'creation_date'
    ordering = ['-creation_date']
    search_fields = ['comment', 'user__username', 'ip_address']
    raw_id_fields = ['user', 'content_type']
    actions = ['fix_text']

    def fix_text(self, request, qs):
        for comment in qs:
            comment.comment = ftfy.fix_text(comment.comment)
            comment.save()

        count = len(qs)
        msg = "1 comment" if count == 1 else "%d comments" % count
        self.message_user(request, "Text fixed on {}".format(msg))

    fix_text.short_description = "Fix text on selected comments"


class CommentFlagAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'flag_date', 'get_comment_url')
    actions = ('accept_flags', )
    raw_id_fields = ('user', 'comment')

    def accept_flags(self, request, qs):
        """This admin action awards a security pin to the user who reported
        the comment and then deletes the flagged comment object.
        """
        for flag in qs:
            bio.badges.award_badge(bio.badges.SECURITY_PIN, flag.user)
            flag.delete()

    accept_flags.short_description = "Accept selected comment flags"


admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentFlag, CommentFlagAdmin)
