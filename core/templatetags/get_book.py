from django import template

register = template.Library()


@register.filter
def get_book(books, book_id):
    return books.filter(id=book_id).first()
