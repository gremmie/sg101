"""
Tag cloud support for the news app.

The font-size calculation is ported from django-tagging, which this app no
longer depends on. It is kept rather than replaced because it decides how
/news/tags/ has looked for years, and a different curve would restyle a page
nobody asked to have restyled.

"""
import math

from django.db.models import Count, F, Func


# Which curve maps a tag's count onto its font size. Logarithmic keeps a tag
# used 691 times from dwarfing everything else, which on this site it otherwise
# would.
LOGARITHMIC, LINEAR = 1, 2


class CloudTag:
    """A tag and its usage, sized for display.

    The template asks for `name` and `font_size`; `count` is what the sizing
    reads. This is deliberately not a model -- there is no tag table any more.

    """
    __slots__ = ('name', 'count', 'font_size')

    def __init__(self, name, count, font_size=1):
        self.name = name
        self.count = count
        self.font_size = font_size

    def __repr__(self):
        return 'CloudTag(%r, %r, %r)' % (self.name, self.count, self.font_size)

    def __eq__(self, other):
        if not isinstance(other, CloudTag):
            return NotImplemented
        return ((self.name, self.count, self.font_size)
                == (other.name, other.count, other.font_size))


def tag_cloud(model, steps=4, distribution=LOGARITHMIC):
    """Every tag used by the given model, with a count and a font size.

    One query: unnest the tag arrays and group. Ordering by name is what the
    page has always done, and it is the ordering the collation audit settled.

    """
    rows = (model.objects.annotate(tag=Func(F('tags'), function='unnest'))
            .values('tag')
            .annotate(count=Count('*'))
            .order_by('tag'))
    return calculate_cloud([CloudTag(row['tag'], row['count']) for row in rows],
                           steps, distribution)


def calculate_cloud(tags, steps=4, distribution=LOGARITHMIC):
    """Set `font_size` on each tag, an integer from 1 to `steps`."""
    if not tags:
        return tags

    counts = [tag.count for tag in tags]
    min_weight = float(min(counts))
    max_weight = float(max(counts))
    thresholds = _calculate_thresholds(min_weight, max_weight, steps)

    for tag in tags:
        tag_weight = _calculate_tag_weight(tag.count, max_weight, distribution)
        for i in range(steps):
            if tag_weight <= thresholds[i]:
                tag.font_size = i + 1
                break

    return tags


def _calculate_thresholds(min_weight, max_weight, steps):
    delta = (max_weight - min_weight) / float(steps)
    return [min_weight + i * delta for i in range(1, steps + 1)]


def _calculate_tag_weight(weight, max_weight, distribution):
    """Logarithmic weighting after the Mephisto tag cloud plugin, by Sven Fuchs,
    which is where django-tagging took it from."""
    if distribution == LINEAR or max_weight == 1:
        return weight
    if distribution == LOGARITHMIC:
        return min(math.log(weight) * max_weight / math.log(max_weight),
                   max_weight)
    raise ValueError('Invalid distribution algorithm specified: %s.'
                     % distribution)
