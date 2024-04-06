from django import template

register = template.Library()


@register.filter
def filter_matches_any(item, filter_queries):
    if filter_queries.get(item.name, False):
        return True
    for sub_item in item.__class__.objects.filter(parent=item):
        if filter_matches_any(sub_item, filter_queries):
            return True
    return False
