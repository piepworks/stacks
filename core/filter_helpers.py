def calculate_unique_child_counts(parent, items, queryset, field_name, child_counts):
    if field_name == "genre":
        unique_books = set()

        for child in items:
            if child.parent == parent:
                related_books = queryset.filter(genre__slug=child.slug)
                unique_books.update({book.id for book in related_books})

        return len(unique_books)
    else:
        return sum(
            child_counts[child.slug] for child in items if child.parent == parent
        )


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
                + calculate_unique_child_counts(
                    parent, items, queryset, field_name, child_counts
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
