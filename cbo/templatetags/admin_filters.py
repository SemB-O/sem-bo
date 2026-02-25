from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return True  # Default to checked if no data
    return dictionary.get(key, True)
