import json

from django.utils.safestring import mark_safe
from django.template import Library


register = Library()


@register.filter(is_safe=True)
def jsonify(object):
    return mark_safe(json.dumps(object))