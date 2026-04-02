"""Template filters for markdown rendering."""

import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def render_markdown(text):
    """Convert markdown text to HTML."""
    return mark_safe(markdown.markdown(
        text, extensions=['extra', 'nl2br']
    ))