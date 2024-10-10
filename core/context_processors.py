from .forms import OpenLibrarySearchForm
from .models import Book


def ol_search_form(request):
    if request.user.is_authenticated and request.path != "/book/new":
        return {
            "status_choices": Book._meta.get_field("status").choices,
            "open_library_search_form": OpenLibrarySearchForm,
        }
    else:
        return {}
