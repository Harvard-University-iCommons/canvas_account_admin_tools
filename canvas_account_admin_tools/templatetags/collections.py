from django import template


register = template.Library()


@register.filter()
def get_value(dictionary, key):
    """
    Custom template filter for returning a value from a dict given the key
    """
    return dictionary.get(key)
