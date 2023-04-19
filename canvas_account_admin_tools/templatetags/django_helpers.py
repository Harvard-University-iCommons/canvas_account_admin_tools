from django import template
from django.conf import settings
from django.utils import timezone
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.filter(is_safe=True)
def format_datetime(datetime):
    return timezone.localtime(datetime).strftime('%b %d, %Y %H:%M:%S')