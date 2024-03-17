import os
import requests
from olclient.openlibrary import OpenLibrary
from isbnlib import canonical, notisbn, to_isbn13
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File


def get_book_from_isbn(isbn):
    ol = OpenLibrary()

    isbn = canonical(isbn)
    ol.Edition.get_olid_by_isbn(isbn)
    olid = ol.Edition.get_olid_by_isbn(isbn)

    r = requests.get(f"http://openlibrary.org/api/volumes/brief/isbn/{isbn}.json")

    try:
        data = r.json()["records"][f"/books/{olid}"]["data"]
    except TypeError:
        data = []

    return data


def search_open_library(query):
    ol = OpenLibrary()
    found = []

    if notisbn(query):
        b = ol.Work.search(query)

        if b:
            main_book = {
                "title": b.title,
                "publish_date": b.publish_date,
                "authors": b.authors,
                "olid": b.identifiers.get("olid")[0],
            }

            # Get Editions from OLID and get cover from Edition
            editions = ol.Work.get(main_book["olid"]).editions

            for book in editions:
                isbn = ""
                try:
                    isbn = book.isbn_13
                except AttributeError:
                    try:
                        isbn = book.isbn_10
                    except AttributeError:
                        pass
                try:
                    isbn = isbn[0]
                except IndexError:
                    pass

                isbn = to_isbn13(isbn)

                try:
                    physical_format = book.physical_format
                except AttributeError:
                    physical_format = ""

                if (
                    isbn != ""
                    and str(main_book["publish_date"]) in str(book.publish_date)
                    and book.title.casefold() == main_book["title"].casefold()
                    and physical_format != "Audio CD"
                ):
                    cover_image = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

                    r = requests.head(cover_image, allow_redirects=True)

                    try:
                        if r.headers["Content-Type"] == "image/jpeg":
                            title = book.title
                            authors = ", ".join(a.name for a in book.authors)
                            publish_date = book.publish_date

                            try:
                                edition_name = book.edition_name
                            except AttributeError:
                                edition_name = ""

                            found.append(
                                {
                                    "title": title,
                                    "authors": authors,
                                    "published": publish_date,
                                    "edition_name": edition_name,
                                    "isbn": isbn,
                                    "olid": main_book["olid"],
                                    "cover": cover_image,
                                }
                            )
                    except KeyError:
                        pass
                        # TODO: Add an image search and return the first item?
        else:
            print("Not found.")

    else:
        data = get_book_from_isbn(isbn)
        # if data == []:
        #     raise Http404

        authors = ", ".join(a["name"] for a in data["authors"])
        book_title = data["title"]
        book_publish_date = data["publish_date"]

        found.append(
            {
                "title": book_title,
                "authors": authors,
                "published": book_publish_date,
                "isbn": isbn,
                "cover": data["cover"]["large"],
            }
        )
    return found


def save_cover_from_url(self, url):
    if url != "":
        r = requests.get(url)

        if r.status_code == 200:
            img_tmp = NamedTemporaryFile(delete=True)
            img_tmp.write(r.content)
            img_tmp.flush()

            self.cover.save(os.path.basename(url), File(img_tmp), save=True)
        else:
            return False
    else:
        return False
