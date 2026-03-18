from django import template

register = template.Library()


@register.filter
def getfield(obj, field_name):
    """Get a field value from a model instance by name."""
    return getattr(obj, field_name, '')
