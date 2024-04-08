from django import template

register = template.Library()


@register.filter
def times(number):
    return range(number)


@register.filter
def remaining_stars(rating):
    return 5 - int(rating)
