from django import template

register = template.Library()


@register.simple_tag
def filter_matches_any(item, filter_name, filter_queries):
    if filter_queries.get(filter_name, False) == item.slug:
        return True

    # Append 'book' to each key in filter_queries and ignore values that are 'all'
    filter_queries = {f"book{k}": v for k, v in filter_queries.items() if v != "all"}

    # Check if any sub_items match the filter
    return item.__class__.objects.filter(
        parent=item, slug=filter_queries.get(f"book{filter_name}", False)
    ).exists()
