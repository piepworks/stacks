from django import template

register = template.Library()


@register.simple_tag
def filter_matches_any(item, filter_name, filter_queries):
    if filter_queries.get(filter_name, False) == item.slug:
        return True
    for sub_item in item.__class__.objects.filter(parent=item):
        if filter_matches_any(sub_item, filter_name, filter_queries):
            return True
    return False
