import requests


def goodreads_status(shelf):
    # Using a dictionary as a case/switch statement.
    try:
        return {
            "to-read": "wishlist",
            "currently-reading": "reading",
            "read": "finished",
            "abandoned": "dnf",
        }[shelf]
    except KeyError:
        return "wishlist"


def the_storygraph_status(status):
    try:
        return {
            "to-read": "wishlist",
            "currently-reading": "reading",
            "read": "finished",
            "did-not-finish": "dnf",
        }[status]
    except KeyError:
        return "wishlist"


def published_year_from_isbn(isbn):
    url = f"https://openlibrary.org/isbn/{isbn}.json"  # noqa: E231
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        date_str = data.get("publish_date")

        # Attempt to extract the year directly if it's an integer
        year_str = date_str.split()[-1]
        if year_str.isdigit():
            return int(year_str)
        else:
            # Implement additional logic for date parsing if necessary
            try:
                # Example of parsing the full date string to extract the year
                from datetime import datetime

                year = datetime.strptime(date_str, "%b %d, %Y").year
                return year
            except ValueError:
                pass
    return None
