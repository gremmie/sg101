"""
Template tags for our Comments application.
We support the following template tags:
    {% get_comment_count for [object] as [var] %}
    {% get_comment_list for [object] as [var] %}`
    {% get_comment_form for [object] as [var] %}`
    {% render_comment_form for [object] %}
    {% render_comment_list [object] %}
"""
from django import template
from django.template.loader import render_to_string

from comments.models import Comment
from comments.forms import CommentForm


register = template.Library()


class GetCommentCountNode(template.Node):
    def __init__(self, obj, var):
        self.object = template.Variable(obj)
        self.as_var = var

    def render(self, context):
        object = self.object.resolve(context)
        qs = Comment.objects.for_object(object)
        context[self.as_var] = qs.count()
        return ''

@register.tag
def get_comment_count(parser, token):
    """
    Gets the comment count for the specified object and makes it available in the
    template context under the variable name specified.
    Syntax:
        {% get_comment_count for [object] as [varname] %}
    """
    try:
        (tag, for_word, obj, as_word, var) = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly 4 arguments" % token.contents.split()[0]

    if for_word != 'for':
        raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tag)

    if as_word != 'as':
        raise template.TemplateSyntaxError("Third argument in %r tag must be 'as'" % tag)

    return GetCommentCountNode(obj, var)


class GetCommentListNode(template.Node):
    def __init__(self, obj, var):
        self.object = template.Variable(obj)
        self.as_var = var

    def render(self, context):
        object = self.object.resolve(context)
        qs = Comment.objects.for_object(object)
        context[self.as_var] = list(qs)
        return ''


@register.tag
def get_comment_list(parser, token):
    """
    Gets a list of comments for the specified object and makes it available in the
    template context under the variable name specified.
    Syntax:
        {% get_comment_list for [object] as [varname] %}
    """
    try:
        (tag, for_word, obj, as_word, var) = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly 4 arguments" % token.contents.split()[0]

    if for_word != 'for':
        raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tag)

    if as_word != 'as':
        raise template.TemplateSyntaxError("Third argument in %r tag must be 'as'" % tag)

    return GetCommentListNode(obj, var)


class GetCommentFormNode(template.Node):
    def __init__(self, obj, var):
        self.object = template.Variable(obj)
        self.as_var = var

    def render(self, context):
        object = self.object.resolve(context)
        context[self.as_var] = CommentForm(object)
        return ''


@register.tag
def get_comment_form(parser, token):
    """
    Gets the comment form for an object and makes it available in the
    template context under the variable name specified.
    Syntax:
        {% get_comment_form for [object] as [varname] %}
    """
    try:
        (tag, for_word, obj, as_word, var) = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly 4 arguments" % token.contents.split()[0]

    if for_word != 'for':
        raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tag)

    if as_word != 'as':
        raise template.TemplateSyntaxError("Third argument in %r tag must be 'as'" % tag)

    return GetCommentFormNode(obj, var)


class RenderCommentFormNode(template.Node):
    def __init__(self, obj):
        self.object = template.Variable(obj)

    def render(self, context):
        object = self.object.resolve(context)
        context.push()
        form_str = render_to_string('comments/comment_form.html', {
            'form': CommentForm(object),
            },
            context)
        context.pop()
        return form_str


@register.tag
def render_comment_form(parser, token):
    """
    Renders a comment form for the specified object using the template
    comments/comment_form.html.
    Syntax:
        {% render_comment_form for [object] %}
    """
    try:
        (tag, for_word, obj) = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly 2 arguments" % token.contents.split()[0]

    if for_word != 'for':
        raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tag)

    return RenderCommentFormNode(obj)


@register.inclusion_tag('comments/comment_list.html')
def render_comment_list(object):
    """
    Renders the comments for the specified object using the template
    comments/comment_list.html.
    Syntax:
        {% render_comment_list [object] %}
    """
    qs = Comment.objects.for_object(object).select_related('user', 'user__profile')
    return {
        'comments': qs,
    }

