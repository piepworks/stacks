import pytest
from http import HTTPStatus
from django.urls import reverse
from model_bakery import baker
from core.models import Book, BookType, BookGenre, BookLocation


def test_favicon(client):
    response = client.get("/favicon.ico")
    assert response.status_code == HTTPStatus.OK
    assert response["Cache-Control"] == "max-age=86400, immutable, public"


def test_homepage(client, settings):
    settings.STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        }
    }
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK


@pytest.fixture
def setup_staticfiles_storage(settings):
    settings.STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        }
    }


@pytest.fixture
def create_user(django_user_model):
    def inner_function(email, password):
        return django_user_model.objects.create_user(email, password)

    return inner_function


@pytest.fixture
def client_logged_in(client, create_user):
    email = "testuser@example.com"
    password = "testpassword"
    user = create_user(email, password)
    client.login(username=email, password=password)
    return client, user


@pytest.mark.django_db
def test_status_view_valid_status(client_logged_in, setup_staticfiles_storage):
    client, user = client_logged_in

    status_url = reverse("status", args=["reading"])
    response = client.get(status_url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_status_view_invalid_status(client_logged_in, setup_staticfiles_storage):
    client, user = client_logged_in

    invalid_status_url = reverse("status", args=["invalid_status"])
    response = client.get(invalid_status_url)
    assert response.status_code == 404


@pytest.fixture
def book_data():
    type1 = baker.make(BookType, slug="type1")
    type2 = baker.make(BookType, slug="type2", parent=type1)
    genre1 = baker.make(BookGenre, slug="genre1")
    genre2 = baker.make(BookGenre, slug="genre2")
    genre3 = baker.make(BookGenre, slug="genre3", parent=genre1)
    location1 = baker.make(BookLocation, slug="location1")
    location2 = baker.make(BookLocation, slug="location2")
    book1 = baker.make(
        Book,
        title="Book 1",
        type=type1,
        genre=genre1,
        status="reading",
    )
    book1.location.add(location1)
    book2 = baker.make(
        Book,
        title="Book 2",
        type=type2,
        genre=genre2,
        status="reading",
    )
    book2.location.add(location2)
    book3 = baker.make(
        Book,
        title="Book 3",
        type=type2,
        genre=genre3,
        status="reading",
    )
    return (
        type1,
        type2,
        genre1,
        genre2,
        genre3,
        location1,
        location2,
        book1,
        book2,
        book3,
    )


@pytest.mark.django_db
def test_book_filtering_by_type_genre(
    client_logged_in, book_data, setup_staticfiles_storage
):
    (
        type1,
        type2,
        genre1,
        genre2,
        genre3,
        location1,
        location2,
        book1,
        book2,
        book3,
    ) = book_data
    client, user = client_logged_in
    response = client.get(
        reverse("status", args=("reading",)),
        {"type": type1.slug, "genre": genre1.slug},
    )
    assert response.status_code == 200
    assert book1 in [book for book, form in response.context["forms"]]
    assert book2 not in [book for book, form in response.context["forms"]]


@pytest.mark.django_db
def test_book_filtering_by_location(
    client_logged_in, book_data, setup_staticfiles_storage
):
    (
        type1,
        type2,
        genre1,
        genre2,
        genre3,
        location1,
        location2,
        book1,
        book2,
        book3,
    ) = book_data
    client, user = client_logged_in
    response = client.get(
        reverse("status", args=("reading",)),
        {"location": location1.slug},
    )
    assert response.status_code == 200
    assert book1 in [book for book, form in response.context["forms"]]
    assert book2 not in [book for book, form in response.context["forms"]]


@pytest.mark.django_db
def test_filtering_by_subgenre_and_subtype(
    client_logged_in, book_data, setup_staticfiles_storage
):
    (
        type1,
        type2,
        genre1,
        genre2,
        genre3,
        location1,
        location2,
        book1,
        book2,
        book3,
    ) = book_data
    client, user = client_logged_in
    response = client.get(
        reverse("status", args=("reading",)),
        {"type": type2.slug, "genre": genre3.slug},
    )
    assert response.status_code == 200
    assert book1 not in [book for book, form in response.context["forms"]]
    assert book3 in [book for book, form in response.context["forms"]]
