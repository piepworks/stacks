def get_filter_counts(queryset, items, field_name):
    if not items:
        return {}

    if hasattr(items[0], "parent"):
        child_counts = {
            item.slug: queryset.filter(**{f"{field_name}__slug": item.slug}).count()
            for item in items
            if item.parent is not None
        }

        parent_counts = {
            parent.slug: {
                "count": queryset.filter(**{f"{field_name}__slug": parent.slug}).count()
                + sum(
                    child_counts[child.slug]
                    for child in items
                    if child.parent == parent
                ),
                "sub_items": {
                    child.slug: child_counts[child.slug]
                    for child in items
                    if child.parent == parent
                },
            }
            for parent in items
            if parent.parent is None
        }

        return parent_counts
    else:
        counts = {
            item.slug: queryset.filter(**{f"{field_name}__slug": item.slug}).count()
            for item in items
        }

        return counts
