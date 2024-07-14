import pytest
import io
from PIL import Image
from unittest import mock
from model_bakery import baker
from requests.exceptions import RequestException
from core.models import Book, BookFormat, BookLocation, BookReading, BookCover


@pytest.fixture
def create_user(django_user_model):
    def inner_function(email, password):
        return django_user_model.objects.create_user(email, password)

    return inner_function


@pytest.fixture
def create_superuser(django_user_model):
    def inner_function(email, password, **extra_fields):
        return django_user_model.objects.create_superuser(
            email, password, **extra_fields
        )

    return inner_function


def test_user_without_email(create_user):
    with pytest.raises(ValueError):
        create_user("", "")


@pytest.mark.django_db
def test_user_creation(create_user):
    user = create_user("user@example.com", "")
    assert str(user) == "user@example.com"


def test_superuser_creation(create_superuser):
    superuser = create_superuser("superuser@example.com", "")
    assert str(superuser) == "superuser@example.com"


def test_superuser_not_staff(create_superuser):
    with pytest.raises(ValueError):
        create_superuser("superuser@example.com", "", is_staff=False)


def test_superuser_not_superuser(create_superuser):
    with pytest.raises(ValueError):
        create_superuser("superuser@example.com", "", is_superuser=False)


@pytest.mark.django_db
def test_book_creation_without_genre():
    book = baker.make(Book)
    assert book.genres.count() == 0


@pytest.mark.django_db
def test_book_creation_with_multiple_formats():
    format1 = baker.make(BookFormat)
    format2 = baker.make(BookFormat)
    book = baker.make(Book)
    book.format.set([format1, format2])
    assert book.format.count() == 2


@pytest.mark.django_db
def test_book_creation_with_multiple_locations():
    location1 = baker.make(BookLocation)
    location2 = baker.make(BookLocation)
    book = baker.make(Book)
    book.location.set([location1, location2])
    assert book.location.count() == 2


@pytest.mark.django_db
def test_book_is_not_archived_by_default():
    book = baker.make(Book)
    assert book.archived is False


@pytest.mark.django_db
def test_book_status_update():
    book = baker.make(Book, status="available")
    book.status = "unavailable"
    book.save()
    assert book.status == "unavailable"


@pytest.mark.django_db
def test_book_status_update_to_reading_creates_bookreading():
    book = baker.make(Book, title="Test Book", status="backlog")
    book.status = "reading"
    book.save()
    assert BookReading.objects.filter(book=book).exists()


@pytest.mark.django_db
def test_book_status_update_to_finished_updates_bookreading():
    book = baker.make(Book, title="Test Book", status="reading")
    book.status = "finished"
    book.save()
    reading = BookReading.objects.get(book=book)
    assert reading.end_date is not None
    assert reading.finished is True


@pytest.mark.django_db
def test_book_status_update_to_dnf_updates_bookreading():
    book = baker.make(Book, title="Test Book", status="reading")
    book.status = "dnf"
    book.save()
    reading = BookReading.objects.get(book=book)
    assert reading.end_date is not None
    assert reading.finished is False


@pytest.mark.django_db
def test_save_cover_from_url_with_empty_url():
    book_cover = baker.make(BookCover)
    assert book_cover.save_cover_from_url("") is False


@pytest.mark.django_db
@mock.patch("requests.get", side_effect=RequestException)
def test_save_cover_from_url_with_request_exception(mock_get):
    book_cover = baker.make(BookCover)
    assert book_cover.save_cover_from_url("http://example.com/image.jpg") is False


@pytest.mark.django_db
@mock.patch("requests.get", return_value=mock.Mock(status_code=404))
def test_save_cover_from_url_with_non_200_status_code(mock_get):
    book_cover = baker.make(BookCover)
    assert book_cover.save_cover_from_url("http://example.com/image.jpg") is False


@pytest.mark.django_db
@mock.patch("requests.get")
def test_save_cover_from_url_with_200_status_code(mock_get):
    # Create a mock image
    img = Image.new("RGB", (60, 30), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    # Mock the response of requests.get
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = img_byte_arr

    book_cover = baker.make(BookCover)
    assert book_cover.save_cover_from_url("http://example.com/image.jpg") is True
    assert book_cover.image is not None
