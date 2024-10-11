from django import template
from core.models import Book

register = template.Library()


@register.filter
def status_display(status):
    return dict(Book._meta.get_field("status").choices)[status]
