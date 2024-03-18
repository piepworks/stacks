import requests


def search_open_library(query):
    querystring = f"?limit=10&fields=cover_i,cover_edition_key,title,author_name,first_publish_year&q={query}"
    response = requests.get(f"https://openlibrary.org/search.json{querystring}")
    data = response.json()

    found = []

    for doc in data["docs"]:
        if "cover_i" in doc:
            cover_image = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
        elif "cover_edition_key" in doc:
            cover_image = f"https://covers.openlibrary.org/b/olid/{doc['cover_edition_key']}-L.jpg"
        else:
            cover_image = None

        if cover_image:
            found.append(
                {
                    "title": doc["title"],
                    "authors": doc.get("author_name", []),
                    "published": (
                        doc["first_publish_year"]
                        if "first_publish_year" in doc
                        else None
                    ),
                    "olid": (
                        doc["cover_edition_key"] if "cover_edition_key" in doc else None
                    ),
                    "cover": cover_image,
                }
            )

    return found
