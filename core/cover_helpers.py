import httpx


def search_open_library(query):
    querystring = (
        f"?limit=10&fields=cover_i,cover_edition_key,title,author_name,"  # noqa: E231
        f"number_of_pages_median,first_publish_year,key{query}"  # noqa: E231
    )

    try:
        response = httpx.get(
            f"https://openlibrary.org/search.json{querystring}"  # noqa: E231
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return {
            "error": (
                "Open Library is having issues. Please try again later or add your book manually. "
                f"We got the following error: “{exc}”"
            )
        }

    if response.content and "application/json" in response.headers["Content-Type"]:
        data = response.json()
        found = []
    else:
        print("Empty response received")
        data = None

    try:
        for doc in data["docs"]:
            if "cover_i" in doc:
                cover_image = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"  # noqa: E231
            elif "cover_edition_key" in doc:
                cover_image = f"https://covers.openlibrary.org/b/olid/{doc['cover_edition_key']}-L.jpg"  # noqa: E231
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
                            doc["cover_edition_key"]
                            if "cover_edition_key" in doc
                            else None
                        ),
                        "pages": (
                            doc["number_of_pages_median"]
                            if "number_of_pages_median" in doc
                            else None
                        ),
                        "cover": cover_image,
                    }
                )
    except TypeError:
        return {
            "error": "Open Library is having issues. Please try again later or add your book manually."
        }

    except KeyError:
        return {
            "error": "Open Library is having issues. Please try again later or add your book manually."
        }

    # If `found` is empty, return the first item in the data['docs']
    if not found and data["docs"]:
        doc = data["docs"][0]

        found = {
            "title": doc["title"],
            "authors": doc.get("author_name", []),
            "published": (
                doc["first_publish_year"] if "first_publish_year" in doc else None
            ),
            "olid": (
                doc["cover_edition_key"]
                if "cover_edition_key" in doc
                else doc["key"].replace("/works/", "") if "key" in doc else None
            ),
            "pages": (
                doc["number_of_pages_median"]
                if "number_of_pages_median" in doc
                else None
            ),
        }

    return found
