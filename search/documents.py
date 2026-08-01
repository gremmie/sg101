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

Each document's get_queryset() also carries whatever rule decides that its
model's rows are visible on the site at all, since search must not surface what
a member cannot otherwise reach. All eight were checked; four have such a rule:

    forums.Topic, forums.Post  the category's groups (a gated category)
    weblinks.Link              is_public, an admin's approval
    downloads.Download         is_public, likewise
    bio.UserProfile            the user's is_active

The other three have none, and the reasons will not change quietly: a news.Story
is approved by existing, since unapproved submissions are a separate PendingStory
model and nothing on the Story itself gates it; podcast.Item has no flag of any
kind and is admin-entered; ygroup.Post is a frozen 2010 archive that nothing
writes to. All three are read unfiltered by their own views. Note that downloads
and weblinks have a Pending model too, but unlike news they *also* keep is_public
on the approved row, which is the flag that matters here.

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
_keys = {}


def register(cls):
    """Registers a Document subclass as the entry for its model."""
    document = cls()
    _registry[cls.model] = document
    _keys[document.key] = document
    return cls


def document_for_model(model):
    """Returns the Document for a searchable model."""
    return _registry[model]


def all_documents():
    """Returns every registered Document."""
    return list(_registry.values())


def document_choices():
    """
    The searchable types as (key, label) pairs, in registry order.

    This is what the search form's checkboxes are built from. Registry order is
    the order the old form listed them in, which the checkboxes keep.

    """
    return [(document.key, document.label) for document in all_documents()]


def document_for_key(key):
    """Returns the Document a search form's type key names."""
    return _keys[key]


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

    # What this type is called on the search page: label names the checkbox
    # that includes it, result_label prefixes each of its result rows. Both are
    # spelled out rather than taken from the model's verbose_name, because
    # forums.Post and ygroup.Post are both "post" and a blended result list has
    # to tell them apart.
    label = None
    result_label = None

    # Lookups the bulk indexer re-applies to each batch by hand. iterator()
    # drops prefetch_related, so a queryset that declares one would issue a
    # query per row over the whole table; declaring it here instead lets the
    # single-object path and the batched path each prefetch correctly.
    prefetch = ()

    # The lookup path from this model to the forums.Category whose privacy
    # governs it, for the types where one does. It both filters private
    # content out of get_queryset() below and tells the task that reacts to a
    # category's groups changing which objects to rebuild.
    category_path = None

    @property
    def key(self):
        """
        How a search URL names this type, as `app_label.model`.

        The old search form used these same values, so a ?models= URL saved or
        linked back when it was running still selects what it used to.

        """
        return '%s.%s' % (self.model._meta.app_label,
                          self.model._meta.model_name)

    def get_queryset(self):
        """
        The objects of this type to index.

        This is the one definition of what belongs in the index. Everything
        reads it: the bulk rebuild, the sweep that removes rows the queryset
        no longer yields, and the per-object task, which indexes an object if
        this queryset still contains it and deletes its row otherwise. An
        object that becomes unindexable therefore needs no special handling
        anywhere -- it simply stops being yielded.

        """
        queryset = self.model._default_manager.all().prefetch_related(
                *self.prefetch)

        if self.category_path:
            # A category with groups assigned is visible only to their members,
            # so its content stays out of the index entirely -- there is no
            # per-user filter at query time to keep it from being found.
            # Privacy is a property of the category, not of the content, and it
            # can be revoked in either direction at any time from the admin.
            queryset = queryset.filter(
                    **{self.category_path + '__groups__isnull': True})

        return queryset

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
    label = 'Forum Topics'
    result_label = 'Forum Topic'
    category_path = 'forum__category'

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
    label = 'Forum Posts'
    result_label = 'Forum Post'
    category_path = 'topic__forum__category'

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
    label = 'News Stories'
    result_label = 'News Story'

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
    label = 'User Profiles'
    result_label = 'User Profile'
    prefetch = ('user__website_profiles',)

    def get_queryset(self):
        # Deactivated accounts are spammers and resignations, and bio hides
        # them from the member list it offers for finding people
        # (bio/views.py:40). The old Xapian index filtered on the same flag.
        # Note that a deactivation reaches this through the profile: marking a
        # spammer saves the profile as well as the user.
        return super().get_queryset().select_related('user').filter(
                user__is_active=True)

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
    label = 'Links'
    result_label = 'Link'

    def get_queryset(self):
        # A link is submitted by a member and stays invisible until an admin
        # approves it; is_public is that approval. Every browse view reads
        # Link.public_objects, which is this same filter.
        return super().get_queryset().select_related('user').filter(
                is_public=True)

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
    label = 'Downloads'
    result_label = 'Download'

    def get_queryset(self):
        # Approval, as on a link -- and here an unapproved row is worse than
        # a stale result: downloads-details is get_object_or_404 against
        # Download.public_objects, so indexing one produces a search hit that
        # 404s on click.
        return super().get_queryset().select_related('user').filter(
                is_public=True)

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
    label = 'Podcasts'
    result_label = 'Podcast'

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
    label = 'Yahoo Group Archives'
    result_label = 'Yahoo Group Archive'

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
