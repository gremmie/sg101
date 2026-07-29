"""
The document registry: how each searchable model becomes one search document.

Each entry supplies the text for the three weight bands -- title (A), summary
(B) and author (C) -- along with the url and date a result page displays. The
vector itself is built from those columns by SearchDocument.

The field lists come from the index templates the old Xapian/Haystack stack left
behind in sg101/templates/search/indexes/, with one deliberate change: author
full names are indexed only on the profile document. A username is immutable,
written once at account activation, but first_name/last_name are editable
through bio.EditUserForm -- and embedding those in content documents would make
a single profile edit rebuild every row that member ever wrote.

"""
import html

from django.utils.html import strip_tags

from bio.models import UserProfile
from downloads.models import Download
from forums.models import Post
from forums.models import Topic
from news.models import Story
from podcast.models import Item
from weblinks.models import Link
from ygroup.models import Post as YgroupPost


_registry = {}


def register(cls):
    """Registers a Document subclass as the entry for its model."""
    _registry[cls.model] = cls()
    return cls


def document_for_model(model):
    """Returns the Document for a searchable model."""
    return _registry[model]


def all_documents():
    """Returns every registered Document."""
    return list(_registry.values())


def body_text(*parts):
    """
    Joins body text, dropping HTML and empty parts.

    Several sources hold rendered HTML rather than the markup it came from --
    every news story, and 40% of the Yahoo Group archive -- and this text is
    both what gets indexed and what result snippets are drawn from, so tags
    would otherwise turn up in both places.

    """
    joined = '\n'.join(part for part in parts if part)
    return html.unescape(strip_tags(joined))


class Document:
    """How one searchable model becomes a search document."""

    model = None

    def get_queryset(self):
        """The objects of this type to index."""
        return self.model._default_manager.all()

    def title(self, obj):
        """Weight A text, and the result page's heading."""
        raise NotImplementedError

    def summary(self, obj):
        """Weight B text, and what result snippets are drawn from."""
        return ''

    def author(self, obj):
        """Weight C text."""
        return ''

    def url(self, obj):
        return obj.get_absolute_url()

    def date(self, obj):
        """The document's own date -- the recency tiebreak."""
        raise NotImplementedError

    def build(self, obj):
        """Returns the column values for obj's row."""
        return {
            'title': self.title(obj),
            'summary': self.summary(obj),
            'author': self.author(obj),
            'url': self.url(obj),
            'date': self.date(obj),
        }


@register
class TopicDocument(Document):
    model = Topic

    def get_queryset(self):
        return super().get_queryset().select_related('user')

    def title(self, obj):
        return obj.name

    # A topic has no body of its own -- its text is its posts, indexed as their
    # own documents -- so summary stays empty, as it was under Xapian.

    def author(self, obj):
        return obj.user.username

    def date(self, obj):
        return obj.creation_date


@register
class PostDocument(Document):
    model = Post

    def get_queryset(self):
        return super().get_queryset().select_related('topic', 'user')

    def title(self, obj):
        return obj.topic.name

    def summary(self, obj):
        return body_text(obj.body)

    def author(self, obj):
        return obj.user.username

    def date(self, obj):
        return obj.creation_date


@register
class StoryDocument(Document):
    model = Story

    def get_queryset(self):
        return super().get_queryset().select_related('submitter')

    def title(self, obj):
        return obj.title

    def summary(self, obj):
        # short_text/long_text hold rendered HTML for every story in the
        # archive; the markup they came from exists only for stories saved
        # since news version 2. tags were indexed by the old stack, though
        # search_summary() leaves them out.
        return body_text(obj.short_text, obj.long_text, obj.tags)

    def author(self, obj):
        return obj.submitter.username

    def date(self, obj):
        return obj.date_submitted


@register
class UserProfileDocument(Document):
    model = UserProfile

    def get_queryset(self):
        return super().get_queryset().select_related('user').prefetch_related(
                'user__website_profiles')

    def title(self, obj):
        # On a profile the author is the document, so username and full name
        # both sit at weight A. search_title() returns exactly that pair.
        return obj.search_title()

    def summary(self, obj):
        sites = []
        for site in obj.user.website_profiles.all():
            sites.extend((site.name, site.url))
        return body_text(obj.location, obj.occupation, obj.interests,
                         obj.profile_text, obj.signature, *sites)

    def author(self, obj):
        return obj.user.username

    def date(self, obj):
        # A profile has no date of its own. date_joined is stable and means
        # "member since"; update_date would let the most recently edited
        # profile win every relevance tie.
        return obj.user.date_joined


@register
class LinkDocument(Document):
    model = Link

    def get_queryset(self):
        return super().get_queryset().select_related('user')

    def title(self, obj):
        return obj.title

    def summary(self, obj):
        # The url was indexed by the old stack but is absent from
        # search_summary(). Description leads so snippets open on prose.
        return body_text(obj.description, obj.url)

    def author(self, obj):
        return obj.user.username

    def date(self, obj):
        return obj.date_added


@register
class DownloadDocument(Document):
    model = Download

    def get_queryset(self):
        return super().get_queryset().select_related('user')

    def title(self, obj):
        return obj.title

    def summary(self, obj):
        return body_text(obj.description)

    def author(self, obj):
        return obj.user.username

    def date(self, obj):
        return obj.date_added


@register
class ItemDocument(Document):
    model = Item

    def title(self, obj):
        return obj.title

    def summary(self, obj):
        return body_text(obj.subtitle, obj.summary, obj.keywords)

    def author(self, obj):
        return obj.author       # a text field, not a foreign key

    def date(self, obj):
        return obj.pubdate


@register
class YgroupPostDocument(Document):
    model = YgroupPost

    def title(self, obj):
        return obj.title

    def summary(self, obj):
        return body_text(obj.msg)

    def author(self, obj):
        # The old index ignored this field. Indexing it makes archive posts
        # findable by who wrote them, on an archive that can never drift.
        return obj.poster

    def date(self, obj):
        return obj.creation_date
