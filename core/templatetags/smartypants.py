import bleach
from django.template.defaulttags import register
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from smartypants import smartypants as sp


@register.filter()
@stringfilter
def smartypants(value):
    return mark_safe(bleach.clean(sp(value), tags=""))
