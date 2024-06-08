import requests


def search_open_library(query):
    querystring = f"?limit=10&fields=cover_i,cover_edition_key,title,author_name,first_publish_year{query}"

    try:
        response = requests.get(f"https://openlibrary.org/search.json{querystring}")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

    if response.content and "application/json" in response.headers["Content-Type"]:
        data = response.json()
        found = []
    else:
        print("Empty response received")
        data = None

    try:
        for doc in data["docs"]:
            if "cover_i" in doc:
                cover_image = (
                    f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                )
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
                            doc["cover_edition_key"]
                            if "cover_edition_key" in doc
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
            "olid": (doc["cover_edition_key"] if "cover_edition_key" in doc else None),
        }

    return found
