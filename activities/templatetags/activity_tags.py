from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def get_limit(d, key):
    """Get a value from a dict by key."""
    if isinstance(d, dict):
        return d.get(key, 0)
    return 0


@register.filter
def add_ref(field, ref_name):
    """Add an x-ref attribute to a form field for Alpine.js."""
    rendered = str(field)
    # Add x-ref attribute and x-on:input for live updates
    rendered = rendered.replace('>', f' x-ref="{ref_name}" x-on:input="$forceUpdate()">', 1)
    return mark_safe(rendered)
