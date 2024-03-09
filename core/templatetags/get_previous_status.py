from django import template
from core.models import Book

register = template.Library()


@register.filter
def get_previous_status(current_status):
    choices = Book._meta.get_field("status").choices
    current_index = next(
        (index for index, choice in enumerate(choices) if choice[0] == current_status),
        None,
    )
    if current_index is not None and current_index > 0:
        previous_status = choices[current_index - 1][0]
        return previous_status
    return None
