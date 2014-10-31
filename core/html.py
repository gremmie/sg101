"""Common HTML related functions"""
import bleach


# Each entry in the _CLEAN_PROFILES dict is a profile name -> 3-tuple pair. The
# tuple consists of (allowed_tags_list, allowed_attributes_dict,
# allowed_styles_list)
#
_CLEAN_PROFILES = {
    'comments': (
        [
            'a', 'b', 'blockquote', 'br', 'code', 'del', 'em',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'i', 'img', 'li', 'ol', 'p', 'pre', 'strong', 'ul',
        ],
        {
            'a': ['href'],
            'img': ['src', 'alt', 'title'],
        },
        [],
    ),
    'news': (
        [
            'a', 'b', 'blockquote', 'br', 'caption', 'center', 'code', 'col',
            'colgroup', 'dd', 'del', 'div', 'dl', 'dt', 'em',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'i', 'img', 'ins', 'li', 'ol', 'p', 'pre', 'small', 'strike',
            'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
            'thead', 'tr', 'tt', 'u', 'ul',
        ],
        {
            'a': ['href'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        },
        [],
    ),
}


def clean_html(text, profile='comments'):
    """Cleans HTML of dangerous tags and content."""
    text = text.strip()
    if not text:
        return text

    tags, attrs, styles = _CLEAN_PROFILES[profile]

    return bleach.clean(text, tags=tags, attributes=attrs, styles=styles,
        strip=True, strip_comments=True)
