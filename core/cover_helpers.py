import requests
from olclient.openlibrary import OpenLibrary


def search_open_library(query):
    ol = OpenLibrary()
    found = []

    b = ol.Work.search(query)

    if b:
        olid = b.identifiers.get("olid")[0]
        cover_image = f"https://covers.openlibrary.org/w/olid/{olid}-L.jpg"

        r = requests.head(cover_image, allow_redirects=True)

        try:
            if r.headers["Content-Type"] == "image/jpeg":
                title = b.title
                authors = b.authors
                publish_date = b.publish_date

                found.append(
                    {
                        "title": title,
                        "authors": authors,
                        "published": publish_date,
                        "olid": olid,
                        "cover": cover_image,
                    }
                )
        except KeyError:
            pass
            # TODO: Add an image search and return the first item?

    return found
